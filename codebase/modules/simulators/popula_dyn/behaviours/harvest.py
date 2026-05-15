"""
behaviours/harvest.py

Harvest behavior - gather resources from land.
"""

from .base_behavior import BaseBehavior


class HarvestBehavior(BaseBehavior):
    """
    Harvest crops from land patch at current position.
    Replaces FarmerAgent.harvest()
    """

    behavior_name = "harvest"

    def execute(
        self,
        unit,
        world_state=None,
    ):
        world_state = world_state or {}
        params = world_state.get("params", {})
        grid = world_state.get("grid")
        position = unit.get_state("position")

        if grid is None or position is None:
            return {}

        skill = unit.get_state("skill", 0.5)
        max_harvest = skill * 3.0

        cell_contents = grid.get_cell_list_contents([position])
        land_patches = [
            c for c in cell_contents if c.unit_type == "land"
        ]

        if not land_patches:
            return {}

        patch = land_patches[0]
        current_crops = patch.get_resource("crops", 0)
        harvest_amount = min(current_crops, max_harvest)

        if harvest_amount <= 0:
            return {}

        patch.modify_resource("crops", -harvest_amount)
        unit.modify_resource("wealth", harvest_amount)

        return {
            "resource_updates": {
                "wealth": harvest_amount
            },
            "events": [
                {
                    "event_type": "harvested",
                    "amount": harvest_amount,
                }
            ]
        }