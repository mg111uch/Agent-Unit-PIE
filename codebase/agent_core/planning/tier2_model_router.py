"""Phase 6 — tier-2 model router (three-tier classifier, tier 2).

Tier 1 is the deterministic factory (`tool_groups.try_factory`). When it
declines (ambiguous request) tier 2 asks a small model — a cloud routing model
("gemini" / "openrouter" backend) or a local FunctionGemma-style model on Ollama
("ollama" backend) — to map the plain-language request to ONE canonical action,
using a fixed action-ID vocabulary so the output is tiny and the tier-3 cloud
reasoning model never sees tool schemas.

Validator/policy before execution: unknown tool IDs are rejected,
`execute_command` is allowlist-checked, payloads are capped. Any failure
returns None → tier 3 (cloud Gemini) recovery.

Backend is pluggable and config-driven (`tier2_model_router.backend`):
"gemini" / "openrouter" use a small cloud routing model, "ollama" keeps the
local model path, and a deterministic stub covers the offline benchmark.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from agent_core.config import ALLOWED_COMMANDS

# Fixed action-ID vocabulary (tiny router output). id -> (tool name, arg keys,
# human-readable summary for the function schema).
ACTION_IDS: dict[int, tuple[str, tuple[str, ...], str]] = {
    1: ("Read", ("path",), "Read the contents of a file at path"),
    2: ("Read", ("path",), "List the files and directories inside a directory at path"),
    3: ("Write", ("path", "content"), "Create or overwrite a file with the given content"),
    4: ("edit_file", ("path", "old_string", "new_string"), "Edit a file by replacing old_string with new_string"),
    5: ("execute_command", ("command",), "Run a shell command in the workspace"),
    6: ("glob_search", ("pattern",), "Find files by glob pattern"),
    7: ("grep_search", ("pattern", "include"), "Search file contents for a regex pattern"),
    8: ("check_path_exists", ("path",), "Check whether a path exists"),
    9: ("get_workspace_info", (), "Show information about the workspace"),
}

_ID_TOOL = {i: spec[0] for i, spec in ACTION_IDS.items()}

# Unique function names so Ollama's FunctionGemma renderer can disambiguate the
# two Read actions (read file vs list directory) in a single tool schema set.
_FN_NAME = {i: f"act_{i}" for i in ACTION_IDS}
_FN_TO_ID = {fn: i for i, fn in _FN_NAME.items()}

_ARG_TYPES: dict[str, str] = {
    "path": "string", "content": "string", "command": "string",
    "pattern": "string", "include": "string",
    "old_string": "string", "new_string": "string",
}


def _action_schema(i: int) -> dict:
    tool, keys, desc = ACTION_IDS[i]
    props = {k: {"type": _ARG_TYPES.get(k, "string"), "description": k} for k in keys}
    return {
        "type": "function",
        "function": {
            "name": _FN_NAME[i],
            "description": desc,
            "parameters": {"type": "object", "properties": props, "required": list(keys)},
        },
    }


# Tool schemas sent to the router model: one function per fixed action. The
# model answers with a native tool call; a text-JSON reply is the fallback.
TOOL_SCHEMAS: list[dict] = [_action_schema(i) for i in ACTION_IDS]

_ROUTER_PROMPT = (
    "You map a user request to exactly one operation from this fixed catalog.\n"
    "  1 = read file          args: path\n"
    "  2 = list directory     args: path\n"
    "  3 = write file         args: path, content\n"
    "  4 = edit file          args: path, old_string, new_string\n"
    "  5 = execute command    args: command\n"
    "  6 = glob search        args: pattern\n"
    "  7 = grep search        args: pattern, include\n"
    "  8 = check path exists  args: path\n"
    "  9 = workspace info     (no args)\n\n"
    "Reply with ONLY valid JSON, no prose: {\"tool\": N, \"args\": {...}}\n"
    "If no operation fits, reply: {\"tool\": 0}"
)

_EXEC_ALLOWED = set(ALLOWED_COMMANDS)
_MAX_CONTENT = 4000


def _parse_action(text: str) -> Optional[dict]:
    """Strictly parse the router's single-JSON-object reply into an action."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start:end + 1])
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    tool_id = data.get("tool")
    if not isinstance(tool_id, int) or tool_id not in _ID_TOOL:
        return None
    return {"id": tool_id, "args": data.get("args") if isinstance(data.get("args"), dict) else {}}


class Tier2ModelRouter:
    """Maps an ambiguous request to a validated tool action via a router model."""

    def __init__(
        self,
        provider: Any,
        *,
        enabled: bool = True,
        max_tokens: int = 40,
    ):
        self.provider = provider
        self.enabled = bool(enabled)
        self.max_tokens = int(max_tokens)

    def _policy(self, name: str, args: dict) -> bool:
        if name == "execute_command":
            cmd = (args.get("command") or "").strip()
            if not cmd.split() or cmd.split()[0] not in _EXEC_ALLOWED:
                return False
        if name == "Write" and len(args.get("content", "")) > _MAX_CONTENT:
            return False
        required = {
            "Read": ("path",),
            "Write": ("path",),
            "edit_file": ("path",),
            "glob_search": ("pattern",),
            "grep_search": ("pattern",),
            "check_path_exists": ("path",),
            "execute_command": ("command",),
        }.get(name, ())
        for key in required:
            if not str(args.get(key, "")).strip():
                return False
        return True

    def route(self, user_input: str) -> Optional[dict]:
        """Return {"name": tool, "input": args} or None (can't route safely)."""
        if not self.enabled or not (user_input or "").strip():
            return None
        try:
            raw = self.provider.generate(
                prompt=user_input,
                system_prompt=_ROUTER_PROMPT,
                temperature=0.0,
                max_tokens=self.max_tokens,
                tools=TOOL_SCHEMAS,
            )
        except Exception:
            return None
        if not raw or raw.get("error"):
            return None
        parsed = None
        for tc in raw.get("tool_calls") or []:
            action_id = _FN_TO_ID.get(tc.get("name", ""))
            if action_id is None:
                continue
            args = {k: v for k, v in (tc.get("arguments") or {}).items()
                    if isinstance(v, (str, bool, int, float))}
            parsed = {"id": action_id, "args": args}
            break
        if parsed is None:
            parsed = _parse_action(raw.get("response") or "")
        if not parsed:
            return None
        name = _ID_TOOL[parsed["id"]]
        args = {k: v for k, v in parsed["args"].items() if isinstance(v, (str, bool, int, float))}
        if not self._policy(name, args):
            return None
        return {"name": name, "input": args}


def build_tier2_model_router() -> Optional[Tier2ModelRouter]:
    """Wire the router from config (TIER2_MODEL_ROUTER_ENABLED); None when disabled.

    Backend is config-driven (`tier2_model_router.backend`): "gemini" /
    "openrouter" use a small cloud routing model, "ollama" keeps the local
    model path. Any construction failure returns None so tier-3 (cloud Gemini)
    recovers.
    """
    import os
    import agent_core.config as cfg
    if not cfg.TIER2_MODEL_ROUTER_ENABLED:
        return None
    backend = (cfg.TIER2_MODEL_ROUTER_BACKEND or "ollama").lower()
    model = cfg.TIER2_MODEL_ROUTER_MODEL
    timeout_s = cfg.TIER2_MODEL_ROUTER_TIMEOUT
    try:
        if backend == "gemini":
            from agent_core.providers.gemini_provider import GeminiProvider
            provider = GeminiProvider(
                api_key=os.getenv("GEMINI_API_KEY", ""),
                model=model,
                timeout_ms=int(timeout_s * 1000),
            )
        elif backend == "openrouter":
            from agent_core.providers.openrouter_provider import OpenRouterProvider
            provider = OpenRouterProvider(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
                model=model,
                timeout=timeout_s,
            )
        else:
            from agent_core.providers.ollama_provider import OllamaProvider
            provider = OllamaProvider(model=model, timeout=timeout_s)
        return Tier2ModelRouter(provider, enabled=True)
    except Exception:
        return None


def deterministic_router(labels: dict[str, str]) -> Tier2ModelRouter:
    """Benchmark/testing stub: canned JSON per prompt substring, provider-like."""
    class _Stub:
        def __init__(self, mapping):
            self._mapping = mapping

        def generate(self, **kwargs):
            prompt = (kwargs.get("prompt") or "").lower()
            for key, resp in self._mapping.items():
                if key in prompt:
                    return {"response": resp}
            return {"response": '{"tool": 0}'}
    return Tier2ModelRouter(_Stub(labels), enabled=True)


if __name__ == "__main__":
    # Smoke test — run with: python -m agent_core.planning.tier2_model_router
    class _ToolStub:
        """Provider-like stub that answers with a native tool_call."""

        def __init__(self, mapping):
            self._mapping = mapping

        def generate(self, **kwargs):
            prompt = (kwargs.get("prompt") or "").lower()
            for key, fn_name, args in self._mapping:
                if key in prompt:
                    return {"response": "", "tool_calls": [{"name": fn_name, "arguments": args}]}
            return {"response": '{"tool": 0}'}

    r = deterministic_router({
        "sum the file": '{"tool": 1, "args": {"path": "x.py"}}',
        "run pytest": '{"tool": 5, "args": {"command": "pytest"}}',
        "rm things": '{"tool": 5, "args": {"command": "rm -rf /"}}',
    })
    assert r.route("sum the file") == {"name": "Read", "input": {"path": "x.py"}}
    assert r.route("run pytest") == {"name": "execute_command", "input": {"command": "pytest"}}
    assert r.route("rm things") is None      # policy blocks non-allowlisted exec
    assert r.route("blah blah") is None      # unknown action id -> None
    assert Tier2ModelRouter(None).route(" x ") is None  # disabled/empty handling

    # Native tool_call path: act_5 -> execute_command.
    t = Tier2ModelRouter(_ToolStub([
        ("run tests", "act_5", {"command": "pytest"}),
        ("delete everything", "act_5", {"command": "rm -rf /"}),
    ]), enabled=True)
    assert t.route("run tests") == {"name": "execute_command", "input": {"command": "pytest"}}
    assert t.route("delete everything") is None  # allowlist rejects rm
    assert t.route("nonsense") is None           # no matching stub -> {"tool": 0}

    assert _FN_TO_ID["act_3"] == 3 and len(TOOL_SCHEMAS) == len(ACTION_IDS)
    print("tier2_model_router smoke OK")
