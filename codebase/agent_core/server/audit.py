"""Audit-wrapping and file tree builder shared by routes and ws_handler."""

from __future__ import annotations

import json
import os

from agent_core.tools.types import ToolResult

_WRITE_TOOLS = frozenset({
    "Write", "edit_file", "execute_command", "todo",
    "undo_last_edit", "git_commit", "kernel_store_context",
    "kernel_create_event", "kernel_emit_signal",
})


def _is_write_call(tool_name: str, raw) -> bool:
    if tool_name not in _WRITE_TOOLS:
        return False
    if tool_name == "todo":
        try:
            args = json.loads(raw) if isinstance(raw, str) else (raw or {})
            return str(args.get("action", "")) != "read"
        except Exception:
            return True
    return True


def build_tree(dir_path: str, max_depth: int = 4, depth: int = 0):
    if depth > max_depth:
        return {
            "name": os.path.basename(dir_path),
            "type": "dir",
            "children": [],
            "truncated": True,
        }
    try:
        entries = []
        for name in sorted(os.listdir(dir_path)):
            if name.startswith(".") or name.startswith("__pycache__"):
                continue
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                entries.append(build_tree(full, max_depth, depth + 1))
            else:
                entries.append({"name": name, "type": "file"})
        return {
            "name": os.path.basename(dir_path),
            "type": "dir",
            "children": entries,
        }
    except PermissionError:
        return {
            "name": os.path.basename(dir_path),
            "type": "dir",
            "children": [],
            "error": "permission denied",
        }


def make_audit_wrapper(active_tools_dict, rate_limiter, audit_log, redact, user_key):
    """Return a wrapped tools dict with audit-log, rate-limit, and redaction."""
    wrapped = {}
    for name, fn in active_tools_dict.items():
        def _make_wrapped(tool_name: str, original_fn):
            def _wrapped(*args, **kwargs):
                raw = args[0] if args else kwargs
                input_str = str(raw)
                if _is_write_call(tool_name, raw):
                    from agent_core.config import RATE_LIMIT_TOOL_WRITES
                    if not rate_limiter.check_write(user_key, RATE_LIMIT_TOOL_WRITES):
                        return ToolResult(ok=False, error_type="rate_limited",
                                          message="Write rate limit exceeded. Please wait.")
                result = original_fn(*args, **kwargs)
                if isinstance(result, ToolResult):
                    result.data = redact(result.data)
                    result.message = redact(result.message)
                    result_str = result.to_string()
                    audit_log.log(user_key, tool_name, input_str, "ok" if result.ok else "error")
                else:
                    result_str = redact(str(result))
                    audit_log.log(user_key, tool_name, input_str,
                                  "ok" if not result_str.startswith("Error") else "error")
                return result
            return _wrapped
        wrapped[name] = _make_wrapped(name, fn)
    return wrapped
