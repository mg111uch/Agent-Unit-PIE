"""Reporter reliability (sensors §11, in-repo half): per-reporter per-capability
scores from history, independent-confirmation counting, confirmation-weighted
confidence that SCALES CityState confidence (never replaces it).
"""
from __future__ import annotations

from typing import Any, Dict, List


def score_reporter(history: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """history [{capability, accurate: bool}] -> {cap: {score, n}} Laplace-smoothed."""
    out: Dict[str, Dict[str, float]] = {}
    by_cap: Dict[str, List[bool]] = {}
    for h in history or []:
        by_cap.setdefault(str(h.get("capability", "general")), []).append(bool(h.get("accurate")))
    for cap, flags in by_cap.items():
        out[cap] = {"score": round((sum(flags) + 1) / (len(flags) + 2), 3), "n": len(flags)}
    return out


def confirmations(observations: List[Dict[str, Any]], metric: str, value: Any,
                  tol: float = 0.05) -> int:
    """Independent reporters agreeing on metric+value (distinct reporter_ids, self excluded)."""
    reporters = set()
    for o in observations or []:
        if o.get("metric") != metric:
            continue
        try:
            if abs(float(o.get("value", 0)) - float(value)) > tol * max(1.0, abs(float(value))):
                continue
        except (TypeError, ValueError):
            if o.get("value") != value:
                continue
        if o.get("reporter_id") is not None:
            reporters.add(o["reporter_id"])
    return max(0, len(reporters) - 1)  # first reporter is the claim itself


def weighted_confidence(base: float, reporter_score: float = 0.5,
                        confirm_count: int = 0) -> float:
    """Scale base confidence: neutral (1.0x) at score 0.5 + 0 confirms."""
    f = (0.5 + min(1.0, max(0.0, reporter_score))) * (1 + 0.1 * min(int(confirm_count), 3))
    f = min(1.2, max(0.5, f))
    return round(min(0.99, float(base) * f), 3)
