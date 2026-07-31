from __future__ import annotations

from typing import Any

from agent_core.tools.types import ToolResult


def subagent_task(params: dict) -> ToolResult:
    """Run a sub-agent to perform an open-ended research or exploration task.

    Delegates the task to a separate agent loop so the main agent's context
    is not polluted by large exploration results. The sub-agent has access
    to the full tool set and returns its final answer.

    Use this when:
    - The task requires exploring unfamiliar parts of the codebase
    - Multiple rounds of search/read/grep are needed
    - The exploration would consume significant context tokens
    """
    task = params.get("task", "")
    if not task:
        return ToolResult(ok=False, error_type="tool", message="'task' field is required")

    provider = params.get("provider") or None
    model = params.get("model") or None
    max_steps = params.get("max_steps", 15)

    from agent_core.server import orchestrator
    from agent_core.loop import iter_agent_events
    from agent_core.tools import registry

    events = list(iter_agent_events(
        task,
        orchestrator,
        provider=provider,
        model=model,
        max_steps=max_steps,
        retrieve_context=False,
        tools_override=registry.tools_dict,
    ))

    result_parts = []
    for e in events:
        if e["type"] == "final":
            content = e.get("full_content") or e.get("content", "")
            if content:
                result_parts.append(content)
        elif e["type"] == "error":
            return ToolResult(ok=False, error_type="tool", message=f"Sub-agent error: {e['message']}")

    if not result_parts:
        return ToolResult(ok=False, error_type="tool", message="Sub-agent returned no result")

    return ToolResult(ok=True, data="\n".join(result_parts))
