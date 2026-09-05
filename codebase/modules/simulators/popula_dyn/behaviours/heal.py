"""
behaviours/heal.py

Heal behavior - restore health to nearby units.
"""

import numpy as np

from .base_behavior import BaseBehavior


class HealBehavior(BaseBehavior):
    """
    Attempt to heal nearby farmers.
    Replaces HealerAgent.step()
    """

    behavior_name = "heal"

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

        healing_rate = unit.get_state("healing_rate", 0.1)
        healing_cost = unit.get_state("healing_cost", 0.5)

        neighbors = grid.get_neighbors(position, moore=True, radius=1, include_center=False)
        potential_patients = [
            n
            for n in neighbors
            if n.unit_type == "human"
            and n.alive
            and n.get_resource("wealth", 0) >= healing_cost
        ]

        if not potential_patients:
            return {}

        rng = world_state.get("rng")
        if rng is None:
            rng = model.random if model is not None and hasattr(model, "random") else None
        if rng is None:
            seed = world_state.get("seed")
            if seed is None:
                raise ValueError("heal needs deterministic rng: pass world_state['rng']")
            rng = np.random.RandomState(seed)
        if rng.random() >= healing_rate:
            return {}

        patient = potential_patients[rng.randint(len(potential_patients))]
        patient.set_state("death_prob_modifier", -0.5)
        patient.modify_resource("wealth", -healing_cost)
        unit.modify_resource("wealth", healing_cost)

        if model and hasattr(model, "successful_healings"):
            model.successful_healings += 1

        return {
            "resource_updates": {
                "wealth": healing_cost
            },
            "events": [
                {
                    "event_type": "healed",
                    "patient_id": patient.unit_id,
                }
            ]
        }