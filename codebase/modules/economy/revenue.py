"""RA-6 revenue metrics + learning: funnel math, sales experiments, findings.

funnel() turns stage counts into conversion rates. time_to_first_revenue()
measures the launch-phase North Star from event timestamps. ab_test()
compares two offers/prices/messages with a min-N confidence rule and emits
a kernel-ready finding dict (hypothesis/experiment/result/confidence).
Pure functions, no DB.
"""
from __future__ import annotations
from typing import Any, Dict, List

FUNNEL_STAGES = ("prospects", "researched", "contacted", "responses",
                 "proposals", "pilots", "won")
MIN_TRIALS = 30


def funnel(counts: Dict[str, float]) -> Dict[str, Any]:
    """Stage counts -> per-step conversion + end-to-end hit rate."""
    stages = [s for s in FUNNEL_STAGES if s in counts]
    conv, prev = {}, None
    for s in stages:
        conv[s] = round(counts[s] / prev, 3) if prev else 1.0
        prev = counts[s] if counts[s] else 0
    end_to_end = round(counts[stages[-1]] / counts[stages[0]], 4) if stages and counts[stages[0]] else 0.0
    return {"stages": stages, "counts": dict(counts),
            "conversion": conv, "end_to_end": end_to_end}


def time_to_first_revenue(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """First 'prospect' ts -> first 'payment' ts (days). None yet = pending."""
    first, paid = None, None
    for e in events or []:
        ts = float(e.get("ts", 0) or 0)
        if e.get("stage") == "prospect" and (first is None or ts < first):
            first = ts
        if e.get("stage") == "payment" and (paid is None or ts < paid):
            paid = ts
    if first is None or paid is None:
        return {"days": None, "status": "pending"}
    return {"days": round((paid - first) / 86400, 1), "status": "achieved"}


def ab_test(name: str, hypothesis: str, arm_a: Dict[str, float],
            arm_b: Dict[str, float]) -> Dict[str, Any]:
    """Two arms {sent, won} -> winner + finding. <MIN_TRIALS = inconclusive."""
    ra = (arm_a.get("won", 0) or 0) / arm_a["sent"] if arm_a.get("sent") else 0.0
    rb = (arm_b.get("won", 0) or 0) / arm_b["sent"] if arm_b.get("sent") else 0.0
    n = (arm_a.get("sent", 0) or 0) + (arm_b.get("sent", 0) or 0)
    if n < MIN_TRIALS:
        verdict, conf = "inconclusive", 0.3
    else:
        verdict = "B" if rb > ra else ("A" if ra > rb else "tie")
        conf = round(min(0.95, 0.5 + abs(rb - ra) * 2 + n / 1000), 2)
    return {"experiment": name, "hypothesis": hypothesis,
            "rate_a": round(ra, 3), "rate_b": round(rb, 3),
            "trials": n, "verdict": verdict,
            "finding": {"hypothesis": hypothesis,
                        "result": f"{verdict} wins ({round(ra,3)} vs {round(rb,3)}, n={n})",
                        "confidence": conf,
                        "evidence": {"experiment": name, "arm_a": arm_a, "arm_b": arm_b}}}
