"""SocietyState (FeatureIdeas #3, Phase A): policy-judgement outputs.

Causally consistent proxies from existing unit state/resources — no new
behaviours. Gini, age structure, food security, skilled share, health index
are computed live from `model.units`; land fertility/crops ground food.
"""
from __future__ import annotations
from typing import Any, Dict, List


def _gini(xs: List[float]) -> float:
    xs = sorted(x for x in xs if x >= 0)
    n = len(xs)
    if n < 2 or sum(xs) <= 0:
        return 0.0
    m = sum(xs) / n
    return sum(abs(a - b) for a in xs for b in xs) / (2 * n * n * m)


def society_state(model) -> Dict[str, Any]:
    """High-level society outputs on which policies are judged."""
    humans = [u for u in model.units.values()
              if u.unit_type == "human" and u.alive]
    lands = [u for u in model.units.values() if u.unit_type == "land"]
    pop = len(humans)
    ages = [float(u.get_state("age", 0) or 0) for u in humans]
    child = sum(1 for a in ages if a < 15) / pop if pop else 0.0
    elder = sum(1 for a in ages if a >= 50) / pop if pop else 0.0
    wealth = [u.get_resource("wealth", 0) for u in humans]
    skills = [float(u.get_state("skill", 0) or 0) for u in humans]
    crops = [u.get_resource("crops", 0) for u in lands]
    need = float(model.params.get("metabolism", 1)) * pop
    food = (sum(crops) / need) if need > 0 else 0.0
    deaths = getattr(model, "deaths_total", 0)
    heals = getattr(model, "successful_healings_total",
                    getattr(model, "successful_healings", 0))
    return {
        "population": pop,
        "age_structure": {"child": round(child, 3), "working": round(1 - child - elder, 3),
                          "elder": round(elder, 3)},
        "gini": round(_gini(wealth), 3),
        "wealth_total": round(sum(wealth), 1),
        "food_security": round(min(2.0, food), 3),
        "skilled_share": round(sum(1 for s in skills if s >= 0.5) / pop, 3) if pop else 0.0,
        "health_index": round(min(1.0, heals / max(1, deaths + heals)), 3),
        "epoch": getattr(model, "epoch", "Agricultural"),
    }
