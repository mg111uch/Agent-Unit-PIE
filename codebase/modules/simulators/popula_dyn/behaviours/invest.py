"""behaviours/invest.py — InvestBehavior: firm converts wealth to capital.

Return-intent only (model applies, no direct mutation). Fires when
wealth >= invest_threshold; moves invest_amount wealth -> capital_stock.
"""
from .base_behavior import BaseBehavior


class InvestBehavior(BaseBehavior):
    """Accumulate capital_stock from surplus wealth (one tranche per step)."""

    behavior_name = "invest"

    def execute(self, unit, world_state=None):
        wealth = unit.get_resource("wealth", 0)
        threshold = float(unit.get_state("invest_threshold", 20.0) or 0)
        amount = float(unit.get_state("invest_amount", 10.0) or 0)
        if amount <= 0 or wealth < threshold or wealth < amount:
            return {}
        stock = float(unit.get_state("capital_stock", 0) or 0)
        return {
            "state_updates": {"capital_stock": stock + amount},
            "resource_updates": {"wealth": -amount},
            "events": [{"event_type": "invested",
                        "firm_id": unit.unit_id, "amount": amount}],
        }
