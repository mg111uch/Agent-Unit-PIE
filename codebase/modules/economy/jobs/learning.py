"""JF-6 job learning + economics: rates -> hypotheses, EV per application.

funnel_rates() converts stage counts to conversions. source_rates() shows
which feeds earn interviews. hypothesize() only claims patterns with
n>=10 behind them — otherwise it says so honestly. application_ev()
reuses the revenue EV kernel: P(offer) x annual value - apply cost.
Pure functions, no DB.
"""
from __future__ import annotations
from typing import Any, Dict, List

MIN_N = 10
FUNNEL = ("scored", "applied", "screen", "interview", "offer", "accepted")


def funnel_rates(counts: Dict[str, float]) -> Dict[str, Any]:
    stages = [s for s in FUNNEL if s in counts]
    conv, prev = {}, None
    for s in stages:
        conv[s] = round(counts[s] / prev, 3) if prev else 1.0
        prev = counts[s] if counts[s] else 0
    end = round(counts[stages[-1]] / counts[stages[0]], 4) if stages and counts[stages[0]] else 0.0
    return {"stages": stages, "conversion": conv, "end_to_end": end}


def source_rates(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Rows {source, interviewed bool} -> per-source {n, rate}."""
    agg: Dict[str, Dict[str, float]] = {}
    for r in rows or []:
        s = agg.setdefault(r.get("source", "?"), {"n": 0, "hits": 0})
        s["n"] += 1
        s["hits"] += 1 if r.get("interviewed") else 0
    return {k: {"n": v["n"], "rate": round(v["hits"] / v["n"], 3)} for k, v in agg.items()}


def hypothesize(stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Patterns with backing n, else an explicit insufficient-data finding."""
    n = stats.get("applications", 0)
    if n < MIN_N:
        return [{"hypothesis": "insufficient data",
                 "result": f"only {n} applications (< {MIN_N})",
                 "confidence": 0.0,
                 "evidence": {"applications": n}}]
    out = []
    for src, r in (stats.get("by_source") or {}).items():
        if r["n"] >= 5 and r["rate"] >= 0.3:
            out.append({"hypothesis": f"{src} roles produce higher interview rate",
                        "result": f"{r['rate']} interview rate over n={r['n']}",
                        "confidence": round(min(0.9, 0.4 + r["rate"]), 2),
                        "evidence": {"source": src, **r}})
    return out or [{"hypothesis": "no strong pattern yet",
                    "result": "no source clears 0.3 over n>=5",
                    "confidence": 0.2, "evidence": stats}]


def application_ev(p_offer: float, salary_monthly: float | None,
                   apply_cost: float = 500.0) -> Dict[str, Any]:
    """EV of one application. Unknown salary -> pending, never zero-guessed."""
    from modules.economy.scoring import expected_value
    if not salary_monthly:
        return {"ev": None, "status": "pending_comp",
                "reason": "salary undisclosed — EV computed after comp known"}
    annual = float(salary_monthly) * 12
    return {"ev": expected_value(p_offer, annual, apply_cost),
            "status": "computed",
            "reason": f"P(offer)={p_offer} x {annual:.0f} - {apply_cost}"}
