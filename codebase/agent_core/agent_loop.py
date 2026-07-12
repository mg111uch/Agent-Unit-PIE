"""
Shared agent tool loop used by CLI and WebSocket server.

Yields event dicts so callers can log or stream without duplicating logic.
"""

from __future__ import annotations

import json
import time
import traceback
from typing import Any, Generator, Optional

from agent_core.config import MAX_AGENT_STEPS
from agent_core.context import retrieve_kernel_context
from agent_core.response_parse import parse_agent_reply
from agent_core.tools import TOOLS, log_output

# Chunk size for streaming final answers over WebSocket / UI
_STREAM_CHUNK_CHARS = 28


def _tool_followup(tool: str, tool_input: Any, tool_result: Any) -> str:
    return (
        f"Tool used: {tool}\n"
        f"Input: {tool_input}\n"
        f"Result: {tool_result}\n"
        f"Decide next step."
    )


def _serialize_tool_input(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    try:
        return json.dumps(tool_input, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(tool_input)


def _stream_final(
    content: str,
    step: int,
    conversation_id: Optional[str],
) -> Generator[dict[str, Any], None, None]:
    """Yield stream_chunk events then a final event (content already streamed)."""
    text = content or ""
    if text:
        for i in range(0, len(text), _STREAM_CHUNK_CHARS):
            yield {
                "type": "stream_chunk",
                "content": text[i : i + _STREAM_CHUNK_CHARS],
                "step": step,
            }
            # Tiny pause so the UI can paint progressive tokens
            time.sleep(0.012)
    yield {
        "type": "final",
        "content": "",
        "step": step,
        "conversation_id": conversation_id,
        # Full text for CLI / callers that only listen for final
        "full_content": text,
    }


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
) -> Generator[dict[str, Any], None, None]:
    """
    Run the multi-step agent loop, yielding events:

      {"type": "status", "status": "thinking"|"tool", "step": int}
      {"type": "step_reply", "content": str, "step": int}
      {"type": "tool_call", "tool": str, "input": str, "step": int}
      {"type": "tool_result", "tool": str, "result": str, "input": str, "step": int}
      {"type": "stream_chunk", "content": str, "step": int}
      {"type": "final", "content": str, "step": int, "conversation_id": str|None}
      {"type": "error", "message": str, "conversation_id": str|None}
    """
    context_info = ""
    if retrieve_context:
        context_info = retrieve_kernel_context(user_input, log=log_context)

    current_input = user_input + context_info
    conv_id = conversation_id

    # Repeated-failure tracking
    _last_tool: str | None = None
    _last_result: str | None = None
    _consecutive_failures = 0

    for step in range(max_steps):
        try:
            yield {
                "type": "status",
                "status": "thinking",
                "step": step,
                "conversation_id": conv_id,
            }

            result = orchestrator.generate(
                prompt=current_input,
                system_prompt=system_prompt,
                conversation_id=conv_id,
                provider=provider,
                model=model,
            )

            if result["status"] == "error":
                yield {
                    "type": "error",
                    "message": f"LLM call failed: {result.get('error')}",
                    "conversation_id": conv_id,
                }
                return

            conv_id = result.get("conversation_id")
            reply = result.get("response")
            if reply is None:
                reply = ""
            elif not isinstance(reply, str):
                reply = str(reply)
            yield {"type": "step_reply", "content": reply, "step": step}

            parsed = parse_agent_reply(reply, TOOLS)

            if parsed.kind == "raw":
                yield from _stream_final(
                    parsed.content or reply, step, conv_id
                )
                return

            if parsed.kind == "final":
                yield from _stream_final(parsed.content or "", step, conv_id)
                return

            if parsed.kind == "invalid_tool":
                yield {
                    "type": "error",
                    "message": f"Invalid or missing tool: {parsed.tool}",
                    "conversation_id": conv_id,
                }
                return

            tool = parsed.tool
            tool_input = parsed.tool_input
            input_str = _serialize_tool_input(tool_input)

            yield {
                "type": "tool_call",
                "tool": tool,
                "input": input_str,
                "step": step,
            }

            tool_result = TOOLS[tool](tool_input)
            result_str = str(tool_result)

            yield {
                "type": "tool_result",
                "tool": tool,
                "input": input_str,
                "result": result_str[:2000],
                "step": step,
            }

            # Repeated-failure breaker: if same tool + same result 3x, inject corrective note
            if result_str.startswith("Error"):
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
                    current_input += "\n\n" + _tool_followup(tool, tool_input, tool_result) + corrective
                    _consecutive_failures = 0
                    if step_delay > 0:
                        time.sleep(step_delay)
                    continue
            else:
                _consecutive_failures = 0
                _last_tool = None
                _last_result = None

            current_input += "\n\n" + _tool_followup(tool, tool_input, tool_result)
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

    yield from _stream_final(
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
    """
    Run one agent turn. Returns (final_or_error_text, conversation_id).

    on_event(event_dict) is called for each event if provided.
    """
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
