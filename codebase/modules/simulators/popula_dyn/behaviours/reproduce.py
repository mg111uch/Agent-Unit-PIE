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
        fertile_min = params.get("fertile_min_age", 18)
        fertile_max = params.get("fertile_max_age", 50)
        vision = params.get("vision", 2)

        if age < fertile_min or age > fertile_max:
            return {}

        neighbors = grid.get_neighbors(
            position, moore=True, radius=vision, include_center=False
        )
        potential_partners = [
            n
            for n in neighbors
            if n.unit_type == "human"
            and n.get_state("gender") != gender
            and n.alive
            and fertile_min <= n.get_state("age", 0) <= fertile_max
        ]

        if not potential_partners:
            return {}

        rng = np.random.RandomState(world_state.get("seed", None))
        if rng.random() >= params.get("birth_rate", 0.005):
            return {}

        partner = rng.choice(potential_partners)
        child_skill = (unit.get_state("skill", 0.5) + partner.get_state("skill", 0.5)) / 2

        child_data = {
            "unit_type": "human",
            "age": 0,
            "gender": rng.choice(["M", "F"]),
            "skill": child_skill,
            "wealth": 5.0,
            "alive": True,
        }

        model.add_unit(child_data)

        return {
            "events": [
                {
                    "event_type": "birth",
                    "parent_id": unit.unit_id,
                    "child_id": child_data.get("unit_id"),
                }
            ]
        }