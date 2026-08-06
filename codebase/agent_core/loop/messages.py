"""Message builder helpers for the agent loop."""

from __future__ import annotations

import json
from typing import Any, List

from agent_core.response_parse import ParsedToolCall


def tool_followup(tool: str, tool_input: Any, tool_result: Any) -> str:
    return (
        f"Tool used: {tool}\n"
        f"Input: {tool_input}\n"
        f"Result: {tool_result}\n"
        f"Answer the user's question now with a final answer. "
        f"Do not make another tool call unless you have no data to answer with yet."
    )


def short_followup() -> str:
    """Followup for messages-based loops where the tool result already lives in
    a preceding tool message — avoids duplicating the full result as text.
    """
    return (
        "Answer the user's question now with a final answer. "
        "Do not make another tool call unless you have no data to answer with yet."
    )


def serialize_tool_input(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    try:
        return json.dumps(tool_input, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(tool_input)


def build_tool_calls_msg(tool_calls: List[ParsedToolCall]) -> dict:
    calls = []
    for tc in tool_calls:
        call = {
            "name": tc.name,
            "arguments": tc.arguments,
            "id": tc.call_id or "",
            "_call_id": tc.call_id or "",
        }
        if tc.thought_signature:
            call["thought_signature"] = tc.thought_signature
        calls.append(call)
    return {"role": "assistant", "content": None, "tool_calls": calls}


def build_tool_results_msg(results: List[dict]) -> dict:
    return {
        "role": "tool",
        "content": None,
        "tool_results": [
            {
                "tool": r["tool"],
                "result": r["result"],
                "id": r.get("call_id", "") or r.get("id", ""),
                "_call_id": r.get("call_id", "") or r.get("id", ""),
                "tool_call_id": r.get("call_id", "") or r.get("id", ""),
            }
            for r in results
        ],
    }


def build_single_tool_result_msg(
    tool: str, result_str: str, call_id: str = ""
) -> dict:
    return {
        "role": "tool",
        "content": None,
        "tool_results": [
            {
                "tool": tool,
                "result": result_str,
                "id": call_id,
                "_call_id": call_id,
                "tool_call_id": call_id,
            }
        ],
    }


def build_corrective_msg(text: str) -> dict:
    return {
        "role": "tool",
        "content": None,
        "tool_results": [{"tool": "parse", "result": text}],
    }
