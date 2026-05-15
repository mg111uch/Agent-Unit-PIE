"""
behaviours/produce.py

Produce behavior - create tools/goods for trade.
"""

import numpy as np

from .base_behavior import BaseBehavior


class ProduceBehavior(BaseBehavior):
    """
    Produce tools and sell them to nearby farmers.
    Replaces ToolmakerAgent.step()
    """

    behavior_name = "produce"

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

        production_rate = unit.get_state("tool_production_rate", 0.1)
        tool_quality = unit.get_state("tool_quality", 0.1)
        tool_cost = unit.get_state("tool_cost", 1.0)
        inventory = unit.get_state("inventory", 0)

        rng = np.random.RandomState(world_state.get("seed", None))
        if rng.random() < production_rate:
            inventory += 1
            unit.set_state("inventory", inventory)

            if model and hasattr(model, "tools_produced"):
                model.tools_produced += 1

        neighbors = grid.get_neighbors(position, moore=True, radius=1, include_center=False)
        potential_customers = [
            n
            for n in neighbors
            if n.unit_type == "human"
            and n.alive
            and n.get_resource("wealth", 0) >= tool_cost
        ]

        if inventory <= 0 or not potential_customers:
            return {}

        customer = rng.choice(potential_customers)
        customer.modify_resource("wealth", -tool_cost)
        customer.set_state(
            "skill", customer.get_state("skill", 0.5) + tool_quality
        )
        unit.modify_resource("wealth", tool_cost)
        unit.set_state("inventory", inventory - 1)

        return {
            "resource_updates": {
                "wealth": tool_cost
            },
            "events": [
                {
                    "event_type": "tool_produced",
                    "customer_id": customer.unit_id,
                }
            ]
        }