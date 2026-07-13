"""Autonomous research mode using the shared agent loop.

Delegates to iter_agent_events for consistent parsing, failure recovery,
and streaming. No longer reimplements the tool-calling mini-loop.
"""

from __future__ import annotations

from typing import Any, Optional

from agent_core.agent_loop import run_agent_turn
from agent_core.tools import log_output
from agent_core.tools.kernel_ops import KERNEL_AVAILABLE

try:
    from kernel.memory.working_memory import working_memory
except ImportError:
    working_memory = None

AUTO_RESEARCH_SYSTEM_PROMPT = """You are an autonomous research agent operating on a real project workspace.
Your goal is to research a question thoroughly using available tools.

## WORKFLOW
1. First, use `kernel_retrieve` to find existing context on the topic.
2. Use `read_file` / `list_files` / `execute_command` to gather information.
3. Use `kernel_store_context` to store important findings.
4. When the goal is fully researched, respond with: {"final": "summary of findings"}

## RULES
- Respond with valid JSON only: {"action": "tool_name", "input": ...} or {"final": "..."}
- Prefer native tool usage. Call tools to gather data.
- Keep findings concise and structured.
- When finished, provide a complete summary of all findings.
- If kernel is unavailable, proceed with file/shell tools only — do not error out."""  # noqa: E501


def run_auto_research(
    goal: str,
    orchestrator: Any,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_iterations: int = 5,
) -> str:
    log_output(f"[Auto-Research] Goal: {goal}")

    all_findings: list[str] = []
    remaining_steps = max_iterations
    conv_id: Optional[str] = None

    for iteration in range(max_iterations):
        log_output(f"[Auto-Research] Iteration {iteration + 1}/{max_iterations}")

        research_prompt = (
            f"Research goal: {goal}\n"
            f"Findings so far: {all_findings if all_findings else '(none yet)'}\n"
            f"Remaining steps: {remaining_steps}\n"
            f"What subtask next?"
        )

        final_text, conv_id = run_agent_turn(
            research_prompt,
            orchestrator,
            conversation_id=conv_id,
            provider=provider,
            model=model,
            system_prompt=AUTO_RESEARCH_SYSTEM_PROMPT,
            max_steps=remaining_steps,
        )

        if final_text and final_text != "Max iterations reached":
            all_findings.append(final_text)
            break

        if conv_id:
            remaining_steps -= 1

    findings_summary = "\n\n".join(all_findings) if all_findings else "No findings produced"

    if KERNEL_AVAILABLE and working_memory and all_findings:
        try:
            working_memory.add_memory(
                memory_type="research",
                content=findings_summary,
                importance=0.7,
                confidence=0.8,
                tags=["auto-research", goal[:30]],
                ttl_seconds=86400,
            )
            log_output("[Kernel] Research findings stored")
        except Exception as e:
            log_output(f"[Kernel] Storage warning: {e}")

    return findings_summary
