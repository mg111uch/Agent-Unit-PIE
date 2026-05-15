"""
behaviours/consume.py

Resource consumption behaviors.

- ConsumeResourcesBehavior: Generic resource decay
- ConsumeMetabolismBehavior: Food consumption based on metabolism
"""

from .base_behavior import BaseBehavior


class ConsumeResourcesBehavior(BaseBehavior):
    """Generic resource consumption - decay all resources."""

    behavior_name = "consume_resources"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        resource_updates = {}

        for resource_name in list(unit.resources.keys()):
            value = float(unit.resources.get(resource_name, 0))
            if value > 0:
                resource_updates[resource_name] = -0.1

        return {
            "resource_updates": resource_updates,
            "events": [
                {
                    "event_type": "resource_consumption",
                }
            ],
        }


class ConsumeMetabolismBehavior(BaseBehavior):
    """
    Consume food based on metabolism.
    Replaces FarmerAgent.consume()
    """

    behavior_name = "consume_metabolism"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        world_state = world_state or {}
        params = world_state.get("params", {})
        metabolism = params.get("metabolism", 1.0)

        wealth = unit.get_resource("wealth", 0)
        new_wealth = max(0, wealth - metabolism)

        unit.set_state("wealth", new_wealth)

        return {
            "resource_updates": {
                "wealth": -metabolism
            }
        }