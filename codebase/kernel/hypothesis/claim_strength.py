"""Evidence ladder (KRN-06) — `claim_strength` enforced in code.

Docs already say "no finding above HYPOTHESIS without multi-seed + falsify".
This module makes that a check the bus runs, not a convention writers follow:

    HYPOTHESIS            default; anything can say it
    REPLICATED            >= MIN_SEEDS independent seeds and >= MIN_N samples
    FALSIFICATION_PASSED  replicated + a recorded falsification attempt
    VALIDATED_OOS         + out-of-sample holdout that held

`check()` never raises: it returns the highest level the evidence supports, so
an overstated claim is downgraded with a visible reason instead of silently
polluting memory.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

LEVELS = ("HYPOTHESIS", "REPLICATED", "FALSIFICATION_PASSED", "VALIDATED_OOS")
RANK = {name: i for i, name in enumerate(LEVELS)}


def min_n() -> int:
    """Minimum sample size for anything above HYPOTHESIS (REV-05/ KRN-06)."""
    try:
        return max(1, int(os.environ.get("PIE_MIN_N", "20")))
    except ValueError:
        return 20


def min_seeds() -> int:
    try:
        return max(1, int(os.environ.get("PIE_MIN_SEEDS", "2")))
    except ValueError:
        return 2


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _has_falsification(claim: Dict[str, Any]) -> bool:
    f = claim.get("falsification") or {}
    return bool(f.get("attempted")) and bool(f.get("passed"))


def _has_oos(claim: Dict[str, Any]) -> bool:
    o = claim.get("oos") or {}
    if not o:
        return False
    metrics = o.get("metrics") or {}
    return bool(o.get("holdout")) and bool(metrics) and \
        all(float(v) >= 0 for v in metrics.values() if isinstance(v, (int, float)))


def check(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Return requested vs supported strength and the blocking reasons."""
    requested = str((claim or {}).get("claim_strength") or "HYPOTHESIS").upper()
    if requested not in RANK:
        return {"requested": requested, "effective": "HYPOTHESIS", "ok": False,
                "violations": [f"unknown claim_strength {requested!r}"],
                "levels": list(LEVELS)}

    seeds = _int(claim.get("seeds"))
    n = _int(claim.get("n"))
    violations: List[str] = []
    effective = "HYPOTHESIS"

    if seeds >= min_seeds() and n >= min_n():
        effective = "REPLICATED"
    else:
        violations.append(
            f"REPLICATED needs >= {min_seeds()} seeds and n >= {min_n()}; "
            f"got seeds={seeds}, n={n}")
    if effective == "REPLICATED" and _has_falsification(claim):
        effective = "FALSIFICATION_PASSED"
    elif effective == "REPLICATED":
        violations.append("FALSIFICATION_PASSED needs a recorded, passed "
                          "falsification attempt")
    if effective == "FALSIFICATION_PASSED" and _has_oos(claim):
        effective = "VALIDATED_OOS"
    elif effective == "FALSIFICATION_PASSED":
        violations.append("VALIDATED_OOS needs an out-of-sample holdout with "
                          "metrics")

    ok = RANK[effective] >= RANK[requested]
    if not ok:
        violations.insert(0, f"claimed {requested} but evidence supports "
                             f"{effective}")
    return {"requested": requested, "effective": effective, "ok": ok,
            "violations": violations if not ok else [], "levels": list(LEVELS),
            "seeds": seeds, "n": n, "min_n": min_n(),
            "min_seeds": min_seeds()}


def enforce(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the verdict: return the claim at the level it can defend."""
    out = dict(claim or {})
    verdict = check(out)
    out["claim_strength"] = verdict["effective"]
    if not verdict["ok"]:
        out["claim_strength_requested"] = verdict["requested"]
        out["claim_strength_downgraded"] = verdict["violations"]
    return out


def level_at_least(level: str, floor: str) -> bool:
    return RANK.get(level, 0) >= RANK.get(floor, 0)
