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
        f"Decide next step."
    )


def serialize_tool_input(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    try:
        return json.dumps(tool_input, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(tool_input)


def build_tool_calls_msg(tool_calls: List[ParsedToolCall]) -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "name": tc.name,
                "arguments": tc.arguments,
                "id": tc.call_id or "",
                "_call_id": tc.call_id or "",
            }
            for tc in tool_calls
        ],
    }


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
                "tool_call_id": r.get("call_id", "") or r.get("id", "") or r["tool"],
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
                "tool_call_id": call_id or tool,
            }
        ],
    }


def build_corrective_msg(text: str) -> dict:
    return {
        "role": "tool",
        "content": None,
        "tool_results": [{"tool": "parse", "result": text}],
    }
