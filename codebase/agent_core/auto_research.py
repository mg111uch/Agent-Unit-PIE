"""Autonomous research mode: Goal -> Plan -> Execute -> Learn -> Repeat."""

from __future__ import annotations

from typing import Any, Optional

from agent_core.tools import (
    TOOLS,
    extract_json,
    log_output,
)
from agent_core.tools.kernel_ops import (
    KERNEL_AVAILABLE,
    retrieval_engine,
)
from agent_core.response_parse import strip_code_fences

try:
    from kernel.memory.working_memory import working_memory
except ImportError:
    working_memory = None

import json

AUTO_RESEARCH_SYSTEM_PROMPT = """You are an autonomous research agent.
Given a research goal, break it into executable subtasks.
For each subtask, respond with JSON: {"action": "tool_name", "input": {...}}
After getting results, decide next subtask or finish.
When goal is achieved, respond with: {"final": "summary of findings"}"""


def run_auto_research(
    goal: str,
    orchestrator: Any,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_iterations: int = 5,
) -> str:
    log_output(f"[Auto-Research] Goal: {goal}")

    if not KERNEL_AVAILABLE or not retrieval_engine:
        return "Error: Kernel not available. Enable kernel for auto-research."

    all_findings: list[str] = []
    current_goal = goal

    for iteration in range(max_iterations):
        log_output(f"[Auto-Research] Iteration {iteration + 1}/{max_iterations}")

        context_info = ""
        try:
            results = retrieval_engine.search(query=current_goal, limit=3)
            if results:
                context_parts = ["## Relevant Context"]
                for r in results[:3]:
                    context_parts.append(f"- {r.content.get('content', str(r))}")
                context_info = "\n" + "\n".join(context_parts)
        except Exception:
            pass

        first_input = (
            f"Goal: {current_goal}\n"
            f"Previous findings: {all_findings}\n"
            f"{context_info}\n"
            f"What subtask next?"
        )

        try:
            result = orchestrator.generate(
                prompt=first_input,
                system_prompt=AUTO_RESEARCH_SYSTEM_PROMPT,
                provider=provider,
                model=model,
            )
            if result["status"] == "error":
                return f"Error in LLM call: {result.get('error')}"
            clean_reply = strip_code_fences(result["response"])
        except Exception as e:
            return f"Error in LLM call: {e}"

        if '"final"' in clean_reply.lower() or "final" in clean_reply.lower():
            try:
                json_str = extract_json(clean_reply)
                data = json.loads(json_str) if json_str else {}
                if "final" in data:
                    all_findings.append(data["final"])
                    break
            except Exception:
                pass
            all_findings.append(clean_reply)
            break

        try:
            json_str = extract_json(clean_reply)
            if not json_str:
                all_findings.append(clean_reply)
                continue
            data = json.loads(json_str)
        except Exception:
            all_findings.append(clean_reply)
            continue

        tool = data.get("action")
        tool_input = data.get("input", "")

        if not tool or tool not in TOOLS:
            all_findings.append(f"Unknown tool: {tool}")
            continue

        try:
            tool_result = TOOLS[tool](tool_input)
            result_str = str(tool_result)[:500]
            all_findings.append(f"[{tool}] {result_str}")
            log_output(f"[Auto] Tool {tool} result: {result_str[:100]}...")
            current_goal = (
                f"Continue research. Last result: {result_str[:200]}. What next?"
            )
        except Exception as e:
            all_findings.append(f"Tool error: {e}")

    findings_summary = "\n\n".join(all_findings)

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

    return findings_summary or "No findings produced"
