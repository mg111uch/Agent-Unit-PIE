"""Context manager (PlanFixes2 Phase 6).

Centralizes every context-fragment the agent loop needs for a turn:
session state (digest + workflow hints), compaction, and the assembled
model-visible user input. The engine delegates to this module instead of
manually joining fragments; estimation/token math stays in context_budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from agent_core.config import (
    CONTEXT_DIGEST_ENABLED,
    WORKFLOW_LEARN_CONTEXT_HINTS,
    HISTORY_RELEVANCE_ENABLED,
    HISTORY_RELEVANCE_KEEP_RECENT,
    HISTORY_RELEVANCE_MIN_OVERLAP,
)
from agent_core.context_budget import ContextBudget, build_budget, estimate_tokens
from agent_core.loop.session_state import SessionState, compact_messages, filter_irrelevant_history


__all__ = [
    "ContextSession",
    "estimate_tokens",
    "estimate_request",
    "compact",
    "build_session_state",
    "build_active_context",
]


@dataclass
class ContextSession:
    """Per-turn ephemeral context fragments (never persisted)."""

    context_info: str = ""
    digest: str = ""
    session_hints: str = ""

    @property
    def extra_text(self) -> str:
        return "\n\n".join(p for p in (self.context_info, self.digest, self.session_hints) if p)


def estimate_request(
    *,
    system_prompt: Optional[str] = None,
    prompt: str = "",
    tools: Optional[list] = None,
    messages: Optional[list] = None,
    digest: str = "",
) -> ContextBudget:
    """Estimate the model-visible token budget for a request before calling."""
    return build_budget(
        system_prompt=system_prompt, prompt=prompt, tools=tools, messages=messages, digest=digest
    )


def compact(
    messages: list[dict],
    state: Optional[SessionState] = None,
    trigger_tokens: Optional[int] = None,
) -> list[dict]:
    """Token-aware compaction (Phase 7). Default budget = reserved effective
    input budget from config (output + reasoning + tool-result headroom)."""
    return compact_messages(messages, state, trigger_tokens=trigger_tokens)


def build_session_state(
    state: SessionState,
    *,
    context_info: str = "",
) -> ContextSession:
    """Assemble the turn's ephemeral context fragments:
    retrieved kernel context, session digest, and workflow hints."""
    digest = ""
    if CONTEXT_DIGEST_ENABLED and state.turn_count > 0:
        if state.workspace_root or state.file_cache or state.todo_plan or state.edits_log:
            digest = state.build_digest()

    session_hints = ""
    if WORKFLOW_LEARN_CONTEXT_HINTS:
        try:
            from agent_core.tools.chain.graph_evolver import graph_evolver
            session_hints = graph_evolver.workflow_hints()
        except Exception:
            pass  # hints must never break the turn

    return ContextSession(
        context_info=context_info,
        digest=digest,
        session_hints=session_hints,
    )


def build_active_context(
    state: SessionState,
    *,
    user_input: str,
    session: ContextSession,
    msg_store: Any = None,
    session_id: Optional[str] = None,
    use_messages: bool = False,
) -> tuple[list[dict], str]:
    """Return (current_messages, current_input) ready for the provider.

    messages-mode: compacts stored history and appends the full ephemeral
    input as the trailing user message (in-memory only).
    prompt-mode: returns the plain prompt with ephemeral fragments appended.
    """
    extra = session.extra_text
    if use_messages:
        current_messages = list(msg_store.get_messages(session_id)) if msg_store else []
        if HISTORY_RELEVANCE_ENABLED:
            current_messages, dropped = filter_irrelevant_history(
                current_messages,
                user_input,
                keep_recent=HISTORY_RELEVANCE_KEEP_RECENT,
                min_overlap=HISTORY_RELEVANCE_MIN_OVERLAP,
            )
            if dropped > 0:
                user_input = (
                    user_input
                    + f"\n(Note: {dropped} unrelated earlier turn(s) were omitted to save context.)"
                )
        current_messages = compact(current_messages, state)
        full_input = user_input + (("\n\n" + extra) if extra else "")
        if not current_messages or not (
            current_messages[-1].get("role") == "user"
            and current_messages[-1].get("content") == full_input
        ):
            current_messages.append({"role": "user", "content": full_input})
        return current_messages, ""
    return [], user_input + (("\n\n" + extra) if extra else "")