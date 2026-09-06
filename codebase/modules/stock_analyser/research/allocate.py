"""Adaptive research allocator (stdlib): bandit over families + explore/exploit/validate split.

Weight(f) = prior(f) * (1 + ready_rate) + explore_bonus; bonus = sqrt(log(total+1)/(n+1)).
Priors via capital.yaml `family_priors` else ml=1.5, default=1.0 (ML-first discovery).
Split via `alloc_explore/exploit/validate` fractions (default 0.3/0.5/0.2).
Novelty quota (`novelty_frac`, default 0.15): least-tested family + feature-space
mutation, so winners don't starve exploration (anti premature convergence).
"""
from __future__ import annotations
import math
import random
from typing import Any, Dict, List


def prior_of(family: str, cap: Dict[str, Any]) -> float:
    priors = cap.get("family_priors", {}) or {}
    if family in priors:
        return float(priors[family])
    if family == "ml" or family.startswith("ml"):
        return float(cap.get("prior_ml", 1.5))
    return float(cap.get("prior_default", 1.0))


def family_stats(run_id: str, families: List[str], db_path: str | None = None) -> Dict[str, Dict]:
    from ..data.store import connect, ensure_schema
    ensure_schema(db_path)
    con = connect(db_path)
    try:
        try:
            con.execute("ALTER TABLE research_candidates ADD COLUMN family TEXT DEFAULT ''")
        except Exception:
            pass
        out: Dict[str, Dict] = {}
        for f in families:
            rows = con.execute("SELECT verdict, COALESCE(oos_net,-1e18) FROM research_candidates"
                               " WHERE run_id=? AND family=?", (run_id, f)).fetchall()
            n = len(rows)
            ready = sum(1 for v, _ in rows if v == "PAPER_READY")
            avg = sum(o for _, o in rows if o and o > -1e17) / max(1, sum(1 for _, o in rows if o and o > -1e17))
            out[f] = {"n": n, "ready": ready,
                      "ready_rate": ready / n if n else 0.0,
                      "avg_oos": avg if n else 0.0}
        return out
    finally:
        con.close()


def choose(families: List[str], stats: Dict[str, Dict], cap: Dict[str, Any],
           rng: random.Random) -> tuple:
    if rng.random() < float(cap.get("novelty_frac", 0.15)):
        fam = min(families, key=lambda f: (stats.get(f, {"n": 0})["n"], f))
        return fam, "explore", True  # novelty: fresh feature-space, not elite
    total = sum(s["n"] for s in stats.values())
    weights = []
    for f in families:
        s = stats.get(f, {"n": 0, "ready_rate": 0.0})
        bonus = math.sqrt(math.log(total + 2) / (s["n"] + 1))
        weights.append(max(0.05, prior_of(f, cap) * (1 + s["ready_rate"] * 2) + bonus))
    fam = rng.choices(families, weights=weights, k=1)[0]
    r = rng.random()
    ex = float(cap.get("alloc_explore", 0.3))
    ep = float(cap.get("alloc_exploit", 0.5))
    mode = "explore" if r < ex else ("exploit" if r < ex + ep else "validate")
    return fam, mode, False


NOVELTY_KINDS = {"ml": ("features", "model"),
                 "sym": ("feature_scale", "lookback", "threshold")}


def novelty_kind(is_ml: bool, rng: random.Random) -> str:
    pool = NOVELTY_KINDS["ml"] if is_ml else NOVELTY_KINDS["sym"]
    return rng.choice(pool)


# Phase 2 (FixesIssues #3/#9): ladder gating. ML only when L0-L2 evidence
# justifies escalation; never "ML failed → bigger ML".
LADDER = ["baseline", "sym", "ml"]


def gate_families(families: List[str], evidence: Dict[str, Any] | None,
                  cap: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Filter families by ladder evidence. evidence: {l2_best_ic, l2_best_spread}."""
    ev, gated, reasons = evidence or {}, [], {}
    ic = float(ev.get("l2_best_ic", 0) or 0)
    sp = float(ev.get("l2_best_spread", 0) or 0)
    min_ic = float((cap or {}).get("ladder_min_ic", 0.02))
    min_sp = float((cap or {}).get("ladder_min_spread", 0.15))
    ml_ok = ic >= min_ic or sp >= min_sp or bool(ev.get("force_ml"))
    for f in families:
        if (f == "ml" or f.startswith("ml")) and not ml_ok:
            reasons[f] = f"gated: L2 ic={ic} spread={sp} below min"
            continue
        gated.append(f)
    return {"allowed": gated or [f for f in families if not f.startswith("ml")] or families,
            "ml_allowed": ml_ok, "reasons": reasons}
