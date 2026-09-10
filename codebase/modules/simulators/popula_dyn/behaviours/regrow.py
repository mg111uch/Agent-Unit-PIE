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
        world_state = world_state or {}
        params = world_state.get("params", {})
        grid = world_state.get("grid")
        fertility = unit.get_state("fertility", 5.0)
        current_crops = unit.get_resource("crops", fertility)

        # carrying capacity: crowded cells regrow toward a capped ceiling
        cap = params.get("carrying_capacity_per_cell", 4)
        position = unit.get_state("position")
        capped = False
        if grid is not None and position is not None:
            humans = sum(1 for c in grid.get_cell_list_contents([position])
                         if getattr(c, "unit_type", None) == "human" and c.alive)
            if humans > cap:
                fertility = fertility * cap / humans
                capped = True

        if current_crops >= fertility:
            if capped:
                return {"events": [{"event_type": "capacity_capped"}],
                        "signals": [{"signal_type": "resource_scarcity",
                                     "strength": 0.5, "decay_rate": 0.05}]}
            return {}

        regrowth_rate = 0.1
        new_crops = min(
            fertility, current_crops + (fertility - current_crops) * regrowth_rate
        )

        out = {
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
        if capped:
            out["events"].append({"event_type": "capacity_capped"})
            out["signals"] = [{"signal_type": "resource_scarcity",
                               "strength": 0.5, "decay_rate": 0.05}]
        return out