"""Per-request context-budget profiler (Agent 0 — instrumentation).

Estimates the model-visible request size before a provider call so every
token in a benchmark can be explained: system, tool schemas, history,
tool results, user input, digest, cached/fresh split.

Estimation only — never mutates the conversation. Token math uses the real
tiktoken encoder (via tokenizer.count_tokens, Phase 7) with a chars/4
fallback, so profiler and compaction agree on the unit models bill.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Any, List, Optional

from agent_core.tokenizer import count_tokens

CHARS_PER_TOKEN = 4.0


def estimate_tokens(value: Any) -> int:
    """Approximate token count for a string / list / dict / scalar."""
    if value is None:
        return 0
    if isinstance(value, (list, dict)):
        try:
            value = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
        except (TypeError, ValueError):
            value = str(value)
    return count_tokens(value)


@dataclass
class ContextBudget:
    """Estimated token breakdown of one LLM request."""

    system_tokens: int = 0
    tool_schema_tokens: int = 0
    history_tokens: int = 0
    tool_result_tokens: int = 0
    user_tokens: int = 0
    digest_tokens: int = 0
    cached_input_tokens: int = 0
    fresh_input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    billable_tokens: int = 0

    # Optional real usage from the provider (when available).
    provider_source: str = ""

    def estimate_total(self) -> int:
        return (
            self.system_tokens
            + self.tool_schema_tokens
            + self.history_tokens
            + self.tool_result_tokens
            + self.user_tokens
            + self.digest_tokens
        )

    def apply_usage(self, usage: dict) -> "ContextBudget":
        """Overlay real provider usage if present (prompt/completion/cached)."""
        if not usage:
            return self
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        completion = int(usage.get("completion_tokens", 0) or 0)
        cached = int(usage.get("cached_tokens", 0) or 0)
        self.output_tokens = completion
        if prompt or completion:
            self.cached_input_tokens = cached
            self.fresh_input_tokens = max(0, prompt - cached)
            self.total_tokens = self.estimate_total()
            self.billable_tokens = self.fresh_input_tokens + completion
            self.provider_source = "measured"
        return self

    def to_dict(self) -> dict:
        return asdict(self)


def _split_messages(messages: List[dict]) -> dict:
    """Bucket message content: history vs tool results vs user vs digest."""
    out = {"history": 0, "tool_result": 0, "user": 0}
    last_user_idx = None
    for i, m in enumerate(messages):
        if m.get("role") == "user" and m.get("content"):
            last_user_idx = i
    for i, m in enumerate(messages):
        role = m.get("role")
        content = m.get("content")
        if role == "user":
            bucket = "user" if i == last_user_idx else "history"
            if isinstance(content, str) and content:
                out[bucket] += estimate_tokens(content)
        elif role == "assistant":
            if isinstance(content, str) and content:
                out["history"] += estimate_tokens(content)
            for tc in m.get("tool_calls") or []:
                out["history"] += estimate_tokens(tc)
        elif role == "tool":
            for tr in m.get("tool_results") or []:
                out["tool_result"] += estimate_tokens(tr.get("result", ""))
    return out


def build_budget(
    *,
    system_prompt: Optional[str] = None,
    prompt: str = "",
    tools: Optional[list] = None,
    messages: Optional[list] = None,
    digest: str = "",
) -> ContextBudget:
    """Estimate the model-visible request from its components."""
    budget = ContextBudget()
    budget.system_tokens = estimate_tokens(system_prompt or "")
    budget.tool_schema_tokens = estimate_tokens(tools or [])
    if messages:
        parts = _split_messages(messages)
        budget.history_tokens = parts["history"]
        budget.tool_result_tokens = parts["tool_result"]
        budget.user_tokens = parts["user"]
    elif prompt:
        budget.user_tokens = estimate_tokens(prompt)
    if digest:
        budget.digest_tokens = estimate_tokens(digest)
    budget.total_tokens = budget.estimate_total()
    budget.billable_tokens = budget.total_tokens
    return budget


def format_budget(budget: ContextBudget, label: str = "request") -> str:
    """Human-readable block of a profiled request (PlanFixes2 #28)."""
    def row(name: str, tokens: int) -> str:
        return f"{name:<22} {tokens:>7,}"

    lines = [f"--- {label} (per-call) ---"]
    lines.append(row("system", budget.system_tokens))
    lines.append(row("tool schemas", budget.tool_schema_tokens))
    lines.append(row("history", budget.history_tokens))
    lines.append(row("tool result", budget.tool_result_tokens))
    lines.append(row("user", budget.user_tokens))
    lines.append(row("digest", budget.digest_tokens))
    total = budget.total_tokens
    lines.append("-" * 32)
    lines.append(row("input (total)", total))
    if budget.cached_input_tokens or budget.fresh_input_tokens:
        lines.append(row("cached", budget.cached_input_tokens))
        lines.append(row("fresh", budget.fresh_input_tokens))
    lines.append(row("output", budget.output_tokens))
    lines.append(row("billable", budget.billable_tokens))
    return "\n".join(lines)


def estimate_gemini_request(
    *,
    contents: Any = None,
    system_instruction: Any = None,
    tools: Any = None,
) -> "ContextBudget":
    """Estimate the exact wire payload Gemini receives immediately before
    generate_content (PlanFixes2 §7): `contents`, `system_instruction`, and
    `tools`, after the provider transformation. The orchestrator profiler sees
    the pre-transformation representation; this one sees what is actually sent.
    """
    budget = ContextBudget()
    budget.system_tokens = estimate_tokens(system_instruction)
    budget.tool_schema_tokens = estimate_tokens(tools)
    budget.history_tokens = estimate_tokens(contents)
    budget.total_tokens = (
        budget.system_tokens + budget.tool_schema_tokens + budget.history_tokens
    )
    budget.billable_tokens = budget.total_tokens
    return budget


def format_wire_vs_actual(wire: "ContextBudget", usage: dict) -> str:
    """Compare the predicted wire request with the provider's prompt account."""
    predicted = int(wire.total_tokens or 0)
    actual = int(usage.get("provider_prompt_tokens", 0) or 0)
    return (
        f"--- WIRE vs ACTUAL ---\n"
        f"predicted_prompt      {predicted:>8,}\n"
        f"provider_prompt       {actual:>8,}\n"
        f"cached                {int(usage.get('provider_cached_tokens', 0) or 0):>8,}\n"
        f"fresh                 {int(usage.get('fresh_prompt_tokens', 0) or 0):>8,}\n"
        f"output                {int(usage.get('completion_tokens', 0) or 0):>8,}"
    )