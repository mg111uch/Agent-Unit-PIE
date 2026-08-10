"""Phase 6 — local tool router (PlanRecommend3 three-tier, tier 2).

Tier 1 is the deterministic factory (`tool_groups.try_factory`). When it
declines (ambiguous request) tier 2 asks a tiny local model — FunctionGemma
or similar on Ollama — to map the plain-language request to ONE canonical
action, using a fixed action-ID vocabulary (PlanRecommend3 §5/§6) so the
output is tiny and the cloud model never sees tool schemas.

Validator/policy before execution (PlanRecommend3 §7): unknown tool IDs are
rejected, `execute_command` is allowlist-checked, payloads are capped. Any
failure returns None → tier 3 (cloud Gemini) recovery.

Backend is pluggable: `OllamaProvider` for live, a deterministic stub for the
offline benchmark (proves wiring with 0 cloud calls, no local model needed).
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from agent_core.config import ALLOWED_COMMANDS

# Fixed action-ID vocabulary (tiny local output). id -> (tool name, arg keys).
ACTION_IDS: dict[int, tuple[str, tuple[str, ...]]] = {
    1: ("Read", ("path",)),                          # read file
    2: ("Read", ("path",)),                          # list directory (Read lists dirs)
    3: ("Write", ("path", "content")),
    4: ("edit_file", ("path", "old_string", "new_string")),
    5: ("execute_command", ("command",)),
    6: ("glob_search", ("pattern",)),
    7: ("grep_search", ("pattern", "include")),
    8: ("check_path_exists", ("path",)),
    9: ("get_workspace_info", ()),
}

_ID_TOOL = {i: spec[0] for i, spec in ACTION_IDS.items()}

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


class LocalRouter:
    """Maps an ambiguous request to a validated tool action via a local model."""

    def __init__(
        self,
        provider: Any,
        *,
        enabled: bool = True,
        max_tokens: int = 80,
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
            )
        except Exception:
            return None
        if not raw or raw.get("error"):
            return None
        parsed = _parse_action(raw.get("response") or "")
        if not parsed:
            return None
        name = _ID_TOOL[parsed["id"]]
        args = {k: v for k, v in parsed["args"].items() if isinstance(v, (str, bool, int, float))}
        if not self._policy(name, args):
            return None
        return {"name": name, "input": args}


def build_local_router() -> Optional[LocalRouter]:
    """Wire the router from config (LOCAL_ROUTER_ENABLED); None when disabled."""
    import agent_core.config as cfg
    if not cfg.LOCAL_ROUTER_ENABLED:
        return None
    try:
        from agent_core.providers.ollama_provider import OllamaProvider
        return LocalRouter(
            OllamaProvider(
                model=cfg.LOCAL_ROUTER_MODEL,
                endpoint=cfg.LOCAL_ROUTER_ENDPOINT,
                timeout=cfg.LOCAL_ROUTER_TIMEOUT,
            ),
            enabled=True,
        )
    except Exception:
        return None


def deterministic_router(labels: dict[str, str]) -> LocalRouter:
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
    return LocalRouter(_Stub(labels), enabled=True)


if __name__ == "__main__":
    # Smoke test — run with: python -m agent_core.planning.local_router
    r = deterministic_router({
        "sum the file": '{"tool": 1, "args": {"path": "x.py"}}',
        "run pytest": '{"tool": 5, "args": {"command": "pytest"}}',
        "rm things": '{"tool": 5, "args": {"command": "rm -rf /"}}',
    })
    assert r.route("sum the file") == {"name": "Read", "input": {"path": "x.py"}}
    assert r.route("run pytest") == {"name": "execute_command", "input": {"command": "pytest"}}
    assert r.route("rm things") is None      # policy blocks non-allowlisted exec
    assert r.route("blah blah") is None      # unknown action id -> None
    assert LocalRouter(None).route(" x ") is None  # disabled/empty handling
    print("local_router smoke OK")