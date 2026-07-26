"""Shared helpers for the agent loop — extracted from engine.py to reduce file size."""

from __future__ import annotations

import json
import threading
from typing import Any, List, Optional

from agent_core.tools.types import ToolResult
from agent_core.loop.messages import build_corrective_msg


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
        tool_args["prepare_only"] = True
        prepare_raw = tools["debate_step"](tool_args)
        try:
            prepare = json.loads(prepare_raw) if isinstance(prepare_raw, str) else {}
        except Exception:
            prepare = {}
        if prepare.get("done"):
            return prepare_raw, []
        tool_args["prepare_only"] = False
        return tools["debate_step"](tool_args), prepare.get("questions", [])
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
