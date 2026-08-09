"""Response parsing for the Gemini provider (pure).

Parses Interactions API and classic generateContent responses into the
internal `{status, response, tool_calls, conversation_id, usage}` format.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from agent_core.providers import BaseLLMProvider


def _get(obj: Any, attr: str, default: Any = None) -> Any:
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default


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
    # Keep Gemini's RAW prompt account intact and expose the fresh (non-cached)
    # share separately (PlanFixes2 §9): never overwrite provider_prompt_tokens
    # with the fresh number. Billing analysis can subtract raw - cached itself.
    fresh = max(0, prompt - cached)

    return {
        "status": "success",
        "response": output,
        "tool_calls": tool_calls or None,
        "conversation_id": None,
        "usage": BaseLLMProvider._build_usage_dict(
            total, prompt_tokens=prompt, completion_tokens=completion, cached_tokens=cached,
            extra={
                "provider_prompt_tokens": prompt,
                "provider_cached_tokens": cached,
                "fresh_prompt_tokens": fresh,
            },
        ),
    }