"""behaviours/hire.py — HireBehavior: firm hires nearby willing humans.

Return-intent only (model applies, no direct mutation). Willing =
skill>=min_skill and wealth<wage. Budget = min(wealth, payroll_fund).
"""
from .base_behavior import BaseBehavior


class HireBehavior(BaseBehavior):
    """Hire up to max_hires_per_step affordable workers (deterministic pick)."""

    behavior_name = "hire"

    def execute(self, unit, world_state=None):
        world_state = world_state or {}
        grid = world_state.get("grid")
        if grid is None:
            return {}
        wage = float(unit.get_state("wage_offer", 5.0) or 0)
        min_skill = float(unit.get_state("min_skill", 0.3) or 0)
        max_h = int(unit.get_state("max_hires_per_step", 2) or 0)
        if wage <= 0 or max_h <= 0:
            return {}
        fund = min(unit.get_resource("wealth", 0),
                   unit.get_state("payroll_fund", 0) or 0)
        afford = min(max_h, int(fund // wage))
        if afford <= 0:
            return {}
        radius = (unit.get_state("hire_radius", None)
                  or world_state.get("params", {}).get("vision", 2))
        position = unit.get_state("position")
        cands = [n for n in grid.get_neighbors(
            position, moore=True, radius=radius, include_center=False)
            if n is not unit and n.unit_type == "human" and n.alive
            and n.get_state("employer", None) is None
            and float(n.get_state("skill", 0) or 0) >= min_skill
            and n.get_resource("wealth", 0) < wage]
        if not cands:
            return {}
        hired = sorted(cands, key=lambda n: n.unit_id)[:afford]
        return {
            "resource_updates": {"wealth": -wage * len(hired)},
            "unit_effects": [
                {"unit_id": w.unit_id,
                 "state_updates": {"employer": unit.unit_id},
                 "resource_updates": {"wealth": wage}} for w in hired],
            "events": [{"event_type": "hired", "worker_id": w.unit_id,
                        "firm_id": unit.unit_id, "wage": wage} for w in hired],
        }
