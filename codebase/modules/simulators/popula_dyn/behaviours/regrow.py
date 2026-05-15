"""
behaviours/regrow.py

Regrow behavior - regenerate resources over time.
"""

from .base_behavior import BaseBehavior


class RegrowBehavior(BaseBehavior):
    """
    Regrow crops towards base fertility.
    Replaces LandPatch.step()
    """

    behavior_name = "regrow"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        fertility = unit.get_state("fertility", 5.0)
        current_crops = unit.get_resource("crops", fertility)

        if current_crops >= fertility:
            return {}

        regrowth_rate = 0.1
        new_crops = min(
            fertility, current_crops + (fertility - current_crops) * regrowth_rate
        )

        unit.set_state("current_crops", new_crops)

        return {
            "resource_updates": {
                "crops": new_crops - current_crops
            },
            "events": [
                {
                    "event_type": "regrown",
                    "amount": new_crops,
                }
            ]
        }