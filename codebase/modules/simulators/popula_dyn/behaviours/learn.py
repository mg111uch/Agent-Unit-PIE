"""
behaviours/learn.py

Learn behavior - knowledge/intelligence growth.
"""

from .base_behavior import BaseBehavior


class LearnBehavior(BaseBehavior):
    """Learning behavior - increase intelligence."""

    behavior_name = "learn"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        intelligence = unit.get_state("intelligence", 0)

        return {
            "state_updates": {
                "intelligence": intelligence + 0.1
            },
            "signals": [
                {
                    "signal_type": "knowledge_growth",
                    "strength": 0.4,
                    "decay_rate": 0.01,
                }
            ],
            "events": [
                {
                    "event_type": "learning_progress",
                }
            ],
        }