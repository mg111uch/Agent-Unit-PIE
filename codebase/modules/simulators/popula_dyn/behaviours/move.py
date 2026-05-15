"""
behaviours/move.py

Move behavior - spatial movement to adjacent cell.
"""

import numpy as np

from .base_behavior import BaseBehavior


class MoveBehavior(BaseBehavior):
    """
    Move to adjacent cell based on vision radius.
    Replaces FarmerAgent.move()
    """

    behavior_name = "move"

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

        vision = params.get("vision", 1)
        possible_moves = grid.get_neighborhood(
            position, moore=True, include_center=False, radius=vision
        )

        if not possible_moves:
            return {}

        rng = np.random.RandomState(world_state.get("seed", None))
        new_pos = possible_moves[rng.randint(len(possible_moves))]
        grid.move_agent(unit, new_pos)

        unit.set_state("position", new_pos)

        return {
            "events": [
                {
                    "event_type": "moved",
                    "from": position,
                    "to": new_pos,
                }
            ]
        }