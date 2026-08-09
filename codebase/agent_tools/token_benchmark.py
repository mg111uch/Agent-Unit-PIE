"""Token budget benchmark — Phase 10 Current-vs-Target report.

Runs a fixed task set through the real agent loop (MockProvider) and aggregates
LLMOrchestrator.profile_records into one Current-vs-Target table.

Two token realities are reported SEPARATELY and never combined:
  - raw      : the prompt/input tokens the provider counts (here estimated by
               the context budget, since MockProvider reports no usage).
  - billable : fresh_input + output tokens, the share that actually bills.

Usage:  conda run -n myenv python codebase/agent_tools/token_benchmark.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_core.config import resolve_active_tool_packs
from agent_core.llm_orchestrator import LLMOrchestrator
from agent_core.loop.engine import iter_agent_events
from agent_core.message_store import MessageStore
from agent_core.providers.mock_provider import MockProvider
from agent_core.tools import registry

_TASKS = [
    "check_path_exists temp/dummy/calculator.py",
    "read file temp/dummy/calculator.py",
    "list files in temp/dummy",
    "grep for 'def ' in *.py",
    "glob '**/*.py'",
    "create temp/new.txt",
    "edit temp/dummy/calculator.py rename add to add2",
    "run pytest on temp/dummy",
    "summarize temp/dummy directory",
    "what changed in this repo",
]


def _avg(recs: list[dict], key: str) -> int:
    """Average of a token field across calls (per-step Current value)."""
    if not recs:
        return 0
    return int(sum(int(r.get(key, 0) or 0) for r in recs) / len(recs))


def report(recs: list[dict], tasks_n: int) -> None:
    calls = len(recs)
    measured = any(r.get("provider_source") == "measured" for r in recs)
    fresh = _avg(recs, "fresh_input_tokens")
    cached = _avg(recs, "cached_input_tokens")
    out = _avg(recs, "output_tokens")
    schema = _avg(recs, "tool_schema_tokens")
    history = _avg(recs, "history_tokens")
    tot = sum(int(r.get("total_tokens", 0) or 0) for r in recs)
    bill_total = sum(int(r.get("billable_tokens", 0) or 0) for r in recs)
    ndash = "–" * 5

    def cur(v: int, tgt_ok: bool) -> str:
        if not measured:
            return ndash
        return f"{v:,} {'ok' if tgt_ok else 'NO'}"

    cached_share = cached / (cached + fresh) if (cached + fresh) else 0.0

    def cell(v: int, ok: bool) -> str:
        return (f"{v:,} ok" if ok else f"{v:,} NO") if measured else ndash

    def pct(v: float, ok: bool) -> str:
        return (f"{v:.0%} ok" if ok else f"{v:.0%} NO") if measured else ndash

    print("\n  Current vs Target (aggregated over the run)")
    src = "measured" if measured else "estimated (mock: no usage)"
    print(f"  {'source':<22}{src}")
    print("  " + "-" * 60)
    print(f"  {'Task count':<22}{tasks_n:>10}  {tasks_n}")
    print(f"  {'LLM calls':<22}{calls:>10}")
    print(f"  {'Fresh input / step':<22}{cell(fresh, fresh < 1200):>10}  < 1,200")
    print(f"  {'Cached share':<22}{pct(cached_share, cached_share > 0.70):>10}  >= 70%")
    print(f"  {'Output / step':<22}{cell(out, out < 500):>10}  < 500")
    print(f"  {'Tool schema / step':<22}{cell(schema, schema < 500):>10}  < 500")
    print(f"  {'History / step':<22}{cell(history, history < 500):>10}  < 500")
    raw_tgt = "YES" if 12_000 <= tot <= 18_000 else "NO"
    print(f"  {'Request tokens (total)':<22}{tot:>10,}  target 12k–18k ({raw_tgt})")

    print("\n  Raw vs billable (never combined)")
    print(f"  {'raw / input tokens':<22}{tot:>10,}")
    print(f"  {'billable (fresh+out)':<22}{bill_total if measured else ndash:>10}")


def main() -> None:
    store = MessageStore(":memory:")
    session_id = "benchmark"
    store.create_session(session_id)

    orchestrator = LLMOrchestrator(default_provider="mock", default_model="mock")
    orchestrator.register_provider("mock", MockProvider(scenario="full_chat"))

    schemas = registry.get_schemas(
        provider_name="mock", categories=resolve_active_tool_packs()
    )
    tool_names = sorted(
        s.get("name") or s.get("function", {}).get("name", "") for s in schemas
    )
    print(f"\nActive tools ({len(tool_names)}): {', '.join(tool_names)}")

    before = len(orchestrator.profile_records)
    for i, task in enumerate(_TASKS, 1):
        for ev in iter_agent_events(
            task,
            orchestrator,
            provider="mock",
            model="mock",
            system_prompt="You are a coding agent.",
            max_steps=6,
            retrieve_context=False,
            msg_store=store,
            session_id=session_id,
        ):
            if ev["type"] == "final":
                break
        after = len(orchestrator.profile_records)
        print(f"  task {i:>2}/{len(_TASKS)}: {task[:44]:<44} {after - before:>2} calls")
        before = after

    recs = orchestrator.profile_records[:]
    report(recs, len(_TASKS))


if __name__ == "__main__":
    main()