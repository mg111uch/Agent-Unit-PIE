"""
behaviours/survival.py

Survival and energy regeneration behaviors.

- SurvivalBehavior: Death check
- RegenerateEnergyBehavior: Energy recovery
"""

import numpy as np

from .base_behavior import BaseBehavior


class SurvivalBehavior(BaseBehavior):
    """
    Check if the unit dies based on various factors.
    Replaces FarmerAgent.check_death()
    """

    behavior_name = "survival"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        world_state = world_state or {}
        params = world_state.get("params", {})
        model = world_state.get("model")

        age = unit.get_state("age", 0)
        wealth = unit.get_resource("wealth", 0)
        death_prob_modifier = unit.get_state("death_prob_modifier", 0.0)

        if not unit.alive:
            return {}

        death_prob = params.get("death_rate", 0.01)

        if wealth < 1.0:
            death_prob *= 5.0

        if age > 60:
            death_prob *= 1.5

        if age > params.get("max_age", 80):
            death_prob = 1.0

        death_prob += death_prob_modifier
        death_prob = max(0.0, death_prob)

        rng = np.random.RandomState(world_state.get("seed", None))
        if rng.random() < death_prob:
            unit.alive = False

            if model:
                if hasattr(model, "deaths"):
                    model.deaths += 1
                else:
                    model.deaths = 1

            return {
                "events": [
                    {
                        "event_type": "death",
                        "reason": "age_or_starvation",
                    }
                ]
            }

        return {}


class RegenerateEnergyBehavior(BaseBehavior):
    """Energy regeneration."""

    behavior_name = "regenerate_energy"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        return {
            "resource_updates": {
                "energy": 1.0,
            },
            "signals": [
                {
                    "signal_type": "energy_recovery",
                    "strength": 0.5,
                    "decay_rate": 0.02,
                }
            ],
        }