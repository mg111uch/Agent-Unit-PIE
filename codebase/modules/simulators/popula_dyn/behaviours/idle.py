"""
behaviours/idle.py

Idle behavior - no action taken.
"""

from .base_behavior import BaseBehavior


class IdleBehavior(BaseBehavior):
    """Unit remains idle."""

    behavior_name = "idle"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        return {
            "events": [
                {
                    "event_type": "idle",
                    "description": f"{unit.unit_id} remained idle",
                }
            ]
        }