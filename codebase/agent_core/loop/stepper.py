"""Step dispatch and state management for the agent loop."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Generator

from agent_core.tools import ToolResult, registry
from agent_core.loop._helpers import (
    _truncate_result,
    _compact_corrective_exchange,
    _run_interactive_tool,
    _handle_corrective_bookkeeping,
    _debug_dump,
    _check_cancelled,
    _finish_tool_events,
    _QUESTION_TOOLS,
)
from agent_core.loop.messages import (
    tool_followup,
    serialize_tool_input,
    build_tool_calls_msg,
    build_tool_results_msg,
    build_single_tool_result_msg,
)
from agent_core.loop.streaming import stream_final
from agent_core.loop.executor import execute_tool_calls
from agent_core.loop.session_state import SessionState

_EDIT_TOOLS = ("edit_file", "write_to_file")


def _deadline_corrective(step: int) -> str:
    return (
        f"\n\n[CORRECTIVE] You have made {step + 1} tool calls without producing a final answer. "
        f"Stop and answer the user's question now."
    )


@dataclass
class StepState:
    current_messages: list
    current_input: str
    last_tool: str | None = None
    last_result: str | None = None
    consecutive_failures: int = 0
    consecutive_raw_failures: int = 0
    tool_call_history: list = field(default_factory=list)


def dispatch_step(
    parsed,
    step_state: StepState,
    *,
    step: int,
    step_delay: float,
    msg_store: Any,
    session_id: str | None,
    cancel_event: Any,
    tools: dict,
    local_planner: Any,
    state: SessionState,
    use_messages: bool,
    conv_id: str | None,
    local_step: bool,
    reply: str,
) -> Generator[dict, None, bool]:
    """Yield events for one agent step, return True if loop should exit."""

    # --- raw (parse failure) ---
    if parsed.kind == "raw":
        step_state.consecutive_raw_failures += 1
        if step_state.consecutive_raw_failures >= 2:
            yield from stream_final(parsed.content or "(done)", step, conv_id)
            return True
        corrective = (
            f"Your response must be valid JSON only with "
            f"'action'/'input' or 'final'. No free text or markdown. "
            f"Valid tools: {', '.join(sorted(tools.keys()))}."
        )
        yield {
            "type": "tool_result",
            "tool": "parse", "input": "", "result": corrective, "ok": False, "step": step,
        }
        corrective_text = tool_followup("parse", "", corrective)
        if use_messages:
            _compact_corrective_exchange(step_state.current_messages)
        step_state.current_input = _handle_corrective_bookkeeping(
            use_messages, step_state.current_messages, step_state.current_input,
            msg_store, session_id, "parse", corrective, corrective_text,
        )
        if local_step and local_planner:
            local_planner.record_fallback()
        return False

    # --- final ---
    if parsed.kind == "final":
        if not (parsed.content or "").strip():
            corrective = (
                "Your response was empty. Summarize what you accomplished or what's blocking you."
            )
            yield {
                "type": "tool_result",
                "tool": "parse", "input": "", "result": corrective, "ok": False, "step": step,
            }
            followup_text = tool_followup("parse", "", corrective)
            if use_messages:
                step_state.current_messages.append({"role": "user", "content": followup_text})
            else:
                step_state.current_input += "\n\n" + followup_text
            return False
        _debug_dump("FINAL", step=step, response=parsed.content or "")
        if use_messages:
            msg_store.add_message(
                session_id=session_id, role="assistant", content=parsed.content or "",
            )
        yield {
            "type": "summary", "step": step, "total_steps": step,
            "cache_hits": state.cache_hits, "cache_misses": state.cache_misses,
        }
        yield from stream_final(
            parsed.content or "", step=step, conversation_id=conv_id, cancel_event=cancel_event,
        )
        return True

    # --- invalid_tool ---
    if parsed.kind == "invalid_tool":
        valid_tools = ", ".join(sorted(tools.keys()))
        corrective = (
            f"Unknown tool: '{parsed.tool}'. "
            f"Valid tools are: {valid_tools}. Respond with a valid tool."
        )
        yield {
            "type": "tool_result",
            "tool": parsed.tool or "unknown", "input": "", "result": corrective, "ok": False, "step": step,
        }
        followup_text = tool_followup(parsed.tool or "unknown", "", corrective)
        if use_messages:
            _compact_corrective_exchange(step_state.current_messages)
        step_state.current_input = _handle_corrective_bookkeeping(
            use_messages, step_state.current_messages, step_state.current_input,
            msg_store, session_id, parsed.tool or "unknown", corrective, followup_text,
        )
        if local_step and local_planner:
            local_planner.record_fallback()
        return False

    # --- multi tool_calls ---
    if parsed.kind == "tool_calls":
        if use_messages:
            _compact_corrective_exchange(step_state.current_messages)
            step_state.current_messages.append(build_tool_calls_msg(parsed.tool_calls))
            msg_store.add_message(
                session_id=session_id, role="assistant", content=None,
                tool_calls=[
                    {"name": tc.name, "arguments": tc.arguments, "id": tc.call_id or "", "_call_id": tc.call_id or ""}
                    for tc in parsed.tool_calls
                ],
            )

        for tc in parsed.tool_calls:
            input_str = serialize_tool_input(tc.arguments)
            yield {
                "type": "tool_call", "tool": tc.name, "input": input_str,
                "call_id": tc.call_id or "", "step": step,
            }

        question_calls = [tc for tc in parsed.tool_calls if tc.name in _QUESTION_TOOLS]
        other_calls = [tc for tc in parsed.tool_calls if tc.name not in _QUESTION_TOOLS]

        if question_calls:
            if other_calls or len(question_calls) > 1:
                name = question_calls[0].name
                results = [{
                    "tool": name, "result": f"Error: {name} cannot be combined with other tools in the same turn.",
                    "ok": False, "call_id": question_calls[0].call_id or "",
                }]
            else:
                tc = question_calls[0]
                arg = tc.arguments if isinstance(tc.arguments, dict) else {}
                result_obj, questions = _run_interactive_tool(tc.name, arg, tools, session_id)
                if questions:
                    yield {
                        "type": "question", "questions": questions,
                        "session_id": session_id, "step": step,
                    }
                if isinstance(result_obj, ToolResult):
                    result_str = result_obj.to_string()
                    is_ok = result_obj.ok
                else:
                    result_str = str(result_obj)
                    is_ok = not result_str.startswith("Error")
                results = [{"tool": tc.name, "result": result_str, "ok": is_ok, "call_id": tc.call_id or ""}]
        else:
            results = execute_tool_calls(parsed.tool_calls, step, tools=tools, cancel_event=cancel_event)

        cancelled = _check_cancelled(cancel_event, step, conv_id)
        if cancelled:
            yield cancelled
            return True

        all_ok = all(r.get("ok", True) for r in results)

        for tc, result in zip(parsed.tool_calls, results):
            input_str = serialize_tool_input(tc.arguments)
            yield {
                "type": "tool_result", "tool": result["tool"], "input": input_str,
                "result": _truncate_result(result.get("result", ""), 2000),
                "ok": result.get("ok", True),
                "call_id": result.get("call_id", tc.call_id or ""), "step": step,
            }
            _finish_tool_events(step_state, tc.name)
        if local_step and local_planner:
            local_planner.record_success()

        _debug_dump("TOOL RESULTS (multi)",
            step=step,
            calls=[{"name": tc.name, "args": tc.arguments, "call_id": tc.call_id} for tc in parsed.tool_calls],
            results=results,
        )

        if use_messages:
            step_state.current_messages.append(build_tool_results_msg(results))
            msg_store.add_message(
                session_id=session_id, role="tool", content=None,
                tool_results=[
                    {"tool": r["tool"], "result": r["result"],
                     "id": r.get("call_id", ""), "_call_id": r.get("call_id", ""),
                     "tool_call_id": r.get("call_id", "")}
                    for r in results
                ],
            )

        if not all_ok:
            failed = [r for r in results if not r.get("ok", True)]
            if len(failed) >= 3:
                corrective = (
                    f"\n\n[CORRECTIVE] Multiple tools failed. "
                    f"Re-read state using get_workspace_info / list_files / read_file."
                )
                if use_messages:
                    step_state.current_messages.append({"role": "user", "content": corrective})
                else:
                    step_state.current_input += corrective

        if step >= 4:
            all_editing = all(r.get("tool") in _EDIT_TOOLS for r in results)
            if not all_editing:
                msg = _deadline_corrective(step)
                if use_messages:
                    step_state.current_messages.append({"role": "user", "content": msg})
                else:
                    step_state.current_input += msg

        return False

    # --- single tool ---
    if parsed.kind == "tool":
        yield {"type": "step_reply", "content": reply, "step": step}

        tool = parsed.tool
        tool_input = parsed.tool_input
        input_str = serialize_tool_input(tool_input)

        yield {"type": "tool_call", "tool": tool, "input": input_str, "step": step}

        if tool in _QUESTION_TOOLS:
            tool_arg = tool_input if isinstance(tool_input, dict) else {}
            if isinstance(tool_input, str):
                try:
                    tool_arg = json.loads(tool_input)
                except json.JSONDecodeError:
                    tool_arg = {"input": tool_input}
            if tool == "debate_step" and not isinstance(tool_arg, dict):
                tool_arg = {"topic": str(tool_input)}
            result_obj, questions = _run_interactive_tool(tool, tool_arg, tools, session_id)
            if questions:
                yield {
                    "type": "question", "questions": questions,
                    "session_id": session_id, "step": step,
                }
        else:
            result_obj = tools[tool](tool_input)

        cancelled = _check_cancelled(cancel_event, step, conv_id)
        if cancelled:
            yield cancelled
            return True

        if isinstance(result_obj, ToolResult):
            result_str = result_obj.to_string()
            is_error = not result_obj.ok
            ok = result_obj.ok
        else:
            result_str = str(result_obj)
            is_error = result_str.startswith("Error")
            ok = not is_error

        yield {
            "type": "tool_result", "tool": tool, "input": input_str,
            "result": _truncate_result(result_str, 2000), "ok": ok, "step": step,
        }

        _finish_tool_events(step_state, tool)
        if local_step and local_planner:
            local_planner.record_success()

        _debug_dump("TOOL RESULT (single)",
            step=step, tool=tool, input=parsed.tool_input, result=result_str, ok=ok,
        )

        if use_messages:
            step_state.current_messages.append({
                "role": "assistant", "content": reply,
                "tool_calls": [{"name": tool, "arguments": tool_input if isinstance(tool_input, dict) else {"input": tool_input}}],
            })
            msg_store.add_message(
                session_id=session_id, role="assistant", content=reply,
                tool_calls=[{"name": tool, "arguments": tool_input if isinstance(tool_input, dict) else {"input": tool_input}}],
            )
            step_state.current_messages.append(build_single_tool_result_msg(tool, result_str))
            msg_store.add_message(
                session_id=session_id, role="tool", content=None,
                tool_results=[{"tool": tool, "result": result_str}],
            )

        if is_error:
            if tool == step_state.last_tool and result_str == step_state.last_result:
                step_state.consecutive_failures += 1
            else:
                step_state.consecutive_failures = 1
            step_state.last_tool = tool
            step_state.last_result = result_str
            if step_state.consecutive_failures >= 3:
                corrective = (
                    f"\n\n[CORRECTIVE] The same tool ({tool}) failed {step_state.consecutive_failures} times "
                    f"in a row with the same error. STOP repeating it. Re-read state using "
                    f"get_workspace_info / list_files / read_file, then adjust your approach."
                )
                followup_text = tool_followup(tool, tool_input, result_str) + corrective
                if use_messages:
                    step_state.current_messages.append({"role": "user", "content": followup_text})
                else:
                    step_state.current_input += "\n\n" + followup_text
                step_state.consecutive_failures = 0
                return False
        else:
            step_state.consecutive_failures = 0
            step_state.last_tool = None
            step_state.last_result = None

        followup_text = tool_followup(tool, tool_input, result_str)
        if step >= 4 and tool not in _EDIT_TOOLS:
            followup_text += _deadline_corrective(step)
        if use_messages:
            step_state.current_messages.append({"role": "user", "content": followup_text})
        else:
            step_state.current_input += "\n\n" + followup_text

        return False

    return False
