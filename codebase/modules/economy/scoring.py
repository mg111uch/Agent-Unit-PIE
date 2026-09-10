"""Opportunity scoring: demand x capability x margin x speed x cost
x scalability x adjacency (FireFlow A4 roadmap, single source).

Pure function, no DB. Zero-capital bias: startup_cost (cost) and
time_to_revenue (speed) carry the heaviest weights, and a cheap gate
rejects capital-heavy opps first (stock alpha-gate philosophy).
"""
from __future__ import annotations
import re
from dataclasses import asdict
from typing import Any, Dict

W = {"demand": 0.16, "capability_fit": 0.16, "margin": 0.12,
     "speed": 0.16, "cost": 0.20, "scalability": 0.10,
     "adjacency": 0.10}  # cost + speed = 0.36: zero-capital bias
PASS_AT = 0.65
WATCH_AT = 0.40
COST_GATE_MULT = 10.0  # startup_cost > 10x price -> auto REJECT (cheap gate)
_DAYS = {"d": 1, "w": 7, "m": 30, "y": 365}


def _d(o: Any) -> Dict[str, Any]:
    return asdict(o) if not isinstance(o, dict) else dict(o)


def _clamp(v: Any) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def parse_days(s: Any) -> float:
    """'30d'/'6m'/'2w'/'1y'/plain number -> days; unknown -> 180 (mild penalty)."""
    if isinstance(s, (int, float)):
        return max(0.0, float(s))
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([dwmy])?\s*", str(s or ""))
    if not m:
        return 180.0
    return float(m.group(1)) * _DAYS.get((m.group(2) or "d").lower(), 1)


def capability_fit(opp: Any, unit: Any) -> float:
    req = _d(opp).get("required_capabilities") or []
    if not req:
        return 0.5  # unknown requirements -> neutral
    have = set(_d(unit).get("capabilities", []) or [])
    return len(set(req) & have) / max(1, len(req))


def score_opportunity(opp: Any, unit: Any = None) -> Dict[str, Any]:
    """Score 0..1 + breakdown + verdict (PASS >= .65, WATCH >= .40, else REJECT)."""
    o, a = _d(opp), _d(unit or {})
    price = max(1.0, float(o.get("price", 0) or 0))
    ratio = float(o.get("startup_cost", 0) or 0) / price
    b = {"demand": _clamp(o.get("moonshot_relevance", 0.0)),
         "capability_fit": _clamp(capability_fit(o, a)),
         "margin": _clamp(o.get("margin", 0.0)),
         "speed": 1.0 / (1.0 + parse_days(o.get("time_to_revenue", "")) / 60.0),
         "cost": 1.0 / (1.0 + ratio * 3.0),
         "scalability": _clamp(o.get("scalability", 0.0)),
         "adjacency": _clamp(o.get("adjacency", 0.0))}
    score = round(sum(W[k] * b[k] for k in W), 3)
    b = {k: round(v, 3) for k, v in b.items()}
    verdict = ("REJECT" if ratio > COST_GATE_MULT or score < WATCH_AT
               else "PASS" if score >= PASS_AT else "WATCH")
    return {"score": score, "breakdown": b, "verdict": verdict}


def barter_price(base: Any, scarcity: Any, sensitivity: Any = 1.0) -> float:
    """Shared barter kernel: scarcity-priced exchange, no currency.

    Single source lives in popula_dyn `core/scarcity.py`; this wrapper keeps
    the economy module on the same pricing without touching the ledger.
    """
    from modules.simulators.popula_dyn.core.scarcity import barter_price as _bp
    return _bp(base, scarcity, sensitivity)
