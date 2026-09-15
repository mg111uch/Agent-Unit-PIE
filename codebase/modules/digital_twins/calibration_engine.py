"""Twin CityState -> popula_dyn params (Phase 5 calibration).

Mapped (well-understood only): population -> initial_pop (1 agent : 20k
people, capped for smoke); literacy -> specialist seed share (documented
proxy for skill share). Placeholder fields (conf<=0.35) enter as
wide-prior RANGES, never point values; water/energy/air stay unmapped
(no honest param exists). Reuses popula_dyn constants; no fork.
"""
from __future__ import annotations

from typing import Any, Dict

POP_SCALE = 20000
POP_CAP = 400
POP_MIN = 50


def calibrate(
    fields: Dict[str, Dict[str, Any]],
    seed: int = 7,
    years: int = 14,
) -> Dict[str, Any]:
    pop = float(fields["population"]["value"])
    lit = float(fields["literacy_rate"]["value"])
    init_pop = min(POP_CAP, max(POP_MIN, round(pop / POP_SCALE)))
    n_spec = max(1, round(init_pop * lit * 0.05))
    params = {
        "initial_pop": init_pop,
        "initial_toolmakers": n_spec,
        "initial_healers": n_spec,
        "initial_traders": max(1, n_spec // 2),
        "seed": seed,
        "years": years,
    }
    priors = {
        "toolmaker_production_rate": [0.05, 0.20],  # industrial_capacity placeholder
        "birth_rate": [0.03, 0.05],  # employment placeholder
    }
    params["toolmaker_production_rate"] = sum(priors["toolmaker_production_rate"]) / 2
    params["birth_rate"] = sum(priors["birth_rate"]) / 2
    mapping = {
        "population->initial_pop": f"{pop:.0f}/{POP_SCALE} capped {POP_CAP}",
        "literacy_rate->specialists": f"proxy share {lit:.2f} x5%",
        "industrial_capacity->toolmaker_production_rate": "RANGE midpoint, flagged",
        "employment->birth_rate": "RANGE midpoint, flagged",
    }
    unmapped = ["water_supply_mld", "energy_reliability", "air_quality_pm25"]
    return {"params": params, "mapping": mapping, "priors": priors,
            "unmapped": unmapped, "provenance": {
                f: {"source": v.get("source"), "confidence": v.get("confidence")}
                for f, v in fields.items()}}


def baseline_error(
    society: Dict[str, Any], pop_anchor_2025: float, literacy: float
) -> Dict[str, Any]:
    """OOS-style check: fit on 2011 init, error vs 2025 anchors (scaled)."""
    expect_pop = pop_anchor_2025 / POP_SCALE
    got_pop = float(society.get("population", 0))
    got_skill = float(society.get("skilled_share", 0) or 0)
    return {
        "population_rel_err": round((got_pop - expect_pop) / max(1, expect_pop), 3),
        "skilled_share_abs_err": round(got_skill - literacy, 3),
        "endpoint": {"pop": got_pop, "expected_scaled": round(expect_pop, 1)},
    }
