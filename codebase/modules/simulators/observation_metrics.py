"""Typed observations for the symbolic gate, with a metric registry.

`build_observation` used to hardcode population, so urban runs (welfare,
output, employment) could not be registered as findings. This module keeps one
small registry: metric -> summary field + tolerance, plus an explicit
`outcome_override` for results that are not a single-direction change (for
example a policy whose sign flips across 400/2k/10k).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

METRIC_FIELDS = {
    "population": "population",
    "welfare": "welfare",
    "urban_output": "urban_output",
    "employment_rate": "employment_rate",
    "firms_per_1000": "firms_per_1000",
}

# Percentage move needed before a metric counts as improved/degraded.
TOLERANCE = {
    "population": 20.0,
    "welfare": 5.0,
    "urban_output": 10.0,
    "employment_rate": 10.0,
    "firms_per_1000": 5.0,
}

SCENARIO_KEYS = (
    "birth_rate", "death_rate", "initial_pop", "years", "mate_radius",
    "mate_global_fallback", "require_opposite_gender", "vision",
    # urban pack
    "domain", "firms_per_1000", "municipal_grant", "road_capacity",
    "power_capacity", "transport_cost", "municipal_capex", "mechanism",
    "magnitude", "scales",
)


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _scenario(params: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    if not baseline:
        return {k: params.get(k) for k in ("birth_rate", "death_rate",
                                          "firms_per_1000") if k in params}
    return {k: params.get(k) for k in SCENARIO_KEYS
            if params.get(k) != baseline.get(k)}


def build_observation(
    *,
    run_id: str,
    summary: Dict[str, Any],
    params: Dict[str, Any],
    signals: List[Dict[str, Any]],
    baseline_summary: Optional[Dict[str, Any]] = None,
    baseline_params: Optional[Dict[str, Any]] = None,
    metric: str = "population",
    simulator: str = "popula_dyn",
) -> Dict[str, Any]:
    """One typed observation; unknown metrics fall back to population."""
    metric = metric if metric in METRIC_FIELDS else "population"
    field = METRIC_FIELDS[metric]
    base = baseline_summary or {}
    observed = _num(summary.get(field))
    baseline_value = _num(base.get(field))

    change = ((observed - baseline_value) / baseline_value * 100
              if baseline_value else 0.0)
    tol = TOLERANCE.get(metric, 20.0)
    verdict = "STABLE"
    if change > tol:
        verdict = "IMPROVED"
    elif change < -tol:
        verdict = "DEGRADED"
    if metric == "population" and observed < 5:
        verdict = "COLLAPSED"

    direction = {"IMPROVED": "INCREASE", "DEGRADED": "DECREASE",
                 "COLLAPSED": "DECREASE"}.get(verdict, "STABLE")
    override = str(summary.get("outcome_override") or "")
    if override:
        verdict = override
        direction = "MIXED" if override in ("UNSTABLE", "MIXED") else direction

    return {
        "experiment": run_id,
        "simulator": simulator,
        "metric": metric,
        "scenario": _scenario(params or {}, baseline_params or {}),
        "baseline": baseline_summary and "given" or "none",
        "baseline_value": round(baseline_value, 6),
        "observed_value": round(observed, 6),
        "delta": round(change, 2),
        "direction": direction,
        "outcome": verdict,
        "horizon": int(summary.get("step_count",
                                   (params or {}).get("years", 0)) or 0),
        "population": summary.get("population", 0),
        "total_wealth": summary.get("total_wealth", 0),
        "deaths": summary.get("deaths_total", summary.get("deaths", 0)),
        "births": summary.get("births_total", summary.get("births", 0)),
        "avg_skill": summary.get("avg_skill", 0),
        "by_scale": summary.get("by_scale") or [],
        "claim_strength": summary.get("claim_strength", "HYPOTHESIS"),
        "signals": [s.get("signal_type") for s in (signals or [])],
    }
