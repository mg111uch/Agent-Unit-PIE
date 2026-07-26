"""Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket."""

from __future__ import annotations

import json
import os
import threading
import time
import traceback
from typing import Any, Generator, List, Optional

from agent_core.config import MAX_AGENT_STEPS, CODEBASE_ROOT, DEBUG_DUMP_ENABLED
from agent_core.context import retrieve_kernel_context
from agent_core.response_parse import parse_provider_response
from agent_core.tools import registry, ToolResult, log_output
from agent_core.loop.messages import (
    tool_followup,
    serialize_tool_input,
    build_tool_calls_msg,
    build_tool_results_msg,
    build_single_tool_result_msg,
)
from agent_core.loop.streaming import stream_final
from agent_core.loop.executor import execute_tool_calls
from agent_core.loop._helpers import (
    _truncate_result,
    _compact_corrective_exchange,
    _run_interactive_tool,
    _handle_corrective_bookkeeping,
    _generate_with_cancel,
    _QUESTION_TOOLS,
)

_DEBUG_LOG = os.path.join(CODEBASE_ROOT, "tui_output.txt")


def _debug_dump(mode: str, **kwargs):
    if not DEBUG_DUMP_ENABLED:
        return
    try:
        file_mode = "w" if mode == "NEW TURN" else "a"
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


def iter_agent_events(
    user_input: str,
    orchestrator: Any,
    *,
    conversation_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_steps: int = MAX_AGENT_STEPS,
    step_delay: float = 0.0,
    retrieve_context: bool = True,
    log_context: bool = False,
    msg_store: Any = None,
    session_id: Optional[str] = None,
    cancel_event: Optional[threading.Event] = None,
    tools_override: Optional[dict] = None,
    tool_categories: Optional[List[str]] = None,
) -> Generator[dict[str, Any], None, None]:
    context_info = ""
    if retrieve_context:
        context_info = retrieve_kernel_context(user_input, log=log_context)

    conv_id = conversation_id
    _last_tool: str | None = None
    _last_result: str | None = None
    _consecutive_failures = 0

    _tools = tools_override if tools_override is not None else registry.tools_dict
    use_messages = msg_store is not None and session_id is not None

    if use_messages:
        current_messages = list(msg_store.get_messages(session_id))
        full_input = user_input + context_info
        if not current_messages or not (
            current_messages[-1].get("role") == "user"
            and current_messages[-1].get("content") == full_input
        ):
            current_messages.append({
                "role": "user",
                "content": full_input,
            })
        current_input = ""
    else:
        current_input = user_input + context_info

    _debug_dump("NEW TURN",
        provider=provider,
        model=model,
        system_prompt=system_prompt or "(none)",
        user_input=user_input,
        context_info=context_info or "(none)",
        messages=current_messages if use_messages else [],
        plain_prompt=current_input if not use_messages else "",
    )

    for step in range(max_steps):
        if cancel_event and cancel_event.is_set():
            yield {
                "type": "final",
                "content": "",
                "step": step,
                "conversation_id": conv_id,
                "full_content": "(cancelled)",
            }
            return

        try:
            yield {
                "type": "status",
                "status": "thinking",
                "step": step,
                "conversation_id": conv_id,
            }

            yield {"type": "llm_call", "status": "start", "step": step}
            if use_messages:
                result = _generate_with_cancel(
                    orchestrator,
                    cancel_event,
                    prompt="",
                    system_prompt=system_prompt,
                    provider=provider,
                    model=model,
                    conversation_id=conv_id,
                    tools=registry.get_schemas(provider_name=provider, categories=tool_categories),
                    messages=current_messages,
                )
            else:
                result = _generate_with_cancel(
                    orchestrator,
                    cancel_event,
                    prompt=current_input,
                    system_prompt=system_prompt,
                    conversation_id=conv_id,
                    provider=provider,
                    model=model,
                    tools=registry.get_schemas(provider_name=provider, categories=tool_categories),
                )
            if result is None:
                yield {
                    "type": "final",
                    "content": "",
                    "step": step,
                    "conversation_id": conv_id,
                    "full_content": "(cancelled)",
                }
                return
            yield {"type": "llm_call", "status": "end", "step": step}

            _debug_dump("LLM RESPONSE",
                step=step,
                user_message_sent=current_input if not use_messages else "(see messages)",
                messages_sent=current_messages if use_messages else [],
                raw_response_text=result.get("response", ""),
                tool_calls_raw=result.get("tool_calls"),
                full_result=result,
            )

            if result["status"] == "error":
                _debug_dump("LLM ERROR",
                    step=step,
                    error=result.get("error", "unknown"),
                )
                yield {
                    "type": "error",
                    "message": f"LLM call failed: {result.get('error')}",
                    "conversation_id": conv_id,
                }
                return

            conv_id = result.get("conversation_id")
            reply = result.get("response") or ""
            tool_calls_raw = result.get("tool_calls")
            if tool_calls_raw is None:
                raw = result.get("raw_response") or {}
                if isinstance(raw, dict):
                    tool_calls_raw = raw.get("tool_calls")

            parsed = parse_provider_response(reply, tool_calls_raw, _tools)

            # --- raw (parse failure) ---
            if parsed.kind == "raw":
                corrective = (
                    f"Your response must be valid JSON only with "
                    f"'action'/'input' or 'final'. No free text or markdown. "
                    f"Valid tools: {', '.join(sorted(_tools.keys()))}."
                )
                yield {
                    "type": "tool_result",
                    "tool": "parse",
                    "input": "",
                    "result": corrective,
                    "ok": False,
                    "step": step,
                }
                corrective_text = tool_followup("parse", "", corrective)
                current_input = _handle_corrective_bookkeeping(
                    use_messages, current_messages, current_input, msg_store, session_id,
                    "parse", corrective, corrective_text,
                )
                if step_delay > 0:
                    time.sleep(step_delay)
                continue

            # --- final ---
            if parsed.kind == "final":
                _debug_dump("FINAL",
                    step=step,
                    response=parsed.content or "",
                )
                if use_messages:
                    msg_store.add_message(
                        session_id=session_id, role="assistant",
                        content=parsed.content or "",
                    )
                yield from stream_final(
                    parsed.content or "",
                    step=step,
                    conversation_id=conv_id,
                    cancel_event=cancel_event,
                )
                return

            # --- invalid_tool ---
            if parsed.kind == "invalid_tool":
                valid_tools = ", ".join(sorted(_tools.keys()))
                corrective = (
                    f"Unknown tool: '{parsed.tool}'. "
                    f"Valid tools are: {valid_tools}. "
                    f"Respond with a valid tool."
                )
                yield {
                    "type": "tool_result",
                    "tool": parsed.tool or "unknown",
                    "input": "",
                    "result": corrective,
                    "ok": False,
                    "step": step,
                }
                followup_text = tool_followup(
                    parsed.tool or "unknown", "", corrective
                )
                current_input = _handle_corrective_bookkeeping(
                    use_messages, current_messages, current_input, msg_store, session_id,
                    parsed.tool or "unknown", corrective, followup_text,
                )
                if step_delay > 0:
                    time.sleep(step_delay)
                continue

            # --- multi tool_calls ---
            if parsed.kind == "tool_calls":
                if use_messages:
                    _compact_corrective_exchange(current_messages)
                    current_messages.append(build_tool_calls_msg(parsed.tool_calls))
                    msg_store.add_message(
                        session_id=session_id, role="assistant",
                        content=None,
                        tool_calls=[
                            {
                                "name": tc.name,
                                "arguments": tc.arguments,
                                "id": tc.call_id or "",
                                "_call_id": tc.call_id or "",
                            }
                            for tc in parsed.tool_calls
                        ],
                    )

                for tc in parsed.tool_calls:
                    input_str = serialize_tool_input(tc.arguments)
                    yield {
                        "type": "tool_call",
                        "tool": tc.name,
                        "input": input_str,
                        "call_id": tc.call_id or "",
                        "step": step,
                    }

                question_calls = [tc for tc in parsed.tool_calls if tc.name in _QUESTION_TOOLS]
                other_calls = [tc for tc in parsed.tool_calls if tc.name not in _QUESTION_TOOLS]

                if question_calls:
                    if other_calls or len(question_calls) > 1:
                        name = question_calls[0].name
                        results = [{
                            "tool": name,
                            "result": f"Error: {name} cannot be combined with other tools in the same turn.",
                            "ok": False,
                            "call_id": question_calls[0].call_id or "",
                        }]
                    else:
                        tc = question_calls[0]
                        arg = tc.arguments if isinstance(tc.arguments, dict) else {}
                        result_obj, questions = _run_interactive_tool(tc.name, arg, _tools, session_id)
                        if questions:
                            yield {
                                "type": "question",
                                "questions": questions,
                                "session_id": session_id,
                                "step": step,
                            }
                        if isinstance(result_obj, ToolResult):
                            result_str = result_obj.to_string()
                            is_ok = result_obj.ok
                        else:
                            result_str = str(result_obj)
                            is_ok = not result_str.startswith("Error")
                        results = [{
                            "tool": tc.name,
                            "result": result_str,
                            "ok": is_ok,
                            "call_id": tc.call_id or "",
                        }]
                else:
                    results = execute_tool_calls(parsed.tool_calls, step, tools=_tools, cancel_event=cancel_event)

                if cancel_event and cancel_event.is_set():
                    yield {
                        "type": "final",
                        "content": "",
                        "step": step,
                        "conversation_id": conv_id,
                        "full_content": "(cancelled)",
                    }
                    return

                all_ok = all(r.get("ok", True) for r in results)

                for tc, result in zip(parsed.tool_calls, results):
                    input_str = serialize_tool_input(tc.arguments)
                    yield {
                        "type": "tool_result",
                        "tool": result["tool"],
                        "input": input_str,
                        "result": _truncate_result(result.get("result", ""), 2000),
                        "ok": result.get("ok", True),
                        "call_id": result.get("call_id", tc.call_id or ""),
                        "step": step,
                    }

                _debug_dump("TOOL RESULTS (multi)",
                    step=step,
                    calls=[{"name": tc.name, "args": tc.arguments, "call_id": tc.call_id} for tc in parsed.tool_calls],
                    results=results,
                )

                if use_messages:
                    current_messages.append(build_tool_results_msg(results))
                    msg_store.add_message(
                        session_id=session_id, role="tool",
                        content=None,
                        tool_results=[
                            {
                                "tool": r["tool"],
                                "result": r["result"],
                                "id": r.get("call_id", ""),
                                "_call_id": r.get("call_id", ""),
                                "tool_call_id": r.get("call_id", ""),
                            }
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
                            current_messages.append({
                                "role": "user",
                                "content": corrective,
                            })
                        else:
                            current_input += corrective

                if step_delay > 0:
                    time.sleep(step_delay)
                continue

            # --- single tool ---
            if parsed.kind == "tool":
                yield {
                    "type": "step_reply",
                    "content": reply,
                    "step": step,
                }
                tool = parsed.tool
                tool_input = parsed.tool_input
                input_str = serialize_tool_input(tool_input)

                yield {
                    "type": "tool_call",
                    "tool": tool,
                    "input": input_str,
                    "step": step,
                }

                if tool in _QUESTION_TOOLS:
                    tool_arg = tool_input if isinstance(tool_input, dict) else {}
                    if isinstance(tool_input, str):
                        try:
                            tool_arg = json.loads(tool_input)
                        except json.JSONDecodeError:
                            tool_arg = {"input": tool_input}
                    if tool == "debate_step" and not isinstance(tool_arg, dict):
                        tool_arg = {"topic": str(tool_input)}
                    result_obj, questions = _run_interactive_tool(tool, tool_arg, _tools, session_id)
                    if questions:
                        yield {
                            "type": "question",
                            "questions": questions,
                            "session_id": session_id,
                            "step": step,
                        }
                else:
                    result_obj = _tools[tool](tool_input)
                if cancel_event and cancel_event.is_set():
                    yield {
                        "type": "final",
                        "content": "",
                        "step": step,
                        "conversation_id": conv_id,
                        "full_content": "(cancelled)",
                    }
                    return
                if isinstance(result_obj, ToolResult):
                    result_str = result_obj.to_string()
                    is_error = not result_obj.ok
                    ok = result_obj.ok
                else:
                    result_str = str(result_obj)
                    is_error = result_str.startswith("Error")
                    ok = not is_error

                yield {
                    "type": "tool_result",
                    "tool": tool,
                    "input": input_str,
                    "result": _truncate_result(result_str, 2000),
                    "ok": ok,
                    "step": step,
                }

                _debug_dump("TOOL RESULT (single)",
                    step=step,
                    tool=tool,
                    input=parsed.tool_input,
                    result=result_str,
                    ok=ok,
                )

                if use_messages:
                    current_messages.append({
                        "role": "assistant",
                        "content": reply,
                        "tool_calls": [{"name": tool, "arguments": tool_input if isinstance(tool_input, dict) else {"input": tool_input}}],
                    })
                    msg_store.add_message(
                        session_id=session_id, role="assistant",
                        content=reply,
                        tool_calls=[{"name": tool, "arguments": tool_input if isinstance(tool_input, dict) else {"input": tool_input}}],
                    )
                    current_messages.append(build_single_tool_result_msg(tool, result_str))
                    msg_store.add_message(
                        session_id=session_id, role="tool",
                        content=None,
                        tool_results=[{"tool": tool, "result": result_str}],
                    )

                if is_error:
                    if tool == _last_tool and result_str == _last_result:
                        _consecutive_failures += 1
                    else:
                        _consecutive_failures = 1
                    _last_tool = tool
                    _last_result = result_str
                    if _consecutive_failures >= 3:
                        corrective = (
                            f"\n\n[CORRECTIVE] The same tool ({tool}) failed {_consecutive_failures} times "
                            f"in a row with the same error. STOP repeating it. Re-read state using "
                            f"get_workspace_info / list_files / read_file, then adjust your approach."
                        )
                        followup_text = tool_followup(tool, tool_input, result_str) + corrective
                        if use_messages:
                            current_messages.append({
                                "role": "user",
                                "content": followup_text,
                            })
                        else:
                            current_input += "\n\n" + followup_text
                        _consecutive_failures = 0
                        if step_delay > 0:
                            time.sleep(step_delay)
                        continue
                else:
                    _consecutive_failures = 0
                    _last_tool = None
                    _last_result = None

                followup_text = tool_followup(tool, tool_input, result_str)
                if use_messages:
                    current_messages.append({
                        "role": "user",
                        "content": followup_text,
                    })
                else:
                    current_input += "\n\n" + followup_text
                if step_delay > 0:
                    time.sleep(step_delay)

        except Exception as e:
            yield {
                "type": "error",
                "message": (
                    f"Exception in step {step}: {str(e)}\n{traceback.format_exc()}"
                ),
                "conversation_id": conv_id,
            }
            return

    _debug_dump("MAX STEPS REACHED", step=max_steps, message="Max iterations reached")
    yield from stream_final(
        "Max iterations reached", max_steps - 1, conv_id,
    )


def run_agent_turn(
    user_input: str,
    orchestrator: Any,
    *,
    conversation_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_steps: int = MAX_AGENT_STEPS,
    step_delay: float = 0.0,
    retrieve_context: bool = True,
    log_context: bool = False,
    on_event: Optional[Any] = None,
) -> tuple[str, Optional[str]]:
    final_text = "Max iterations reached"
    conv_id = conversation_id

    for event in iter_agent_events(
        user_input,
        orchestrator,
        conversation_id=conversation_id,
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        max_steps=max_steps,
        step_delay=step_delay,
        retrieve_context=retrieve_context,
        log_context=log_context,
    ):
        if on_event:
            on_event(event)
        if event.get("conversation_id") is not None or "conversation_id" in event:
            conv_id = event.get("conversation_id", conv_id)
        if event["type"] == "step_reply":
            log_output(f"\n[Agent Step {event['step']}]: {event['content']}")
        elif event["type"] == "stream_chunk":
            pass
        elif event["type"] == "final":
            final_text = event.get("full_content") or event.get("content") or final_text
            conv_id = event.get("conversation_id", conv_id)
            return final_text, conv_id
        elif event["type"] == "error":
            msg = event["message"]
            log_output(f"[ERROR] {msg}")
            return msg, event.get("conversation_id", conv_id)

    return final_text, conv_id
