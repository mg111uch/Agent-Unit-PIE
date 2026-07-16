"""Tool call executor — runs tool calls and collects results."""

from __future__ import annotations

import threading
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
    cancel_event: Optional[threading.Event] = None,
) -> List[dict]:
    results = []
    _tools = tools or registry.tools_dict

    # Merge parallel get_symbol calls into one batch (fan out same result to all call_ids)
    get_symbol_calls = [tc for tc in calls if tc.name == "get_symbol"]
    other_calls = [tc for tc in calls if tc.name != "get_symbol"]
    if get_symbol_calls:
        merged_names = []
        file_path = None
        for tc in get_symbol_calls:
            args = tc.arguments if isinstance(tc.arguments, dict) else {}
            name = args.get("name") or (args.get("names") or [None])[0]
            if name:
                merged_names.append(name)
            if not file_path:
                file_path = args.get("file_path")
        if len(merged_names) > 1:
            merged_args = {"names": merged_names}
            if file_path:
                merged_args["file_path"] = file_path
            try:
                result_obj = _tools["get_symbol"](merged_args)
                result_str = str(result_obj)
                result_val = result_str[:10000]
                ok = not result_str.startswith("Error")
            except Exception as e:
                result_val = f"Error: {e}"
                ok = False
            for tc in get_symbol_calls:
                results.append({
                    "tool": "get_symbol",
                    "result": result_val,
                    "ok": ok,
                    "call_id": tc.call_id or "",
                })
        else:
            for tc in get_symbol_calls:
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
                        "result": result_str[:10000],
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

    for tc in other_calls:
        if cancel_event and cancel_event.is_set():
            break
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
                "result": result_str[:10000],
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
