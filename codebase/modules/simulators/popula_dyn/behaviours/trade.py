"""
behaviours/trade.py

Trade behaviors - exchange resources between units.

- TradeBehavior: Generic trading
- TradeBehaviorAg: Agricultural trading (replaces TraderAgent)
"""

import numpy as np

from .base_behavior import BaseBehavior


class TradeBehavior(BaseBehavior):
    """Generic trading behavior."""

    behavior_name = "trade"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        capital = unit.get_resource("capital", 0)

        if capital <= 0:
            return {
                "signals": [
                    {
                        "signal_type": "economic_stress",
                        "strength": 0.7,
                        "decay_rate": 0.03,
                    }
                ]
            }

        return {
            "resource_updates": {
                "capital": 2.0,
            },
            "events": [
                {
                    "event_type": "trade_completed",
                }
            ],
            "signals": [
                {
                    "signal_type": "market_activity",
                    "strength": 0.6,
                    "decay_rate": 0.04,
                }
            ],
        }


class TradeBehaviorAg(BaseBehavior):
    """
    Facilitate trade between agents.
    Replaces TraderAgent.step() - renamed to avoid conflict.
    """

    behavior_name = "trade_ag"

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

        trade_margin = unit.get_state("trade_margin", 0.05)
        trade_range = unit.get_state("trade_range", 2)

        neighbors = grid.get_neighbors(
            position, moore=True, radius=trade_range, include_center=False
        )
        all_agents = [
            n
            for n in neighbors
            if n.unit_id != unit.unit_id and hasattr(n, "get_resource")
        ]

        if len(all_agents) < 2:
            return {}

        rng = np.random.RandomState(world_state.get("seed", None))
        sorted_agents = sorted(
            all_agents, key=lambda a: a.get_resource("wealth", 0), reverse=True
        )
        richest = sorted_agents[0]
        poorest = sorted_agents[-1]

        richest_wealth = richest.get_resource("wealth", 0)
        trade_amount = min(richest_wealth * 0.1, 5.0)

        if trade_amount <= 0:
            return {}

        margin = trade_amount * trade_margin
        transfer = trade_amount - margin

        richest.modify_resource("wealth", -trade_amount)
        poorest.modify_resource("wealth", transfer)
        unit.modify_resource("wealth", margin)

        if model:
            if hasattr(model, "trades_executed"):
                model.trades_executed += 1
            if hasattr(model, "wealth_traded"):
                model.wealth_traded += trade_amount

        return {
            "resource_updates": {
                "wealth": margin
            },
            "events": [
                {
                    "event_type": "trade_executed",
                    "from": richest.unit_id,
                    "to": poorest.unit_id,
                    "amount": transfer,
                }
            ]
        }