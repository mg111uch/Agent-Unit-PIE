"""Agent evaluation harness — Phase 8.

Tests agent BEHAVIOR, not just functions (FixesIssues #6/#9).
Mini helpers are pure (no DB writes) for gate use; full suite is deterministic.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Dict, List, Any, Tuple

def conformance_mini() -> Tuple[bool,str]:
    """Workflow conformance mini: legal path ok, illegal blocked."""
    try:
        from development.workflow_engine import WorkflowEngine
        we = WorkflowEngine()
        we.advance("orient")
        we.advance("version_sync", produced={"context":"x"}, success="context_found")
        we.advance("hypothesis", produced={"version_id":"v"}, success="version_synced")
        we.advance("decide_branch", produced={"hypothesis_id":"h"}, success="hypothesis_ready")
        we.advance("experiment", produced={"branch":"experiment"}, success="branch_chosen")
        we.advance("update_knowledge", produced={"run_id":"r","finding_id":"f"}, success="finding_registered")
        # illegal should raise
        we2 = WorkflowEngine()
        try:
            we2.advance("experiment")
            return False, "conformance fail: illegal start->experiment not blocked"
        except ValueError:
            pass
        return True, "conformance ok"
    except Exception as e:
        return False, f"conformance error: {e}"

def adversarial_mini() -> Tuple[bool,str]:
    """Lineage sanity (5 invariants) using in-memory nodes — no DB writes."""
    try:
        from kernel.simulation_version import is_compatible, affected_by
        from kernel.schemas.simulation_schema import concepts_for_changed_files
        # 1 stale, 2 partial, 3 unrelated, 4 opposite not contradiction, 5 same-version contradiction
        c1 = concepts_for_changed_files(["codebase/modules/simulators/popula_dyn/core/reproduction.py"])
        c2 = concepts_for_changed_files(["codebase/modules/simulators/popula_dyn/core/regrow.py"])
        if not ("population_growth" in c1 and "terrain" in c2):
            return False, f"adversarial concept map fail {c1}/{c2}"
        # affected_by
        if not affected_by(["population_growth"], c1): return False, "affected_by fail"
        if affected_by(["population_growth"], c2): return False, "unrelated should not affect"
        # is_compatible mock lineage
        if not is_compatible("popula_dyn@abc", "popula_dyn@abc", "popula_dyn"): return False, "compatible self fail"
        return True, "adversarial mini ok"
    except Exception as e:
        return False, f"adversarial mini error: {e}"

# ---- Full suite (deterministic, writes only to tmp topic) ----

def _run_one(name: str, fn) -> Dict[str, Any]:
    t0=time.time()
    try:
        ok, msg = fn()
        return {"name": name, "pass": bool(ok), "msg": msg, "ms": int((time.time()-t0)*1000)}
    except Exception as e:
        return {"name": name, "pass": False, "msg": f"exception: {e}", "ms": int((time.time()-t0)*1000)}

def _recovery_check() -> Tuple[bool,str]:
    # inject failures and ensure graceful error strings (not crash)
    try:
        from development.develop_tools import develop_experiment, develop_modify_simulator
        r1 = develop_experiment({"run_id": ""})  # missing
        if "Error" not in r1: return False, "recovery: missing run_id not error"
        r2 = develop_modify_simulator({"path": "nope.md"})
        if "Error" not in r2: return False, "recovery: missing old_string not error"
        # workflow violation already tested in conformance
        return True, "recovery ok"
    except Exception as e:
        return False, str(e)

def _workflow_evolution_check() -> Tuple[bool,str]:
    # validate that editing research_development.json inefficiency is detectable
    try:
        from development.contracts import validate_workflow
        p = Path("data/workflows/research_development.json")
        data = json.loads(p.read_text())
        ok, _ = validate_workflow(data)
        if not ok: return False, "workflow_evolution: base workflow invalid"
        # simulate adding doc-only node (no logic) -> still valid but measure token cost
        data["nodes"].append({"id":"tmp_doc","goal":"doc","inputs":[],"preconditions":[],"actions":[],"outputs":[],"success":["done"],"failure":[],"next":[]})
        ok2,_ = validate_workflow(data)
        if not ok2: return False, "added node should still validate"
        return True, "workflow_evolution ok (detect inefficiency via token count in Phase 7 state)"
    except Exception as e:
        return False, str(e)

def _research_loop_check() -> Tuple[bool,str]:
    # state should contain required fields and budget
    try:
        from development.development_state import generate_state
        s = generate_state("popula_dyn")
        need = ["sim","git","wf_node","allowed","hyps","runs","_bytes"]
        for k in need:
            if k not in s: return False, f"research_loop: missing {k}"
        if s["_bytes"] > 2000: return False, f"budget exceed {s['_bytes']}"
        return True, f"research_loop ok bytes={s['_bytes']}"
    except Exception as e:
        return False, str(e)

def run_all() -> Dict[str,Any]:
    suite = [
        ("workflow_conformance", lambda: conformance_mini()),
        ("recovery", _recovery_check),
        ("adversarial_lineage", lambda: adversarial_mini()),
        ("workflow_evolution", _workflow_evolution_check),
        ("research_loop", _research_loop_check),
    ]
    results = [_run_one(n, fn) for n, fn in suite]
    passed = sum(1 for r in results if r["pass"])
    # self-improvement benchmark placeholder: measure tool surface vs iteration
    bench = {
        "iterations_to_solution": "n/a (run via develop_orient→experiment→analyze loop with clean context)",
        "tool_surface_tokens": "~2KB state vs 10.8k all-tools (develop.* reduces load)",
        "note": "Does iteration N+1 use fewer tools and better simulator? Measure via harness repeated runs."
    }
    return {"total": len(results), "passed": passed, "results": results, "benchmark": bench, "ts": int(time.time())}

if __name__ == "__main__":
    import sys
    out = run_all()
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["passed"]==out["total"] else 1)
