"""Phase 4 — Gemini mode A/B/C benchmark + 3-step per-call diagnostic.

Compares the three Gemini execution modes from PlanPhases2 Phase 4:

  A. stateless                          (client-compacted history, implicit cache)
  B. stateful previous_interaction_id   (server-side chain, skip tools on chain)
  C. stateful + tool tools resend       (server-side chain, tools always attached)

Each mode runs the same task set through the real agent loop. Per-call token
facts come from LLMOrchestrator.profile_records (real provider usage when the
provider reports it, else the estimated budget).

Set GEMINI_DIAGNOSE=true to run the single 3-step task and log every call
individually (PlanFixes2 §8 P0 — the decisive experiment), instead of the
aggregate task set.

Usage:
  GEMINI_API_KEY=... conda run -n myenv python codebase/agent_tools/gemini_mode_benchmark.py
  # Without a key, it runs a deterministic mock calibration of the three modes.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_TASKS = [
    "check_path_exists temp/dummy/calculator.py",
    "read file temp/dummy/calculator.py",
    "list files in temp/dummy",
    "grep for 'def ' in *.py",
    "what changed in this repo",
]

# The decisive single-task diagnostic (PlanFixes2 §8): exactly one 3-step task,
# each call logged individually so the 10k can be attributed to system / tools /
# stateless replay.
_DIAGNOSE_TASK = (
    "Read temp/dummy/calculator.py and tell me what the add function does."
)

_MODES = [
    ("A  stateless(+implicit_cache)", {"GEMINI_STATELESS": True, "GEMINI_IMPLICIT_CACHE": True}),
    ("B  stateless(no cache)", {"GEMINI_STATELESS": True, "GEMINI_IMPLICIT_CACHE": False}),
    ("C  stateful", {"GEMINI_STATELESS": False, "GEMINI_IMPLICIT_CACHE": False}),
]


def _read_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _apply(mode_patch: dict) -> None:
    import agent_core.config as cfg
    import agent_core.providers.gemini_provider as gp

    for name, val in mode_patch.items():
        setattr(cfg, name, val)
        if hasattr(gp, name):
            setattr(gp, name, val)


def _build_mock_orch() -> any:
    from agent_core.llm_orchestrator import LLMOrchestrator
    from agent_core.providers.mock_provider import MockProvider

    orch = LLMOrchestrator(default_provider="mock", default_model="mock")
    orch.register_provider("mock", MockProvider(scenario="full_chat"))
    return orch


def _build_live_orch() -> any:
    from agent_core.llm_orchestrator import LLMOrchestrator
    from agent_core.providers.gemini_provider import GeminiProvider

    orch = LLMOrchestrator(
        default_provider="gemini", default_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    )
    orch.register_provider(
        "gemini", GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"), model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"))
    )
    return orch


def _print_per_call(recs, label: str) -> None:
    """Log each individual call's wire-level token accounting (PlanFixes2 §8)."""
    print(f"\n  [{label}] per-call detail")
    print(f"  {'call':<6}{'prov_prompt':>12}{'cached':>8}{'fresh':>8}{'out':>6}{'tool_schema':>12}{'history':>9}")
    for r in recs:
        fresh = int(r.get("fresh_prompt_tokens", r.get("fresh_input_tokens", 0)) or 0)
        cached = int(r.get("provider_cached_tokens", r.get("cached_input_tokens", 0)) or 0)
        prov_prompt = int(r.get("provider_prompt_tokens", 0) or 0)
        if not prov_prompt and (fresh or cached):
            prov_prompt = fresh + cached
        print(
            f"  {r.get('call_num','?'):<6}"
            f"{prov_prompt:>12,}"
            f"{cached:>8,}"
            f"{fresh:>8,}"
            f"{int(r.get('output_tokens', 0) or 0):>6,}"
            f"{int(r.get('tool_schema_tokens', 0) or 0):>12,}"
            f"{int(r.get('history_tokens', 0) or 0):>9,}"
        )


def _run_tasks(orch, store, tasks, max_steps=8) -> None:
    from agent_core.loop.engine import iter_agent_events
    for task in tasks:
        for ev in iter_agent_events(
            task, orch, provider=orch.default_provider, model=orch.default_model,
            system_prompt="You are a coding agent.", max_steps=max_steps,
            msg_store=store, session_id="ab",
        ):
            if ev["type"] == "final":
                break


# ---------------------------------------------------------------------------
# Phase 4b / PlanFixes2 §P3 — per-scenario benchmark (8 cases A-H)
# ---------------------------------------------------------------------------

# Each case: label, prompt handed to the agent, and optional deterministic
# mock stanzas so the offline run exercises the same tool paths as live.
# G ("failed tool") and H ("nonexistent file") deliberately end in a failed
# tool so tool_failures / false_success can be observed.
_P3_CASES = [
    ("A  find existing file",
     "find temp/dummy/calculator.py",
     [{"response": "", "tool_calls": [{"name": "glob_search", "arguments": {"pattern": "temp/dummy/calculator.py"}}]},
      {"response": '{"final": "Found it: temp/dummy/calculator.py"}', "tool_calls": None}]),
    ("B  read file",
     "read file temp/dummy/calculator.py",
     [{"response": "", "tool_calls": [{"name": "read_file", "arguments": {"path": "temp/dummy/calculator.py"}}]},
      {"response": '{"final": "Here is the file."}', "tool_calls": None}]),
    ("C  create directory",
     "create directory temp/toolbench",
     [{"response": "", "tool_calls": [{"name": "execute_command", "arguments": {"command": "mkdir -p temp/toolbench"}}]},
      {"response": '{"final": "Created directory temp/toolbench."}', "tool_calls": None}]),
    ("D  write file",
     "overwrite the file temp/dummy/bench_write.txt with content hello",
     [{"response": "", "tool_calls": [{"name": "write_to_file", "arguments": {"path": "temp/dummy/bench_write.txt", "mode": "overwrite", "content": "hello"}}]},
      {"response": '{"final": "Wrote the file."}', "tool_calls": None}]),
    ("E  edit file",
     "add a multiply function to temp/dummy/calculator.py",
     [{"response": "", "tool_calls": [{"name": "edit_file", "arguments": {"path": "temp/dummy/calculator.py", "old_string": "def add(", "new_string": "def mul(\n    return x*y\n\ndef add("}}]},
      {"response": '{"final": "Added multiply."}', "tool_calls": None}]),
    ("F  execute command",
     "run the python version",
     [{"response": "", "tool_calls": [{"name": "execute_command", "arguments": {"command": "python3 --version"}}]},
      {"response": '{"final": "Python 3.11."}', "tool_calls": None}]),
    ("G  failed tool",
     "run the imaginary command predict_the_research_parity",
     [{"response": "", "tool_calls": [{"name": "nonexistent_tool_xyz", "arguments": {}}]},
      {"response": '{"final": "Done."}', "tool_calls": None}]),
    ("H  nonexistent file",
     "read file temp/dummy/does_not_exist_xyz.py",
     [{"response": "", "tool_calls": [{"name": "read_file", "arguments": {"path": "temp/dummy/does_not_exist_xyz.py"}}]},
      {"response": '{"final": "Read done."}', "tool_calls": None}]),
]

_FAIL_TERMS = (
    "fail", "failed", "error", "blocked", "not allowed", "denied", "rejected",
    "not found", "doesn't exist", "does not exist", "no such", "missing",
    "unable", "cannot", "can't", "nonexistent", "non-existent",
    "not executed", "uncompleted", "permission",
)


def _detect_false_success(failures: int, final_text: str) -> int:
    """P0 #1: a failed tool must never be reported as success.

    Returns 1 when tool_failures>0 but the final answer still claims success
    (no failure wording); else 0. Deterministic heuristic for benchmarking.
    """
    if not failures or not final_text:
        return 0
    low = final_text.lower()
    if any(t in low for t in _FAIL_TERMS):
        return 0
    return 1


def _sum_rec(recs: list[dict], key: str) -> int:
    return sum(int(r.get(key, 0) or 0) for r in recs)


def _run_p3(orch, store, prompt, max_steps=8) -> dict:
    from agent_core.loop.engine import iter_agent_events
    from agent_core.prompts import load_system_prompt
    from agent_core.config import resolve_active_tool_packs, resolve_active_tool_mode, SYSTEM_PROMPT_CORE_ONLY
    system_prompt = load_system_prompt(
        active_packs=resolve_active_tool_packs(),
        mode=resolve_active_tool_mode(),
        core_only=SYSTEM_PROMPT_CORE_ONLY,
    )
    failures = 0
    finals = []
    for ev in iter_agent_events(
        prompt, orch, provider=orch.default_provider, model=orch.default_model,
        system_prompt=system_prompt, max_steps=max_steps,
        msg_store=store, session_id="p3",
    ):
        t = ev["type"]
        if t == "tool_result":
            if ev.get("ok") is False:
                failures += 1
        elif t in ("error", "parse_error"):
            failures += 1
        elif t == "final":
            finals.append(ev.get("full_content") or ev.get("content") or "")
    final_text = "\n".join(finals)

    recs = orch.profile_records
    output = _sum_rec(recs, "output_tokens")
    total_in = _sum_rec(recs, "total_tokens")
    return {
        "initial_prompt_tokens": int(recs[0].get("total_tokens", 0) or 0) if recs else 0,
        "tool_schema_tokens": _sum_rec(recs, "tool_schema_tokens"),
        "system_tokens": _sum_rec(recs, "system_tokens"),
        "continuation_tokens": _sum_rec(recs, "history_tokens") + _sum_rec(recs, "tool_result_tokens"),
        "output_tokens": output,
        "total": total_in + output,
        "tool_failures": failures,
        "false_success": _detect_false_success(failures, final_text),
        "calls": len(recs),
    }


def _build_mock(orch, stanzas) -> None:
    from agent_core.providers.mock_provider import MockProvider
    orch.register_provider("mock", MockProvider(stanzas=stanzas))


def run_p3_benchmark(live: bool) -> None:
    """Run the 8 PlanFixes §P3 scenarios and print the required per-case rows."""
    from agent_core.message_store import MessageStore
    from agent_core.llm_orchestrator import LLMOrchestrator

    rows = []
    for label, prompt, mock_stanzas in _P3_CASES:
        if live:
            orch = _build_live_orch()
        else:
            orch = LLMOrchestrator(default_provider="mock", default_model="mock")
            _build_mock(orch, mock_stanzas)
        store = MessageStore(":memory:")
        store.create_session("p3")
        m = _run_p3(orch, store, prompt)
        rows.append((label, m))

    cols = ("initial_prompt_tokens", "tool_schema_tokens", "system_tokens",
            "continuation_tokens", "output_tokens", "total",
            "tool_failures", "false_success")
    width = max(8, len("initial_prompt"))
    header = f"{'Scenario':<24}" + "".join(f"{c:>{width+2}}" for c in cols)
    print(f"\nPlanFixes §P3 — per-scenario benchmark ({'LIVE' if live else 'MOCK'})")
    print(f"{'Scenario':<24}" + "".join(f"{c:>{width+2}}" for c in cols))
    print("-" * len(header))
    for label, m in rows:
        vals = "".join(f"{m[c]:>{width+2}}" for c in cols)
        print(f"{label:<24}{vals}  calls={m['calls']}")
    print(f"\nPipe: {'live Gemini' if live else 'mock (deterministic stanzas)'} — "
          f"set GEMINI_API_KEY for live runs.")


def main() -> None:
    from agent_core.config import resolve_active_tool_packs
    from agent_core.loop.engine import iter_agent_events
    from agent_core.message_store import MessageStore
    from agent_core.tools import registry

    live = _read_key()
    if os.getenv("GEMINI_P3", "").lower() in ("1", "true", "yes"):
        run_p3_benchmark(live=live)
        return
    diagnose = os.getenv("GEMINI_DIAGNOSE", "").lower() in ("1", "true", "yes")
    tasks = [_DIAGNOSE_TASK] if diagnose else _TASKS
    rows: list[tuple[str, dict, str]] = []
    for label, patch in _MODES:
        _apply(patch)
        orch = _build_live_orch() if live else _build_mock_orch()
        store = MessageStore(":memory:")
        store.create_session("ab")
        calls_before = orch.total_requests
        tot = {"fresh": 0, "cached": 0, "out": 0, "total": 0, "calls": 0}
        _ = resolve_active_tool_packs()  # keep import
        _run_tasks(orch, store, tasks, max_steps=8)
        recs = orch.profile_records[calls_before:]
        for rec in recs:
            tot["fresh"] += rec.get("fresh_input_tokens", 0)
            tot["cached"] += rec.get("cached_input_tokens", 0)
            tot["out"] += rec.get("output_tokens", 0)
            tot["total"] += rec.get("total_tokens", 0)
            tot["calls"] += 1
        rows.append((label, tot, "measured" if live else "estimated"))
        if diagnose:
            _print_per_call(recs, label)

    print(f"\n{'Mode':<28}{'calls':>7}{'fresh':>9}{'cached':>9}{'output':>8}{'total':>9}  src")
    print("-" * 72)
    for label, t, src in rows:
        print(f"{label:<28}{t['calls']:>7}{t['fresh']:>9}{t['cached']:>9}{t['out']:>8}{t['total']:>9}  {src}")
    print("\nPipe: run with GEMINI_API_KEY set for measured provider usage.")
    if not diagnose:
        print("Set GEMINI_DIAGNOSE=true for the single 3-step per-call diagnostic.")
    print("Set GEMINI_P3=true for the 8-case per-scenario benchmark (PlanFixes2 §P3).")


if __name__ == "__main__":
    main()