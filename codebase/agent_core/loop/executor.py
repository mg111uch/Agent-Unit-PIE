"""Tool call executor — runs tool calls and collects results."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.response_parse import ParsedToolCall
from agent_core.tools import registry, ToolResult


def execute_tool_calls(
    calls: List[ParsedToolCall],
    step: int,
    tools: Optional[Dict[str, Any]] = None,
) -> List[dict]:
    results = []
    _tools = tools or registry.tools_dict
    for tc in calls:
        try:
            result_obj = _tools[tc.name](tc.arguments)
            if isinstance(result_obj, ToolResult):
                result_str = result_obj.to_string()
                is_ok = result_obj.ok
            else:
                result_str = str(result_obj)
                is_ok = not result_str.startswith("Error")
            results.append({
                "tool": tc.name,
                "result": result_str[:500],
                "ok": is_ok,
            })
        except Exception as e:
            results.append({
                "tool": tc.name,
                "result": f"Error: {e}",
                "ok": False,
            })
    return results
