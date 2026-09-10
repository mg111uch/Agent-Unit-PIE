"""behaviours/prospect.py: fertility-gradient prospecting move (no A* / GIS)."""

import numpy as np

from .base_behavior import BaseBehavior


class ProspectBehavior(BaseBehavior):
    """Hill-climb to richest visible land cell; else stay (move covers roam)."""

    behavior_name = "prospect"

    def execute(self, unit, world_state=None):
        world_state = world_state or {}
        params = world_state.get("params", {})
        grid = world_state.get("grid")
        model = world_state.get("model")
        position = unit.get_state("position")
        if grid is None or position is None:
            return {}
        if not params.get("prospect_enabled", True):
            return {}
        if unit.unit_type != "human" or not unit.alive:
            return {}
        rng = world_state.get("rng")
        if rng is None:
            rng = (model.random if model is not None and hasattr(model, "random")
                   else np.random.RandomState(world_state.get("seed", None)))
        if rng.random() >= params.get("prospect_prob", 0.5):
            return {}
        vision = params.get("vision", 2)
        threshold = params.get("prospect_threshold", 0.5)
        cells = grid.get_neighborhood(position, moore=True, include_center=True,
                                      radius=vision)

        def _crops(pos):
            for c in grid.get_cell_list_contents([pos]):
                if getattr(c, "unit_type", None) == "land":
                    return float(c.get_resource("crops", 0))
            return 0.0

        here = _crops(position)
        scored = [( _crops(p), p) for p in cells]
        best_val = max(s for s, _ in scored)
        if best_val - here < threshold:
            return {}
        tied = [p for s, p in scored if s == best_val]
        target = tied[rng.randint(len(tied))]
        if target == position:
            return {}
        grid.move_agent(unit, target)
        unit.set_state("position", target)
        return {
            "events": [{"event_type": "prospected", "from": list(position),
                        "to": list(target), "gain": round(best_val - here, 2)}],
            "signals": [{"signal_type": "mobility", "strength": 0.5,
                         "decay_rate": 0.05}],
        }
