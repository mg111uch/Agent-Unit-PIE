"""Tools/schema normalization helpers for the Gemini provider.

Pure, stateless functions: OpenAI-style / legacy registry tool dicts to
Interactions-style flat tools, and OpenAI JSON-schema to Gemini Schema form.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


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
        if k in ("items", "anyOf"):
            if isinstance(v, dict) or isinstance(v, list):
                out[k] = _sanitize_gemini_schema(v)
            continue
        if k in _GEMINI_SCHEMA_SCALARS:
            out[k] = v
    return out