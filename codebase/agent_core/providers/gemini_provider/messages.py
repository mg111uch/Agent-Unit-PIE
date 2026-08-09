"""Internal chat messages <-> Gemini wire format conversions.

Conversions from internal messages to Interactions steps, to classic
generateContent contents, plus tool-schema pruning helpers used on
chained turns.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


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


def _active_decl_names(gc_tools) -> set[str]:
    """Names of the schemas already present in the payload."""
    return {
        d.get("name")
        for group in (gc_tools or [])
        for d in (group.get("function_declarations") or [])
        if d.get("name")
    }


def _prune_gc_tools(gc_tools, messages: List[Dict[str, Any]]):
    """Keep the turn's active tool set stable across the whole chain.

    The engine routes the user request to a small active group (tool_groups.py)
    once at the start of the turn; every chained step must keep THAT set and
    never widen back to a base set of schemas (PlanFixes2 #3/#4/#5). Only tools
    already used this turn are additionally preserved. Returns the original
    when nothing is pruned so callers can tell 'no-op' from 'reduced'.
    """
    keep = _active_decl_names(gc_tools) | _tools_used_this_turn(messages)
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