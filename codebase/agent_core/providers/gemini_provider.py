"""
llm/providers/gemini_provider.py

Gemini provider using the Interactions API (google-genai >= 2.3.0).
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Dict, Generator, List, Optional

from agent_core.config import (
    GEMINI_SKIP_TOOLS_ON_CHAIN,
    GEMINI_STATELESS,
    GEMINI_STATELESS_CACHE,
    GEMINI_STATELESS_SKIP_SCHEMAS,
    GEMINI_PRUNE_TOOLS_ON_CHAIN,
)
from agent_core.providers import BaseLLMProvider
from agent_core.providers.gemini_cache import GeminiContextCache


def _get(obj: Any, attr: str, default: Any = None) -> Any:
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default


def _format_tool_for_gemini(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize OpenAI-style, legacy gemini function_declarations, or flat tools."""
    result: List[Dict[str, Any]] = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        # Legacy generateContent wrapper: {"function_declarations": [...]}
        if "function_declarations" in t:
            for decl in t.get("function_declarations") or []:
                if not isinstance(decl, dict):
                    continue
                fd: dict[str, Any] = {
                    "type": "function",
                    "name": decl.get("name", ""),
                    "description": decl.get("description", ""),
                }
                params = decl.get("parameters") or decl.get("parameters_json_schema") or {}
                if params:
                    fd["parameters"] = params
                result.append(fd)
            continue

        # OpenAI / registry default: {"type": "function", "function": {...}}
        if "function" in t and isinstance(t["function"], dict):
            fn = t["function"]
            fd = {
                "type": "function",
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
            }
            params = fn.get("parameters") or {}
            if params:
                fd["parameters"] = params
            result.append(fd)
            continue

        # Already Interactions-style flat tool
        if t.get("type") == "function" or "name" in t:
            fd = {
                "type": "function",
                "name": t.get("name", ""),
                "description": t.get("description", ""),
            }
            params = t.get("parameters") or {}
            if params:
                fd["parameters"] = params
            result.append(fd)
    return result


def _parse_interaction(res: Any) -> dict[str, Any]:
    output = _get(res, "output_text", None) or ""

    tool_calls: list[dict[str, Any]] = []
    steps = _get(res, "steps", None) or []
    for step in steps:
        step_type = _get(step, "type")
        if step_type == "function_call":
            name = _get(step, "name", "")
            args = _get(step, "arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"input": args}
            call_id = _get(step, "id", "") or ""
            tool_calls.append({
                "id": call_id,
                "call_id": call_id,
                "name": name,
                "arguments": args if isinstance(args, dict) else {"input": args},
            })

    usage = _get(res, "usage", None)
    token_count = 0
    prompt_tokens = 0
    completion_tokens = 0
    if usage:
        token_count = _get(usage, "total_tokens", 0) or _get(usage, "total_token_count", 0) or 0
        prompt_tokens = (
            _get(usage, "prompt_tokens", 0)
            or _get(usage, "prompt_token_count", 0)
            or 0
        )
        completion_tokens = (
            _get(usage, "completion_tokens", 0)
            or _get(usage, "candidates_token_count", 0)
            or 0
        )

    if not tool_calls and output:
        try:
            parsed = json.loads(output)
            if "final" not in parsed and "action" not in parsed:
                output = json.dumps({"final": output})
        except json.JSONDecodeError:
            output = json.dumps({"final": output})

    return {
        "status": "success",
        "response": output,
        "tool_calls": tool_calls or None,
        "conversation_id": _get(res, "id", None),
        "usage": BaseLLMProvider._build_usage_dict(
            token_count, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    }


def _messages_to_steps(
    messages: List[Dict[str, Any]],
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """Convert internal chat messages to Interactions API steps."""
    sys_inst = None
    steps: list[dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "user")
        if role == "system":
            sys_inst = msg.get("content", "")
            continue
        content = msg.get("content")
        tool_calls = msg.get("tool_calls")
        tool_results = msg.get("tool_results")

        if role == "user":
            steps.append({
                "type": "user_input",
                "content": [{"type": "text", "text": content or ""}],
            })
        elif role == "assistant":
            if content:
                steps.append({
                    "type": "model_output",
                    "content": [{"type": "text", "text": content}],
                })
            if tool_calls:
                for tc in tool_calls:
                    call_id = (
                        tc.get("id")
                        or tc.get("_call_id")
                        or tc.get("call_id")
                        or ""
                    )
                    steps.append({
                        "type": "function_call",
                        "id": call_id,
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments", {}),
                    })
        elif role == "tool":
            if tool_results:
                for tr in tool_results:
                    call_id = (
                        tr.get("_call_id")
                        or tr.get("call_id")
                        or tr.get("id")
                        or tr.get("tool_call_id")
                        or ""
                    )
                    steps.append({
                        "type": "function_result",
                        "name": tr.get("tool", tr.get("name", "")),
                        "call_id": call_id,
                        "result": [{"type": "text", "text": tr.get("result", "")}],
                    })

    return steps, sys_inst


def _tools_fingerprint(tools: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Stable hash of the formatted tool schema set, or None when empty."""
    if not tools:
        return None
    formatted = _format_tool_for_gemini(tools)
    raw = json.dumps(formatted, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _tool_calls_valid(tools: Optional[List[Dict[str, Any]]], parsed: dict[str, Any]) -> bool:
    """Validate model tool_calls against the schema.

    Used when tools were skipped on a chained turn: if the model hallucinated
    unknown tool names or omitted required args, we should retry WITH tools.
    """
    tool_calls = parsed.get("tool_calls")
    if not tool_calls:
        return True
    if not tools:
        return False
    catalog: dict[str, list[str]] = {}
    for t in _format_tool_for_gemini(tools):
        name = t.get("name", "")
        required = []
        params = t.get("parameters") or {}
        if isinstance(params, dict):
            required = list(params.get("required") or [])
        catalog[name] = required
    for tc in tool_calls:
        name = tc.get("name", "")
        if name not in catalog:
            return False
        required = catalog[name] or []
        args = tc.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        missing = [r for r in required if r not in args]
        if missing:
            return False
    return True


def _tools_for_generate_content(tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """Build the classic generateContent `tools` payload from flat tool dicts.

    The registry emits OpenAI-style JSON schemas (additionalProperties, anyOf,
    etc.) which the generateContent API rejects, so each declaration's
    parameters are sanitized into Gemini Schema form first.
    """
    decls = []
    for t in _format_tool_for_gemini(tools or []):
        decl: dict[str, Any] = {"name": t.get("name", ""), "description": t.get("description", "")}
        if t.get("parameters"):
            decl["parameters"] = _sanitize_gemini_schema(t["parameters"])
        decls.append(decl)
    return [{"function_declarations": decls}] if decls else None


# Keys the classic generateContent Schema accepts. Anything else in the
# registry's OpenAI-style schema (additionalProperties, oneOf, $defs, ...) is
# dropped so the API doesn't reject the payload.
_GEMINI_SCHEMA_SCALARS = {
    "type", "format", "description", "title", "nullable", "enum", "default",
    "example", "minimum", "maximum", "minItems", "maxItems", "minLength",
    "maxLength", "minProperties", "maxProperties", "pattern", "required",
    "propertyOrdering",
}


def _sanitize_gemini_schema(node: Any) -> Any:
    """Recursively convert an OpenAI-style JSON schema to Gemini Schema form."""
    if isinstance(node, list):
        return [_sanitize_gemini_schema(x) for x in node]
    if not isinstance(node, dict):
        return node

    out: dict[str, Any] = {}
    for k, v in node.items():
        combined = k.replace("-", "").lower()
        if combined in ("additionalproperties", "additionalitems", "$schema",
                        "$defs", "definitions", "allof", "id"):
            continue
        if combined in ("oneof",):
            if isinstance(v, list):
                out["anyOf"] = [_sanitize_gemini_schema(x) for x in v]
            continue
        if k in ("properties",) and isinstance(v, dict):
            out["properties"] = {n: _sanitize_gemini_schema(s) for n, s in v.items()}
            continue
        if k in ("items", "anyOf") :
            if isinstance(v, dict) or isinstance(v, list):
                out[k] = _sanitize_gemini_schema(v)
            continue
        if k in _GEMINI_SCHEMA_SCALARS:
            out[k] = v
    return out


def _messages_to_contents(
    messages: List[Dict[str, Any]],
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """Convert internal chat messages to classic generateContent contents.

    Fully self-contained (no server-side state): tool calls become
    functionCall parts in model turns and their results become
    functionResponse parts in user turns.
    """
    sys_inst = None
    contents: list[dict[str, Any]] = []

    def _push(role: str, parts: list[dict[str, Any]]) -> None:
        if parts and (not contents or contents[-1]["role"] != role):
            contents.append({"role": role, "parts": parts})

    for msg in messages:
        role = msg.get("role", "user")
        if role == "system":
            sys_inst = msg.get("content", "")
            continue

        if role == "assistant":
            tool_calls = msg.get("tool_calls") or []
            content = msg.get("content")
            parts = []
            if content:
                parts.append({"text": content})
            for tc in tool_calls:
                call_id = tc.get("id") or tc.get("_call_id") or tc.get("call_id") or ""
                args = tc.get("arguments", {})
                if not isinstance(args, dict):
                    try:
                        args = {"input": args}
                    except Exception:
                        args = {"input": str(args)}
                part: dict[str, Any] = {
                    "functionCall": {"id": call_id, "name": tc.get("name", ""), "args": args},
                }
                if tc.get("thought_signature"):
                    part["thought_signature"] = tc["thought_signature"]
                parts.append(part)
            if parts:
                _push("model", parts)
        elif role == "tool":
            parts = []
            for tr in msg.get("tool_results") or []:
                call_id = (
                    tr.get("_call_id") or tr.get("call_id") or tr.get("id") or tr.get("tool_call_id") or ""
                )
                name = tr.get("tool", tr.get("name", ""))
                text = tr.get("result", "")
                if not isinstance(text, str):
                    text = json.dumps(text, ensure_ascii=False)
                if name == "parse" or not call_id:
                    parts.append({"text": text})
                else:
                    parts.append({
                        "functionResponse": {
                            "id": call_id,
                            "name": name,
                            "response": {"output": text},
                        },
                    })
            if parts:
                _push("user", parts)
        else:
            content = msg.get("content")
            if content:
                _push("user", [{"text": content}])

    return contents, sys_inst


def _thought_signature_for_replay(part: Any) -> str:
    """Reconstruct the wire `thoughtSignature` string from a response part.

    The SDK decodes the REST base64 value into bytes, so we re-encode to the
    exact string the API issued. Stateless generateContent requires the
    original signature on any functionCall part replayed in history.
    """
    ts = getattr(part, "thought_signature", None)
    if not ts:
        return ""
    if isinstance(ts, bytes):
        try:
            return base64.b64encode(ts).decode("ascii")
        except Exception:
            return ts.decode("utf-8", "replace")
    return str(ts)


def _parse_generate_content(res: Any) -> dict[str, Any]:
    """Parse a classic generateContent response into the internal format."""
    output = ""
    tool_calls: list[dict[str, Any]] = []

    candidates = getattr(res, "candidates", None) or []
    if candidates:
        content = getattr(candidates[0], "content", None)
        for part in (getattr(content, "parts", None) or []):
            text = getattr(part, "text", None)
            if text:
                output += text
            fc = getattr(part, "function_call", None)
            if fc:
                name = getattr(fc, "name", "") or ""
                args = getattr(fc, "args", None) or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"input": args}
                call_id = getattr(fc, "id", None) or ""
                tool_calls.append({
                    "id": call_id,
                    "call_id": call_id,
                    "name": name,
                    "arguments": args if isinstance(args, dict) else {"input": args},
                    "thought_signature": _thought_signature_for_replay(part),
                })

    usage = getattr(res, "usage_metadata", None)
    total = getattr(usage, "total_token_count", 0) or 0
    prompt = getattr(usage, "prompt_token_count", 0) or 0
    completion = getattr(usage, "candidates_token_count", 0) or 0
    cached = getattr(usage, "cached_content_token_count", 0) or 0
    # prompt_token_count includes tokens served from the context cache, which
    # bill at the discounted cached-input rate. Report the fresh (non-cached)
    # tokens so the stateless per-call bloat reflects what is actually paid for.
    prompt = max(0, prompt - cached)
    total = max(0, total - cached)

    return {
        "status": "success",
        "response": output,
        "tool_calls": tool_calls or None,
        "conversation_id": None,
        "usage": BaseLLMProvider._build_usage_dict(
            total, prompt_tokens=prompt, completion_tokens=completion
        ) | {"cached_tokens": int(cached)},
    }


def _is_chained_turn(messages: List[Dict[str, Any]]) -> bool:
    """True when tools were already used since the current user prompt — i.e.
    the conversation currently ends in a tool exchange (tool results or a
    fresh tool call). Each new user prompt starts a turn, so tool schemas and
    the system prompt are re-sent at the start of every user prompt and omitted
    on the tool-chain follow-ups within it.
    """
    if not messages:
        return False
    last = messages[-1]
    role = last.get("role")
    if role == "tool" and last.get("tool_results"):
        return True
    if role == "assistant" and last.get("tool_calls"):
        return True
    return False


# Tools always re-sent on chained turns; everything else is pruned so the
# per-call schema stays small (Issues2.md: dynamic tool exposure). Mirrors the
# OpenRouter config set.
_CHAIN_BASE_TOOLS = {
    "read_file", "list_files", "grep_search", "glob_search",
    "execute_command", "edit_file", "write_to_file",
}


def _tools_used_this_turn(messages: List[Dict[str, Any]]) -> set[str]:
    used: set[str] = set()
    for msg in reversed(messages):
        if msg.get("role") == "user" and msg.get("content"):
            break
        for tc in msg.get("tool_calls") or []:
            name = tc.get("name", "")
            if name:
                used.add(name)
    return used


def _prune_gc_tools(gc_tools, messages: List[Dict[str, Any]]):
    """Reduce the classic generateContent tools payload to the base set + tools
    already used this turn. Returns the original when nothing is pruned so
    callers can tell 'no-op' from 'reduced'.
    """
    keep = _CHAIN_BASE_TOOLS | _tools_used_this_turn(messages)
    total = 0
    pruned_decls = []
    for group in gc_tools or []:
        decls = group.get("function_declarations") or []
        total += len(decls)
        kept = [d for d in decls if d.get("name") in keep]
        if kept:
            pruned_decls.append({"function_declarations": kept})
    kept_count = sum(len(g.get("function_declarations") or []) for g in pruned_decls)
    if kept_count < total:
        return pruned_decls or None
    return gc_tools


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash"):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.default_model = model
        self._supports_stateful = True
        self._last_tools_fp: Optional[str] = None
        self._gemini_cache: Optional[GeminiContextCache] = None

    def generate(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if messages:
            if GEMINI_STATELESS:
                # Client-managed history: send the full (compacted) conversation
                # every call with store=False so billed context is bounded by our
                # compaction, not by Gemini's server-side chain retention.
                return self._generate_stateless(
                    messages,
                    model or self.default_model,
                    system_prompt,
                    tools,
                )
            if conversation_id:
                return self._generate_stateful(
                    messages,
                    model or self.default_model,
                    system_prompt,
                    tools,
                    conversation_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            # First turn: store server-side so previous_interaction_id chaining works.
            # Do not use store=False here — that breaks tool follow-ups with 400.
            return self._generate_initial_from_messages(
                messages,
                model or self.default_model,
                system_prompt,
                tools,
            )

        model_name = model or self.default_model
        call_kwargs: dict[str, Any] = {"model": model_name}

        if conversation_id:
            call_kwargs["previous_interaction_id"] = conversation_id
            call_kwargs["input"] = prompt
            if system_prompt:
                call_kwargs["system_instruction"] = system_prompt
        else:
            full = prompt
            if system_prompt:
                full = f"{system_prompt}\n\n{prompt}"
            call_kwargs["input"] = full

        fp = _tools_fingerprint(tools)
        skip_tools = bool(
            conversation_id
            and fp
            and GEMINI_SKIP_TOOLS_ON_CHAIN
            and fp == self._last_tools_fp
        )
        if not skip_tools and fp:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
        self._last_tools_fp = fp

        try:
            res = self.client.interactions.create(**call_kwargs)
        except Exception:
            if "tools" not in call_kwargs and fp:
                call_kwargs["tools"] = _format_tool_for_gemini(tools)
                res = self.client.interactions.create(**call_kwargs)
            else:
                raise
        parsed = _parse_interaction(res)
        if skip_tools and fp and not _tool_calls_valid(tools, parsed):
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
            try:
                res = self.client.interactions.create(**call_kwargs)
            except Exception:
                pass
            else:
                parsed = _parse_interaction(res)
        return parsed

    def _generate_with_messages(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return self._generate_initial_from_messages(
            messages, model or self.default_model, system_prompt, tools,
        )

    def _generate_initial_from_messages(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """First Interactions turn: store history server-side for later chaining."""
        steps, sys_inst = _messages_to_steps(messages)

        call_kwargs: dict[str, Any] = {
            "model": model,
            "input": steps,
        }
        if system_prompt or sys_inst:
            call_kwargs["system_instruction"] = system_prompt or sys_inst
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
            self._last_tools_fp = _tools_fingerprint(tools)

        res = self.client.interactions.create(**call_kwargs)
        return _parse_interaction(res)

    def _generate_stateful(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
        conversation_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Continue a server-side conversation; send only the latest turn + tool results."""
        pending_results: list[dict[str, Any]] = []
        last_user = None

        for msg in messages:
            role = msg.get("role", "user")
            if role == "user" and msg.get("content"):
                last_user = msg["content"]
                pending_results = []
            elif role == "tool":
                for tr in msg.get("tool_results") or []:
                    call_id = (
                        tr.get("_call_id")
                        or tr.get("call_id")
                        or tr.get("id")
                        or tr.get("tool_call_id")
                        or ""
                    )
                    name = tr.get("tool", tr.get("name", ""))
                    if name == "parse" or not call_id:
                        text = tr.get("result", "")
                        if text:
                            last_user = text
                        continue
                    text = tr.get("result", "")
                    if not isinstance(text, str):
                        text = json.dumps(text, ensure_ascii=False)
                    step: dict[str, Any] = {
                        "type": "function_result",
                        "name": name,
                        "call_id": call_id,
                        "result": [{"type": "text", "text": text}],
                    }
                    if isinstance(text, str) and text.startswith("Error"):
                        step["is_error"] = True
                    pending_results.append(step)

        if pending_results:
            input_data: Any = pending_results
        elif last_user:
            # Fall back to last user text (e.g. corrective follow-ups without call_id)
            input_data = last_user
        else:
            # Never send an empty-string input — some API versions reject or
            # waste a call on it.
            input_data = "(continue)"

        call_kwargs: dict[str, Any] = {
            "model": model,
            "previous_interaction_id": conversation_id,
            "input": input_data,
        }
        # Do not resend system_instruction on chained turns (can cause invalid_request).
        fp = _tools_fingerprint(tools)
        skip_tools = bool(
            fp and GEMINI_SKIP_TOOLS_ON_CHAIN and fp == self._last_tools_fp
        )
        if not skip_tools and fp:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
        self._last_tools_fp = fp

        try:
            res = self.client.interactions.create(**call_kwargs)
        except Exception:
            # If we skipped tools (schema persisted server-side) but the API
            # actually required them, retry once with tools attached.
            if "tools" not in call_kwargs and fp:
                call_kwargs["tools"] = _format_tool_for_gemini(tools)
                res = self.client.interactions.create(**call_kwargs)
            else:
                raise
        parsed = _parse_interaction(res)
        # Skipped tools can make the model hallucinate tool names/args on a
        # chained turn (no schema visible). If so, retry once WITH tools.
        if skip_tools and fp and not _tool_calls_valid(tools, parsed):
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
            try:
                res = self.client.interactions.create(**call_kwargs)
            except Exception:
                pass
            else:
                parsed = _parse_interaction(res)
        return parsed

    def _generate_stateless(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Client-managed history via the classic generateContent API.

        Fully self-contained per call: the (client-compacted) conversation is
        sent every time, so billed context is bounded by our compaction. Uses
        generateContent, NOT interactions with store=False (which rejects tool
        follow-ups with a 400 invalid_request).
        """
        contents, sys_inst = _messages_to_contents(messages)
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "(continue)"}]}]

        sys_text = (system_prompt or sys_inst or "").strip()
        gc_tools = _tools_for_generate_content(tools)
        chained = _is_chained_turn(messages)
        skip_schemas = GEMINI_STATELESS_SKIP_SCHEMAS
        use_cache = GEMINI_STATELESS_CACHE

        if self._gemini_cache is None:
            self._gemini_cache = GeminiContextCache(self.client, model)
        cache = self._gemini_cache

        if chained:
            # Tool-chaining step within a turn: do NOT resend the (8k-char)
            # system prompt — it was already sent at the start of this turn.
            # When the full cache exists the model still sees it (billed at the
            # discounted cached-input rate); otherwise it continues from the
            # conversation alone. Schemas are omitted only when skip_schemas is
            # enabled, with a retry below if the model still emits a tool call.
            use_tools = not skip_schemas
            if use_tools and gc_tools and GEMINI_PRUNE_TOOLS_ON_CHAIN:
                gc_tools = _prune_gc_tools(gc_tools, messages)
            cache_name = cache.existing(sys_text, gc_tools, sys_only=False) if use_cache else None
            config: dict[str, Any] = {"temperature": temperature, "max_output_tokens": max_tokens}
            if cache_name:
                config["cached_content"] = cache_name
            elif use_tools and gc_tools:
                config["tools"] = gc_tools
        else:
            # Start of a turn: send the full system prompt + schemas (cached).
            use_tools = True
            cache_name = cache.ensure(sys_text, gc_tools, sys_only=False) if use_cache else None
            config = {"temperature": temperature, "max_output_tokens": max_tokens}
            if cache_name:
                config["cached_content"] = cache_name
            else:
                if sys_text:
                    config["system_instruction"] = sys_text
                if gc_tools:
                    config["tools"] = gc_tools

        try:
            res = self.client.models.generate_content(
                model=model, contents=contents, config=config,
            )
        except Exception:
            # Stale/expired cache reference — drop it and retry once inline.
            if cache_name:
                cache.invalidate()
                config = {"temperature": temperature, "max_output_tokens": max_tokens}
                if not chained and sys_text:
                    config["system_instruction"] = sys_text
                if use_tools and gc_tools:
                    config["tools"] = gc_tools
                res = self.client.models.generate_content(
                    model=model, contents=contents, config=config,
                )
            else:
                raise
        parsed = _parse_generate_content(res)

        # Chained turn with schemas skipped: if the model still emitted a real
        # tool call (it couldn't have seen a schema), retry once WITH tools.
        if (
            chained
            and use_tools is False
            and gc_tools
            and parsed.get("tool_calls")
            and _tool_calls_valid(tools, parsed)
        ):
            full_cache = cache.ensure(sys_text, gc_tools, sys_only=False) if use_cache else None
            retry_config: dict[str, Any] = {"temperature": temperature, "max_output_tokens": max_tokens}
            if full_cache:
                retry_config["cached_content"] = full_cache
            elif gc_tools:
                retry_config["tools"] = gc_tools
            try:
                res = self.client.models.generate_content(
                    model=model, contents=contents, config=retry_config,
                )
            except Exception:
                pass
            else:
                parsed = _parse_generate_content(res)

        parsed["conversation_id"] = None
        return parsed

    def generate_stream(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        if messages:
            if GEMINI_STATELESS:
                contents, extracted_system = _messages_to_contents(messages)
                if not contents:
                    contents = [{"role": "user", "parts": [{"text": "(continue)"}]}]
                config: dict[str, Any] = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                sys_inst = system_prompt or extracted_system
                config = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                gc_tools = _tools_for_generate_content(tools)
                chained = _is_chained_turn(messages)
                if chained and gc_tools and GEMINI_PRUNE_TOOLS_ON_CHAIN:
                    gc_tools = _prune_gc_tools(gc_tools, messages)
                cache_name = None
                if self._gemini_cache is not None and GEMINI_STATELESS_CACHE:
                    cache_name = self._gemini_cache.existing(
                        (system_prompt or sys_inst or "").strip(), gc_tools, sys_only=False,
                    )
                if cache_name:
                    config["cached_content"] = cache_name
                else:
                    if not chained and sys_inst:
                        config["system_instruction"] = sys_inst
                    if gc_tools:
                        config["tools"] = gc_tools
                stream = self.client.models.generate_content_stream(
                    model=model or self.default_model, contents=contents, config=config,
                )
                for chunk in stream:
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
                return
            input_data, extracted_system = _messages_to_steps(messages)
            sys_inst = system_prompt or extracted_system
        else:
            full = prompt
            if system_prompt:
                full = f"{system_prompt}\n\n{prompt}"
            sys_inst = None
            input_data = full

        call_kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "input": input_data,
            "stream": True,
        }
        if conversation_id:
            call_kwargs["previous_interaction_id"] = conversation_id
        if sys_inst:
            call_kwargs["system_instruction"] = sys_inst
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)

        for event in self.client.interactions.create(**call_kwargs):
            if _get(event, "event_type") == "step.delta":
                delta = _get(event, "delta")
                if delta and _get(delta, "type") == "text":
                    text = _get(delta, "text")
                    if text:
                        yield text
