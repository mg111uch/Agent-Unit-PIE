"""Tool call executor — runs tool calls and collects results."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.response_parse import ParsedToolCall
from agent_core.tools import registry, ToolResult

# Tools historically took a single string; native FC sends an object.
_STRING_ARG_KEYS: Dict[str, tuple[str, ...]] = {
    "read_file": ("path", "input", "file"),
    "list_files": ("path", "input", "directory", "dir"),
    "execute_command": ("command", "cmd", "input"),
    "glob_search": ("pattern", "glob", "input"),
}


def _normalize_tool_arg(name: str, arguments: Any) -> Any:
    if not isinstance(arguments, dict):
        return arguments
    keys = _STRING_ARG_KEYS.get(name)
    if not keys:
        return arguments
    for k in keys:
        if arguments.get(k) is not None and arguments.get(k) != "":
            return arguments[k]
    if len(arguments) == 1:
        return next(iter(arguments.values()))
    if name == "list_files" and not arguments:
        return "."
    return arguments


def execute_tool_calls(
    calls: List[ParsedToolCall],
    step: int,
    tools: Optional[Dict[str, Any]] = None,
) -> List[dict]:
    results = []
    _tools = tools or registry.tools_dict
    for tc in calls:
        try:
            arg = _normalize_tool_arg(tc.name, tc.arguments)
            result_obj = _tools[tc.name](arg)
            if isinstance(result_obj, ToolResult):
                result_str = result_obj.to_string()
                is_ok = result_obj.ok and not result_str.startswith("Error")
            else:
                result_str = str(result_obj)
                is_ok = not result_str.startswith("Error")
            results.append({
                "tool": tc.name,
                "result": result_str[:500],
                "ok": is_ok,
                "call_id": tc.call_id or "",
            })
        except Exception as e:
            results.append({
                "tool": tc.name,
                "result": f"Error: {e}",
                "ok": False,
                "call_id": tc.call_id or "",
            })
    return results
