"""core/scarcity.py: supply-demand scarcity index + barter pricing.

Pure helpers, no RNG (deterministic). Single source of truth shared by
popula_dyn behaviours and the economy module (`scoring.barter_price`).
"""

from __future__ import annotations

from typing import Any, Dict


def _clamp01(v: Any) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def food_per_capita(model: Any) -> float:
    """Total land crops per living human (supply side)."""
    crops = sum(float(u.get_resource("crops", 0) or 0)
                for u in model.units.values() if u.unit_type == "land")
    return crops / max(1, model.get_population_count())


def scarcity_index(model: Any, params: Dict[str, Any]) -> float:
    """Global 0..1 scarcity: worst of food shortfall vs baseline and
    last-step carrying-capacity pressure (regrow caps)."""
    base = max(1e-9, float(params.get("scarcity_food_baseline", 5.0)))
    s_food = 1.0 - food_per_capita(model) / base
    land = sum(1 for u in model.units.values() if u.unit_type == "land")
    s_cap = (model.capacity_capped / max(1, land)) if land else 0.0
    return _clamp01(max(s_food, s_cap))


def local_scarcity(grid: Any, position: tuple, params: Dict[str, Any],
                   radius: int = 2) -> float:
    """Neighbourhood 0..1 scarcity: local crops per local human vs baseline."""
    base = max(1e-9, float(params.get("scarcity_food_baseline", 5.0)))
    cells = grid.get_neighborhood(position, moore=True, include_center=True,
                                  radius=radius or 2)
    contents = grid.get_cell_list_contents(cells)
    crops = sum(float(c.get_resource("crops", 0) or 0)
                for c in contents if getattr(c, "unit_type", None) == "land")
    humans = sum(1 for c in contents
                 if getattr(c, "unit_type", None) == "human" and c.alive)
    return _clamp01(1.0 - (crops / max(1, humans)) / base)


def barter_price(base: Any, scarcity: Any, sensitivity: Any = 1.0) -> float:
    """Scarcity-priced exchange value, no hardcoded currency.

    price = base * (1 + sensitivity * scarcity); scarcity 0 → base rate.
    """
    try:
        s = _clamp01(scarcity)
        return round(float(base) * (1.0 + float(sensitivity) * s), 2)
    except (TypeError, ValueError):
        return round(float(base), 2)
