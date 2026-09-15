"""Contrast lab: ONE policy x Kanpur x Delhi + Capability Vector (Phase 6).

Vector dims come from existing sim columns ONLY (society + branch fiscal):
economic_output, working_population, real_income_proxy, inequality_gini,
fiscal_cost, food_security, health_index, skilled_share. GDP-alone (wealth)
is 1 of 8 dims and never decides. Pareto verdict: universal /
city-specific / null.
"""
from __future__ import annotations

from typing import Any, Dict

DIMS = (
    "economic_output",
    "working_population",
    "real_income_proxy",
    "inequality_gini",
    "fiscal_cost",
    "food_security",
    "health_index",
    "skilled_share",
)
LOWER_BETTER = {"inequality_gini", "fiscal_cost"}


def score_vector(society: Dict[str, Any], fiscal: float) -> Dict[str, float]:
    pop = max(1, int(society.get("population", 0)))
    wealth = float(society.get("wealth_total", 0))
    return {
        "economic_output": round(wealth, 1),
        "working_population": round(pop * float(
            society.get("age_structure", {}).get("working", 0))),
        "real_income_proxy": round(wealth / pop, 3),
        "inequality_gini": float(society.get("gini", 0)),
        "fiscal_cost": round(float(fiscal), 1),
        "food_security": float(society.get("food_security", 0)),
        "health_index": float(society.get("health_index", 0)),
        "skilled_share": float(society.get("skilled_share", 0)),
    }


def compare_vectors(
    base: Dict[str, float], pol: Dict[str, float]
) -> Dict[str, Any]:
    deltas = {d: round(pol[d] - base[d], 3) for d in DIMS}
    improved = sum(
        (deltas[d] < 0) if d in LOWER_BETTER else (deltas[d] > 0)
        for d in DIMS
    )
    gini_ok = deltas["inequality_gini"] <= 0.02
    return {"deltas": deltas, "improved_dims": improved, "gini_ok": gini_ok}


def run_contrast(
    policy: Dict[str, Any],
    city_fields: Dict[str, Dict[str, Dict[str, Any]]],
    seed: int = 7,
    years: int = 12,
) -> Dict[str, Any]:
    """Calibrate -> baseline+branch per city. Returns table + verdict."""
    from modules.simulators.popula_dyn.core.simulation_model import (
        SimulationModel as _SM)
    from modules.simulators.popula_dyn.core.scenarios import branch as _br
    from modules.digital_twins import calibration_engine as _ce
    cities = {}
    for city_id, fields in city_fields.items():
        cal = _ce.calibrate(fields, seed=seed, years=years)
        base = dict(cal["params"])
        base["grid_width"] = base["grid_height"] = 20
        out = _br(_SM, base, [dict(policy)])
        rows = {r["name"]: r for r in out["rows"]}
        bkey = "baseline:no_intervention"
        pkey = f"policy:{policy['mechanism']}"
        bv = score_vector(rows[bkey]["society"], rows[bkey]["fiscal"])
        pv = score_vector(rows[pkey]["society"], rows[pkey]["fiscal"])
        cities[city_id] = {"baseline": bv, "policy": pv,
                           "cmp": compare_vectors(bv, pv)}
    gains = {c: (v["cmp"]["improved_dims"] >= 5 and v["cmp"]["gini_ok"])
             for c, v in cities.items()}
    n = sum(gains.values())
    verdict = ("universal" if n == len(cities) and n > 0
               else "city-specific" if n == 1 else "null")
    lines = ["city | " + " | ".join(DIMS) + " | improved"]
    for c, v in cities.items():
        lines.append(c + " base | " + " | ".join(
            str(v["baseline"][d]) for d in DIMS))
        lines.append(c + " pol  | " + " | ".join(
            str(v["policy"][d]) for d in DIMS)
            + f" | {v['cmp']['improved_dims']}/8")
    return {"cities": cities, "gains": gains, "verdict": verdict,
            "table": "\n".join(lines)}
