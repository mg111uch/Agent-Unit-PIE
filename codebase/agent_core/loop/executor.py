"""Tool call executor — runs tool calls and collects results."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from agent_core.config import MODEL_TOOL_RESULT_MAX_CHARS
from agent_core.response_parse import ParsedToolCall
from agent_core.tools import registry, ToolResult

# Bound every model-facing tool result (PlanFixes2 §8). The full raw output is
# never what the LLM needs; targeted follow-ups can refetch verbatim on demand.
_MODEL_RESULT_MAX = MODEL_TOOL_RESULT_MAX_CHARS

# Tools historically took a single string; native FC sends an object.
_STRING_ARG_KEYS: Dict[str, tuple[str, ...]] = {
    "Read": ("path", "input", "file"),
    "execute_command": ("command", "cmd", "input"),
    "glob_search": ("pattern", "glob", "input"),
    "check_path_exists": ("path", "input"),

}


def _normalize_tool_arg(name: str, arguments: Any) -> Any:
    if not isinstance(arguments, dict):
        return arguments
    keys = _STRING_ARG_KEYS.get(name)
    if not keys:
        return arguments
    extra = set(arguments) - set(keys)
    if extra:
        return arguments
    for k in keys:
        if arguments.get(k) is not None and arguments.get(k) != "":
            return arguments[k]
    if len(arguments) == 1:
        return next(iter(arguments.values()))
    return arguments


def _call_tool(name: str, fn: Callable, arguments: Any) -> Any:
    if isinstance(arguments, dict) and name in _STRING_ARG_KEYS:
        return fn(**arguments)
    return fn(arguments)


def _record_tool_call(name: str, duration_ms: float, is_error: bool, text: str) -> None:
    """Persist per-tool call stats for the native loop (parity with MCP path).
    Never breaks tool execution on DB failures."""
    try:
        from kernel.persistence.db import kernel_db
        kernel_db.record_tool_call(name, duration_ms, is_error, len(text))
    except Exception:
        pass


def execute_tool_calls(
    calls: List[ParsedToolCall],
    step: int,
    tools: Optional[Dict[str, Any]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> List[dict]:
    results = []
    _tools = tools or registry.tools_dict

    def _run_timed(name: str, fn: Callable, arguments: Any) -> tuple[Any, float, Optional[BaseException]]:
        t0 = time.perf_counter()
        try:
            res = _call_tool(name, fn, arguments)
            err = None
        except Exception as e:  # noqa: BLE001
            res, err = None, e
        return res, (time.perf_counter() - t0) * 1000, err

    def _missing(name: str) -> dict:
        _record_tool_call(name, 0.0, True, "tool not available")
        return {"tool": name, "result": f"Error: tool '{name}' not available.", "ok": False, "call_id": ""}

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
            fn = _tools.get("get_symbol")
            if fn is None:
                for tc in get_symbol_calls:
                    results.append({**_missing("get_symbol"), "call_id": tc.call_id or ""})
            else:
                result_obj, dur, err = _run_timed("get_symbol", fn, merged_args)
                if err is not None:
                    result_val = f"Error: {err}"
                    ok = False
                elif isinstance(result_obj, ToolResult):
                    ok = result_obj.ok
                    result_val = result_obj.to_string()[:_MODEL_RESULT_MAX]
                else:
                    result_str = str(result_obj)
                    result_val = result_str[:_MODEL_RESULT_MAX]
                    ok = not result_str.startswith("Error")
                _record_tool_call("get_symbol", dur, not ok, result_val)
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
                except Exception as e:  # noqa: BLE001
                    results.append({
                        "tool": tc.name, "result": f"Error: {e}", "ok": False,
                        "call_id": tc.call_id or "",
                    })
                    continue
                fn = _tools.get(tc.name)
                if fn is None:
                    results.append({**_missing(tc.name), "call_id": tc.call_id or ""})
                    continue
                result_obj, dur, err = _run_timed(tc.name, fn, arg)
                if err is not None:
                    result_str = f"Error: {err}"
                    is_ok = False
                elif isinstance(result_obj, ToolResult):
                    result_str = result_obj.to_string()
                    is_ok = result_obj.ok
                else:
                    result_str = str(result_obj)
                    is_ok = not result_str.startswith("Error")
                _record_tool_call(tc.name, dur, not is_ok, result_str)
                results.append({
                    "tool": tc.name,
                    "result": result_str[:_MODEL_RESULT_MAX],
                    "ok": is_ok,
                    "call_id": tc.call_id or "",
                })

    for tc in other_calls:
        if cancel_event and cancel_event.is_set():
            break
        try:
            arg = _normalize_tool_arg(tc.name, tc.arguments)
        except Exception as e:  # noqa: BLE001
            results.append({
                "tool": tc.name, "result": f"Error: {e}", "ok": False,
                "call_id": tc.call_id or "",
            })
            continue
        fn = _tools.get(tc.name)
        if fn is None:
            results.append({**_missing(tc.name), "call_id": tc.call_id or ""})
            continue
        result_obj, dur, err = _run_timed(tc.name, fn, arg)
        if err is not None:
            result_str = f"Error: {err}"
            is_ok = False
        elif isinstance(result_obj, ToolResult):
            result_str = result_obj.to_string()
            is_ok = result_obj.ok
        else:
            result_str = str(result_obj)
            is_ok = not result_str.startswith("Error")
        _record_tool_call(tc.name, dur, not is_ok, result_str)
        results.append({
            "tool": tc.name,
            "result": result_str[:_MODEL_RESULT_MAX],
            "ok": is_ok,
            "call_id": tc.call_id or "",
        })
    return results
