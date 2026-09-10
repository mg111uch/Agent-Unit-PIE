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

        if wealth <= 0:
            death_prob *= 8.0
        elif wealth < 1.0:
            death_prob *= 5.0
        elif wealth < 2.0:
            death_prob *= 2.0

        # adaptability trait buffers hardship mortality (mirror fertility scaling)
        if wealth < 2.0:
            adapt = max(0.5, min(1.5, float(unit.get_state("adaptability", 1.0))))
            death_prob /= adapt

        # individual variation: per-unit drawn lifespan (falls back to max_age)
        lifespan = unit.get_state("lifespan", params.get("max_age", 60))
        if age > lifespan - 10:
            death_prob *= 1.5

        if age > lifespan:
            death_prob = 1.0

        death_prob += death_prob_modifier
        # scarcity↔vital-rates: dear food raises mortality (mirror adaptability)
        sc = world_state.get("scarcity", 0.0)
        try:
            death_prob *= 1.0 + float(params.get("scarcity_mortality", 1.0)) * float(sc)
        except (TypeError, ValueError):
            pass
        death_prob = max(0.0, death_prob)

        rng = world_state.get("rng")
        if rng is None:
            rng = model.random if model is not None and hasattr(model, "random") else np.random.RandomState(world_state.get("seed", None))
        if rng.random() < death_prob:
            unit.alive = False
            # categorized cause (policy analysis: what kills units?)
            if wealth <= 0:
                reason = "starvation"
            elif age > unit.get_state("lifespan", params.get("max_age", 60)):
                reason = "old_age"
            else:
                reason = "hazard"
            return {
                "events": [
                    {
                        "event_type": "death",
                        "reason": reason,
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