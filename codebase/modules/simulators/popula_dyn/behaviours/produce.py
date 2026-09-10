"""
behaviours/produce.py

Produce behavior - create tools/goods for trade.
"""

import numpy as np

from .base_behavior import BaseBehavior
from modules.simulators.popula_dyn.core.scarcity import barter_price, local_scarcity


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

        rng = world_state.get("rng")
        if rng is None:
            rng = model.random if model is not None and hasattr(model, "random") else None
        if rng is None:
            seed = world_state.get("seed")
            if seed is None:
                raise ValueError("produce needs deterministic rng: pass world_state['rng']")
            rng = np.random.RandomState(seed)
        if rng.random() < production_rate:
            inventory += 1

        neighbors = grid.get_neighbors(position, moore=True, radius=1, include_center=False)
        # barter market: tools cost more when local food is scarce
        sc = local_scarcity(grid, position, params, 1)
        price = barter_price(tool_cost, sc, params.get("barter_sensitivity", 1.0))
        potential_customers = [
            n
            for n in neighbors
            if n.unit_type == "human"
            and n.alive
            and n.get_resource("wealth", 0) >= price
        ]

        if inventory <= 0 or not potential_customers:
            # return-intent: model owns inventory + tools_produced counting.
            # Craft-only (no sale yet) still reports tool_produced, as before.
            if inventory > unit.get_state("inventory", 0):
                return {"state_updates": {"inventory": inventory},
                        "events": [{"event_type": "tool_produced"}]}
            return {}

        customer = potential_customers[rng.randint(len(potential_customers))]
        # return-intent: model applies customer effects + own inventory/wealth
        return {
            "state_updates": {"inventory": inventory - 1},
            "resource_updates": {
                "wealth": price
            },
            "unit_effects": [
                {
                    "unit_id": customer.unit_id,
                    "state_updates": {
                        "skill": customer.get_state("skill", 0.5) + tool_quality
                    },
                    "resource_updates": {"wealth": -price},
                }
            ],
            "events": [
                {
                    "event_type": "tool_produced",
                    "customer_id": customer.unit_id,
                    "price": price,
                }
            ]
        }