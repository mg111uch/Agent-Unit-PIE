"""Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket."""

from __future__ import annotations

import json
import threading
import time
import traceback
from typing import Any, Generator, List, Optional

from agent_core.config import MAX_AGENT_STEPS
from agent_core.context import retrieve_kernel_context
from agent_core.response_parse import parse_provider_response
from agent_core.tools import registry, ToolResult, log_output
from agent_core.loop.messages import (
    tool_followup,
    serialize_tool_input,
    build_tool_calls_msg,
    build_tool_results_msg,
    build_single_tool_result_msg,
    build_corrective_msg,
)
from agent_core.loop.streaming import stream_final
from agent_core.loop.executor import execute_tool_calls


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
        current_messages.append({
            "role": "user",
            "content": user_input + context_info,
        })
        current_input = ""
    else:
        current_input = user_input + context_info

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

            if use_messages:
                result = orchestrator.generate(
                    prompt="",
                    system_prompt=system_prompt,
                    provider=provider,
                    model=model,
                    tools=registry.get_schemas(),
                    messages=current_messages,
                )
            else:
                result = orchestrator.generate(
                    prompt=current_input,
                    system_prompt=system_prompt,
                    conversation_id=conv_id,
                    provider=provider,
                    model=model,
                    tools=registry.get_schemas(),
                )

            if result["status"] == "error":
                yield {
                    "type": "error",
                    "message": f"LLM call failed: {result.get('error')}",
                    "conversation_id": conv_id,
                }
                return

            conv_id = result.get("conversation_id")
            reply = result.get("response") or ""
            tool_calls_raw = result.get("tool_calls")

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
                    "step": step,
                }
                corrective_text = tool_followup("parse", "", corrective)
                if use_messages:
                    current_messages.append(build_corrective_msg(corrective))
                    current_messages.append({
                        "role": "user",
                        "content": corrective_text,
                    })
                    msg_store.add_message(
                        session_id=session_id, role="tool",
                        content=None,
                        tool_results=[{"tool": "parse", "result": corrective}],
                    )
                else:
                    current_input += "\n\n" + corrective_text
                if step_delay > 0:
                    time.sleep(step_delay)
                continue

            # --- final ---
            if parsed.kind == "final":
                if use_messages:
                    msg_store.add_message(
                        session_id=session_id, role="assistant",
                        content=parsed.content or "",
                    )
                _msgs = locals().get("current_messages") if use_messages else None
                yield from stream_final(
                    parsed.content or "", step, conv_id,
                    orchestrator=orchestrator,
                    provider=provider,
                    model=model,
                    system_prompt=system_prompt,
                    messages=_msgs,
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
                    "step": step,
                }
                followup_text = tool_followup(
                    parsed.tool or "unknown", "", corrective
                )
                if use_messages:
                    current_messages.append(build_corrective_msg(corrective))
                    current_messages.append({
                        "role": "user",
                        "content": followup_text,
                    })
                    msg_store.add_message(
                        session_id=session_id, role="tool",
                        content=None,
                        tool_results=[{"tool": parsed.tool or "unknown", "result": corrective}],
                    )
                else:
                    current_input += "\n\n" + followup_text
                if step_delay > 0:
                    time.sleep(step_delay)
                continue

            # --- multi tool_calls ---
            if parsed.kind == "tool_calls":
                if use_messages:
                    current_messages.append(build_tool_calls_msg(parsed.tool_calls))
                    msg_store.add_message(
                        session_id=session_id, role="assistant",
                        content=None,
                        tool_calls=[
                            {"name": tc.name, "arguments": tc.arguments}
                            for tc in parsed.tool_calls
                        ],
                    )

                results = execute_tool_calls(parsed.tool_calls, step, tools=_tools)
                all_ok = all(r.get("ok", True) for r in results)
                yield {
                    "type": "tool_result",
                    "tool": "multi",
                    "input": json.dumps([{"name": tc.name, "arguments": tc.arguments} for tc in parsed.tool_calls]),
                    "result": json.dumps(results, indent=2)[:2000],
                    "step": step,
                }

                if use_messages:
                    current_messages.append(build_tool_results_msg(results))
                    msg_store.add_message(
                        session_id=session_id, role="tool",
                        content=None,
                        tool_results=[
                            {"tool": r["tool"], "result": r["result"]}
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

                result_obj = _tools[tool](tool_input)
                if isinstance(result_obj, ToolResult):
                    result_str = result_obj.to_string()
                    is_error = not result_obj.ok
                else:
                    result_str = str(result_obj)
                    is_error = result_str.startswith("Error")

                yield {
                    "type": "tool_result",
                    "tool": tool,
                    "input": input_str,
                    "result": result_str[:2000],
                    "step": step,
                }

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

    yield from stream_final(
        "Max iterations reached", max_steps - 1, conv_id
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
