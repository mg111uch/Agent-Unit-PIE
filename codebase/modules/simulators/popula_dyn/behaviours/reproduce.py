"""
behaviours/reproduce.py

Reproduce behavior - create new units.
"""

import numpy as np

from .base_behavior import BaseBehavior


class ReproduceBehavior(BaseBehavior):
    """
    Attempt to mate with a nearby fertile partner.
    Replaces FarmerAgent.mate()
    """

    behavior_name = "reproduce"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        world_state = world_state or {}
        params = world_state.get("params", {})
        grid = world_state.get("grid")
        model = world_state.get("model")
        position = unit.get_state("position")

        if grid is None:
            return {}

        age = unit.get_state("age", 0)
        gender = unit.get_state("gender", "M")
        fertile_min = params.get("fertile_min_age", 15)
        fertile_max = params.get("fertile_max_age", 50)
        vision = params.get("vision", 2)
        mate_radius = params.get("mate_radius", vision)
        mate_global_fallback = params.get("mate_global_fallback", True)
        require_opposite_gender = params.get("require_opposite_gender", True)

        if age < fertile_min or age > fertile_max:
            return {}

        neighbors = grid.get_neighbors(
            position, moore=True, radius=mate_radius, include_center=True
        )
        def _ok(n):
            gender_ok = (n.get_state("gender") != gender) if require_opposite_gender else True
            return (
                n is not unit
                and n.unit_type == "human"
                and n.alive
                and gender_ok
                and fertile_min <= n.get_state("age", 0) <= fertile_max
            )
        potential_partners = [n for n in neighbors if _ok(n)]
        if not potential_partners and mate_global_fallback and model is not None:
            try:
                potential_partners = [n for n in model.units.values() if _ok(n)]
            except Exception:
                pass

        if not potential_partners:
            return {}

        rng = model.random if model is not None and hasattr(model, "random") else np.random.RandomState(world_state.get("seed", None))
        if rng.random() >= params.get("birth_rate", 0.04):
            return {}

        partner = potential_partners[rng.randint(len(potential_partners))]
        child_skill = (unit.get_state("skill", 0.5) + partner.get_state("skill", 0.5)) / 2

        # return-intent: model owns spawn (deterministic id + add_unit)
        child_data = {
            "unit_type": "human",
            "position": position,
            "behaviors": ["move", "harvest", "consume_metabolism", "reproduce", "survival"],
            "state": {"age": 0, "gender": rng.choice(["M", "F"]), "skill": child_skill, "position": position},
            "resources": {"wealth": 5.0},
            "alive": True,
        }

        return {
            "spawn": child_data,
            "events": [
                {
                    "event_type": "birth",
                    "parent_id": unit.unit_id,
                }
            ]
        }