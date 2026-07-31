"""Shared helpers for the agent loop — extracted from engine.py to reduce file size."""

from __future__ import annotations

import json
import os
import threading
from typing import Any, List, Optional

from agent_core.config import CODEBASE_ROOT, DEBUG_DUMP_ENABLED, DEBUG_DUMP_APPEND_MODE
from agent_core.tools.types import ToolResult
from agent_core.loop.messages import build_corrective_msg

_DEBUG_LOG = os.path.join(CODEBASE_ROOT, "tui_output.txt")


def _debug_dump(mode: str, **kwargs):
    if not DEBUG_DUMP_ENABLED:
        return
    try:
        file_mode = "a" if DEBUG_DUMP_APPEND_MODE else ("w" if mode == "NEW TURN" else "a")
        with open(_DEBUG_LOG, file_mode) as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{mode}]\n")
            f.write(f"{'='*60}\n")
            for k, v in kwargs.items():
                label = k.replace("_", " ").title()
                if isinstance(v, str):
                    f.write(f"\n{label}:\n{v}\n")
                elif isinstance(v, (list, dict)):
                    f.write(f"\n{label}:\n{json.dumps(v, indent=2, default=str)}\n")
                else:
                    f.write(f"\n{label}:\n{str(v)}\n")
            f.write(f"{'='*60}\n")
    except Exception:
        pass


_QUESTION_TOOLS = {"ask_user_question", "debate_step"}

_DEFAULT_TOOL_CATEGORIES = None


def _truncate_result(result: str, max_chars: int = 2000) -> str:
    if len(result) <= max_chars:
        return result
    if result.strip().startswith(("{", "[")):
        truncated = result[:max_chars]
        last_close = max(truncated.rfind("}"), truncated.rfind("]"))
        if last_close > max_chars // 2:
            return truncated[:last_close + 1]
    return result[:max_chars]


def _compact_corrective_exchange(messages: list) -> list:
    if len(messages) < 3:
        return messages
    last_three = messages[-3:]
    roles = [m.get("role") for m in last_three]
    if roles == ["assistant", "tool", "user"]:
        asst = last_three[0]
        tool_msg = last_three[1]
        is_raw = asst.get("tool_calls") is None and "raw" in str(asst.get("content", ""))
        is_invalid = (
            "Unknown tool" in str(tool_msg.get("tool_results", ""))
            or "Your response must be valid JSON" in str(tool_msg.get("content", ""))
        )
        if is_raw or is_invalid:
            messages[-3:] = [{"role": "user", "content": "[format correction applied]"}]
    return messages


def _run_interactive_tool(
    tool_name: str,
    tool_args: dict,
    tools: dict,
    session_id: str,
) -> tuple[Any, list]:
    tool_args["_session_id"] = session_id
    if tool_name == "ask_user_question":
        return tools["ask_user_question"](tool_args), tool_args.get("questions", [])
    if tool_name == "debate_step":
        debate_fn = tools.get("debate_step")
        if debate_fn is None:
            return None, []
        tool_args["prepare_only"] = True
        prepare_raw = debate_fn(tool_args)
        try:
            prepare = json.loads(prepare_raw) if isinstance(prepare_raw, str) else {}
        except Exception:
            prepare = {}
        if prepare.get("done"):
            return prepare_raw, []
        tool_args["prepare_only"] = False
        return debate_fn(tool_args), prepare.get("questions", [])
    return None, []


def _handle_corrective_bookkeeping(
    use_messages: bool,
    current_messages: list,
    current_input: str,
    msg_store: Any,
    session_id: str,
    tool_name: str,
    corrective: str,
    followup: str,
) -> str:
    if use_messages:
        current_messages.append(build_corrective_msg(corrective))
        current_messages.append({"role": "user", "content": followup})
        msg_store.add_message(
            session_id=session_id, role="tool",
            content=None,
            tool_results=[{"tool": tool_name, "result": corrective}],
        )
        return current_input
    return current_input + "\n\n" + followup


def _check_cancelled(cancel_event, step, conv_id):
    """Yield final event if cancelled. Returns True if loop should exit."""
    if cancel_event and cancel_event.is_set():
        return {
            "type": "final", "content": "", "step": step,
            "conversation_id": conv_id, "full_content": "(cancelled)",
            "_exit": True,
        }
    return None


def _finish_tool_events(step_state, tool_name):
    """Append tool_call_history entry for a completed tool."""
    from agent_core.tools import registry
    step_state.tool_call_history.append({
        "name": tool_name, "_category": registry.get_category(tool_name),
    })


def _generate_with_cancel(
    orchestrator: Any,
    cancel_event: Optional[threading.Event],
    **kwargs: Any,
) -> Optional[dict]:
    """Run orchestrator.generate() in a daemon thread, signalling stop_flag on cancel."""
    result_holder: dict = {}
    stop_flag = threading.Event()

    def _run():
        result_holder["value"] = orchestrator.generate(cancel_flag=stop_flag, **kwargs)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    while t.is_alive():
        if cancel_event and cancel_event.is_set():
            stop_flag.set()
            return None
        t.join(timeout=0.5)
    return result_holder.get("value")
