"""Graduated autonomy gate — Phase 8.

Levels (FixesIssues #7):
 L0 suggest        — no edit, always allowed
 L1 edit+test      — edit allowed but must run checks locally
 L2 edit+test+commit — as L1 plus commit permitted
 L3 sim self-modify — simulator code only, needs sim smoke
 L4 workflow self-modify — workflow JSON/MD, needs contracts + harness
 L5 kernel propose — suggestion only, gated human approval
 L6 kernel modify  — full gate: tests + lineage + retrieval + contracts

Default autonomy CEILING = 3 (sim). L4 gated, L5-6 require explicit human approval.
All checks reuse one SQLite persistence path — no second store.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

_LEVELS: Dict[int, Dict[str, Any]] = {
    0: {"name": "suggest", "desc": "Suggest change only", "needs": []},
    1: {"name": "edit+test", "desc": "Edit + local test", "needs": ["contracts"]},
    2: {"name": "edit+test+commit", "desc": "Edit + test + commit", "needs": ["contracts", "sim_smoke"]},
    3: {"name": "sim_modify", "desc": "Self-modify simulator", "needs": ["contracts", "sim_smoke", "lineage"]},
    4: {"name": "workflow_modify", "desc": "Self-modify workflow", "needs": ["contracts", "workflow_conformance", "sim_smoke"]},
    5: {"name": "kernel_propose", "desc": "Propose kernel change (human gate)", "needs": ["contracts", "human_approval"]},
    6: {"name": "kernel_modify", "desc": "Kernel modify with full gate", "needs": ["contracts", "sim_smoke", "lineage", "retrieval", "human_approval"]},
}
DEFAULT_CEILING = 3

# path category → required level
def required_level(path: str) -> int:
    p = Path(path).as_posix().lower()
    if "data/workflows" in p: return 4
    if "codebase/kernel" in p: return 6
    if "codebase/modules/stock_analyser" in p: return 3
    if "codebase/modules/simulators" in p: return 3
    if "codebase/development" in p: return 4
    if p.endswith(".md") and "workflow" in p: return 4
    return 2  # generic code

def _check_contracts(path: str) -> Tuple[bool, str]:
    if "data/workflows" in path and path.endswith(".json"):
        try:
            from development.contracts import validate_workflow
            data = json.loads(Path(path).read_text())
            ok, errs = validate_workflow(data)
            return ok, "contracts ok" if ok else f"contracts fail: {errs[:2]}"
        except Exception as e:
            return False, f"contracts error: {e}"
    return True, "contracts skip (not workflow json)"

def _check_sim_smoke() -> Tuple[bool, str]:
    # lightweight: check simulation connector importable + version sync works
    try:
        from kernel.simulation_version import get_current_version
        v = get_current_version("popula_dyn")
        return True, f"sim smoke ok ver={v['version_id'] if v else 'none'}"
    except Exception as e:
        return False, f"sim smoke fail: {e}"

def _check_lineage() -> Tuple[bool, str]:
    # run adversarial lineage mini-check via eval harness helper (no side effects)
    try:
        from development.eval_harness import adversarial_mini
        ok, msg = adversarial_mini()
        return ok, msg
    except Exception as e:
        return False, f"lineage check fail: {e}"

def _check_retrieval() -> Tuple[bool, str]:
    try:
        from kernel.retrieval.retrieval_engine import retrieval_engine
        # HISTORICAL filter sanity (no DB write)
        hits = retrieval_engine.search("population", limit=2, simulator="popula_dyn")
        return True, f"retrieval ok hits={len(hits)}"
    except Exception as e:
        return False, f"retrieval fail: {e}"

def _check_conformance() -> Tuple[bool, str]:
    try:
        from development.eval_harness import conformance_mini
        ok, msg = conformance_mini()
        return ok, msg
    except Exception as e:
        return False, f"conformance fail: {e}"

def gate(level: int, path: str, human_approved: bool=False) -> Dict[str, Any]:
    """Validate requested autonomy level against required level for path.

    Returns {allowed, required_level, requested_level, needs, results, message}
    """
    need_lv = required_level(path)
    allowed = level >= need_lv
    # ceiling enforcement
    if need_lv > DEFAULT_CEILING and not human_approved and level >= 5:
        # L5-6 need explicit approval even if level high enough
        if not human_approved:
            allowed = False
    info = _LEVELS.get(level, _LEVELS[0])
    target = _LEVELS.get(need_lv, _LEVELS[0])
    needs = target["needs"]
    results: Dict[str, Tuple[bool,str]] = {}
    # run checks if gate would allow (or to show why not)
    checkers = {
        "contracts": lambda: _check_contracts(path),
        "sim_smoke": _check_sim_smoke,
        "lineage": _check_lineage,
        "retrieval": _check_retrieval,
        "workflow_conformance": _check_conformance,
        "human_approval": lambda: (human_approved, "human approved" if human_approved else "need human approval"),
    }
    for n in needs:
        fn = checkers.get(n)
        if fn:
            results[n] = fn()
    all_pass = all(v[0] for v in results.values()) if results else True
    if allowed and not all_pass:
        allowed = False
    msg = f"need L{need_lv} ({target['name']}) for {path}; requested L{level} ({info['name']}) → {'ALLOW' if allowed else 'GATE'}"
    if not all_pass:
        fails = [k for k,v in results.items() if not v[0]]
        msg += f"; checks fail: {fails}"
    return {
        "allowed": allowed and all_pass,
        "required_level": need_lv,
        "requested_level": level,
        "needs": needs,
        "results": {k: {"pass": v[0], "msg": v[1]} for k,v in results.items()},
        "message": msg,
    }

def can_edit(path: str, level: int=DEFAULT_CEILING, human_approved: bool=False) -> Tuple[bool, str]:
    r = gate(level, path, human_approved)
    return r["allowed"], r["message"]
