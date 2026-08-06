"""Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket."""

from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Generator, List, Optional

from agent_core.config import (
    COMPACTION_TRIGGER_CHARS,
    CONTEXT_DIGEST_ENABLED,
    TOOL_NUDGE_THRESHOLD,
    WORKFLOW_LEARN_CONTEXT_HINTS,
    GEMINI_CHAIN_RESTART_TOKENS,
    GEMINI_STATELESS,
    resolve_active_tool_names,
    resolve_active_tool_packs,
)
from agent_core.context import retrieve_kernel_context
from agent_core.response_parse import parse_provider_response
from agent_core.tools import registry, log_output
from agent_core.loop.session_state import (
    SessionState,
    set_session_state,
    reset_session_state,
    compact_messages,
)
from agent_core.loop._helpers import (
    _generate_with_cancel,
    _debug_dump,
)
from agent_core.loop.stepper import StepState, dispatch_step

_schema_dumped = False


def iter_agent_events(
    user_input: str,
    orchestrator: Any,
    *,
    conversation_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_steps: int = 100,
    step_delay: float = 0.0,
    retrieve_context: bool = True,
    log_context: bool = False,
    msg_store: Any = None,
    session_id: Optional[str] = None,
    cancel_event: Optional[threading.Event] = None,
    tools_override: Optional[dict] = None,
    tool_categories: Optional[List[str]] = None,
    session_state: Optional[SessionState] = None,
    local_planner: Any = None,
) -> Generator[dict[str, Any], None, None]:
    context_info = ""
    if retrieve_context:
        context_info = retrieve_kernel_context(user_input, log=log_context)

    state = session_state if session_state is not None else SessionState()
    state.begin_turn()
    _state_token = set_session_state(state)

    use_messages = msg_store is not None and session_id is not None

    # Digest + workflow hints are ephemeral per-turn context. They are computed
    # once, appended to the in-memory user message only, and never persisted to
    # msg_store (which would replay stale snapshots on every later turn).
    digest = ""
    if CONTEXT_DIGEST_ENABLED and state.turn_count > 0:
        # Only inject a digest that carries useful info; skip the pure header
        # so an empty snapshot isn't billed every turn.
        if state.workspace_root or state.file_cache or state.todo_plan or state.edits_log:
            digest = state.build_digest()

    session_hints = ""
    if WORKFLOW_LEARN_CONTEXT_HINTS:
        try:
            from agent_core.tools.chain.graph_evolver import graph_evolver
            session_hints = graph_evolver.workflow_hints()
        except Exception:
            pass  # hints must never break the turn

    # Stateless mode needs no server-side chain: every call already carries the
    # compacted client history, so the id is meaningless and would only linger.
    if GEMINI_STATELESS:
        conversation_id = None
    # Gemini stateful chains are billed against the full server-side context on
    # every call. Drop the chain once the accumulated estimate passes the
    # threshold: the next call rebuilds a fresh chain from the compacted client
    # history, bounding per-call cost (the new conversation_id propagates out).
    elif use_messages and state.should_restart_chain(GEMINI_CHAIN_RESTART_TOKENS):
        state.accumulated_tokens = 0
        conversation_id = None

    conv_id = conversation_id
    _interaction_id = conversation_id

    _tools = tools_override if tools_override is not None else registry.get_tools(categories=tool_categories)

    try:
        yield from _iter_agent_events_body(
            user_input=user_input,
            orchestrator=orchestrator,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            max_steps=max_steps,
            step_delay=step_delay,
            context_info=context_info,
            digest=digest,
            session_hints=session_hints,
            msg_store=msg_store,
            session_id=session_id,
            cancel_event=cancel_event,
            tool_categories=tool_categories,
            local_planner=local_planner,
            state=state,
            use_messages=use_messages,
            _tools=_tools,
            conv_id=conv_id,
            _interaction_id=_interaction_id,
        )
    finally:
        reset_session_state(_state_token)
        try:
            if msg_store is not None and session_id:
                from agent_core.config import WORKFLOW_LEARN_SESSION_END, WORKFLOW_LEARN_GRAPH_EVOLVE
                if WORKFLOW_LEARN_SESSION_END:
                    from agent_core.tools.chain.chain_miner import miner
                    miner.mine_session(session_id, msg_store)
                if WORKFLOW_LEARN_GRAPH_EVOLVE:
                    from agent_core.tools.chain.chain_store import chain_store
                    sequence = [tc.get("name") for msg in msg_store.get_messages(session_id, limit=10000)
                                for tc in (msg.get("tool_calls") or [])
                                if tc.get("name")]
                    if len(sequence) >= 2:
                        chain_store.upsert_sequence(session_id, sequence)
                    from agent_core.tools.chain.graph_evolver import graph_evolver
                    graph_evolver.sweep_stale_chains()
                    graph_evolver.evolve()
        except Exception:
            pass  # session-end mining must never break the turn


def _iter_agent_events_body(
    *,
    user_input: str,
    orchestrator: Any,
    conversation_id: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    system_prompt: Optional[str],
    max_steps: int,
    step_delay: float,
    context_info: str,
    digest: str,
    session_hints: str,
    msg_store: Any,
    session_id: Optional[str],
    cancel_event: Optional[threading.Event],
    tool_categories: Optional[List[str]],
    local_planner: Any,
    state: SessionState,
    use_messages: bool,
    _tools: dict,
    conv_id: Optional[str],
    _interaction_id: Optional[str],
) -> Generator[dict[str, Any], None, None]:
    if use_messages:
        current_messages = list(msg_store.get_messages(session_id))
        current_messages = compact_messages(
            current_messages, state, trigger_chars=COMPACTION_TRIGGER_CHARS
        )
        extra = "\n\n".join(p for p in (context_info, digest, session_hints) if p)
        full_input = user_input + (("\n\n" + extra) if extra else "")
        if not current_messages or not (
            current_messages[-1].get("role") == "user"
            and current_messages[-1].get("content") == full_input
        ):
            # full_input carries ephemeral per-turn context (digest/hints) and is
            # appended to the in-memory list ONLY — never persisted to msg_store.
            current_messages.append({
                "role": "user",
                "content": full_input,
            })
        current_input = ""
    else:
        extra = "\n\n".join(p for p in (context_info, digest, session_hints) if p)
        current_input = user_input + (("\n\n" + extra) if extra else "")
        current_messages = []

    step_state = StepState(
        current_messages=current_messages,
        current_input=current_input,
    )

    _cached_schemas = registry.get_schemas(
        provider_name=provider,
        categories=tool_categories,
        names=resolve_active_tool_names() or None,
    )
    _debug_dump("NEW TURN",
        provider=provider,
        model=model,
        system_prompt=system_prompt or "(none)",
        user_input=user_input,
        context_info=context_info or "(none)",
        session_digest=digest or "(none)",
        cache_hits=state.cache_hits,
        cache_misses=state.cache_misses,
        messages=current_messages if use_messages else [],
        plain_prompt=current_input if not use_messages else "",
    )

    step = 0
    while True:
        if cancel_event and cancel_event.is_set():
            yield {
                "type": "final",
                "content": "",
                "step": step,
                "conversation_id": conv_id,
                "full_content": "(cancelled)",
            }
            return

        step += 1
        if step > max_steps:
            yield {
                "type": "final", "content": "", "step": step,
                "conversation_id": conv_id,
                "full_content": "(max steps reached)",
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
            _local_step = False
            if local_planner and local_planner.should_route_local(
                step, step_state.tool_call_history,
                step_state.current_input if not use_messages else "",
            ):
                _local_result = local_planner.generate_local(
                    messages=step_state.current_messages if use_messages else None,
                    system_prompt=system_prompt,
                    cancel_event=cancel_event,
                )
                if _local_result and not _local_result.get("error"):
                    result = _local_result
                    _local_step = True
                else:
                    result = None
            if not _local_step:
                global _schema_dumped
                if not _schema_dumped:
                    _schema_dumped = True
                    _debug_dump("TOOL SCHEMAS", schemas=_cached_schemas)
                gen_kwargs = dict(
                    orchestrator=orchestrator, cancel_event=cancel_event,
                    system_prompt=system_prompt, provider=provider, model=model,
                    conversation_id=_interaction_id, tools=_cached_schemas,
                )
                if use_messages:
                    gen_kwargs["prompt"] = ""
                    gen_kwargs["messages"] = step_state.current_messages
                else:
                    gen_kwargs["prompt"] = step_state.current_input
                result = _generate_with_cancel(**gen_kwargs)
            if result is None:
                yield {
                    "type": "final",
                    "content": "",
                    "step": step,
                    "conversation_id": conv_id,
                    "full_content": "(cancelled)",
                }
                return
            yield {"type": "llm_call", "status": "end", "step": step, "usage": result.get("usage", {}), "latency_seconds": result.get("latency_seconds"), "retries": result.get("retries", 0)}

            state.note_usage(result.get("usage", {}))

            _debug_dump("LLM USAGE",
                step=step,
                total_tokens=result.get("usage", {}).get("total_tokens"),
                latency_seconds=result.get("latency_seconds"),
                retries=result.get("retries", 0),
            )

            _debug_dump("LLM RESPONSE",
                step=step,
                user_message_sent=step_state.current_input if not use_messages else "(see messages)",
                messages_sent=step_state.current_messages if use_messages else [],
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

            _interaction_id = result.get("conversation_id") or _interaction_id
            reply = result.get("response") or ""
            tool_calls_raw = result.get("tool_calls")
            if tool_calls_raw is None:
                raw = result.get("raw_response") or {}
                if isinstance(raw, dict):
                    tool_calls_raw = raw.get("tool_calls")

            parsed = parse_provider_response(reply, tool_calls_raw, _tools)

            step_usage = result.get("usage", {})
            should_exit = yield from dispatch_step(
                parsed, step_state,
                step=step,
                step_delay=step_delay,
                msg_store=msg_store,
                session_id=session_id,
                cancel_event=cancel_event,
                tools=_tools,
                local_planner=local_planner,
                state=state,
                use_messages=use_messages,
                conv_id=_interaction_id,
                local_step=_local_step,
                reply=reply,
                nudge_threshold=TOOL_NUDGE_THRESHOLD,
                step_usage=step_usage,
            )
            if should_exit:
                return
            if step_delay > 0:
                time.sleep(step_delay)

        except Exception as e:
            yield {
                "type": "error",
                "message": (
                    f"Exception in step {step}: {str(e)}\n{traceback.format_exc()}"
                ),
                "conversation_id": _interaction_id,
            }
            return

def run_agent_turn(
    user_input: str,
    orchestrator: Any,
    *,
    conversation_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_steps: int = 100,
    step_delay: float = 0.0,
    retrieve_context: bool = True,
    log_context: bool = False,
    on_event: Optional[Any] = None,
    tool_categories: Optional[List[str]] = None,
) -> tuple[str, Optional[str]]:
    final_text = ""
    conv_id = conversation_id
    if tool_categories is None:
        tool_categories = resolve_active_tool_packs()

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
        tool_categories=tool_categories,
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
