"""Kernel context retrieval for agent turns."""

from __future__ import annotations

from agent_core.tools import log_output
from agent_core.tools.kernel_ops import (
    AUTO_RETRIEVE_CONTEXT,
    KERNEL_AVAILABLE,
    RETRIEVE_LIMIT,
    retrieval_engine,
)


def retrieve_kernel_context(
    query: str,
    *,
    limit: int | None = None,
    pattern_limit: int = 3,
    log: bool = False,
) -> str:
    """Return a markdown context block, or empty string if unavailable/disabled."""
    if not AUTO_RETRIEVE_CONTEXT or not KERNEL_AVAILABLE or not retrieval_engine:
        return ""

    retrieve_limit = limit if limit is not None else RETRIEVE_LIMIT
    try:
        results = retrieval_engine.search(query=query, limit=retrieve_limit)
        patterns = retrieval_engine.retrieve_patterns(limit=pattern_limit)
        if not results and not patterns:
            return ""

        context_parts = ["## Retrieved Context"]
        for r in results:
            context_parts.append(f"- {r.content.get('content', {})}")
        for p in patterns:
            context_parts.append(f"- Pattern: {p.content.get('title', 'unknown')}")

        if log:
            log_output(
                f"[Kernel] Retrieved {len(results)} memories, {len(patterns)} patterns"
            )
        return "\n" + "\n".join(context_parts)
    except Exception as e:
        log_output(f"[Kernel] Context retrieval warning: {e}")
        return ""
