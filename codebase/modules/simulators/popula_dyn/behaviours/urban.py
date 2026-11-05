"""behaviours/urban.py — urban labour market (SIM-03 Phase A).

Two return-intent behaviours, no direct cross-unit mutation:

- WorkBehavior   worker finds a firm, receives a wage, firm pays it
- OperateBehavior firm turns capital + labour + power reliability into output

Wages are paid by the worker behaviour (it debits the employer through a
`unit_effects` entry), so one step has exactly one wage flow.
"""
from .base_behavior import BaseBehavior


def _clamp(v, lo, hi):
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return lo


def _firms(model):
    return [u for u in model.units.values()
            if u.unit_type == "firm" and u.alive]


def _employee_map(model):
    """One scan per step: firm_id -> [worker ids], updated as workers hire."""
    step = getattr(model, "step_count", 0)
    mapping = getattr(model, "_emp_map", None)
    if mapping is None or getattr(model, "_emp_step", None) != step:
        mapping = {}
        for u in model.units.values():
            if u.unit_type == "human" and u.alive:
                employer = u.get_state("employer")
                if employer:
                    mapping.setdefault(employer, []).append(u.unit_id)
        model._emp_map = mapping
        model._emp_step = step
    return mapping


def _employee_counts(model):
    return {firm: len(ids) for firm, ids in _employee_map(model).items()}


def _employees(model, firm_id):
    return len(_employee_map(model).get(firm_id, ()))


def _dist(firm, position):
    pos = firm.get_state("position") or (0, 0)
    return ((pos[0] - position[0]) ** 2 + (pos[1] - position[1]) ** 2,
            firm.unit_id)


def _nearest_firm(unit, model, grid, radius):
    """Nearest firm that still has a vacancy (local first, then global).

    Ties break on `unit_id`, and the local pick is the true nearest, so the
    hire does not depend on grid dict order or model shuffle order.
    """
    position = unit.get_state("position")
    firms = [f for f in _firms(model)
             if _employees(model, f.unit_id)
             < int(f.get_state("max_workers", 20) or 20)
             and float(f.get_resource("wealth", 0) or 0)
             >= 0.5 * float(f.get_state("wage_offer", 2.0) or 2.0)]
    if not firms or position is None:
        return None
    if grid is not None:
        cells = grid.get_neighborhood(position, moore=True,
                                      include_center=True, radius=radius)
        local = [f for f in grid.get_cell_list_contents(cells)
                 if f.unit_type == "firm" and f.alive and f in firms]
        if local:
            return min(local, key=lambda f: _dist(f, position))
    return min(firms, key=lambda f: _dist(f, position))


class WorkBehavior(BaseBehavior):
    """Sell one step of labour to a firm that can still pay the wage."""

    behavior_name = "work"

    def execute(self, unit, world_state=None):
        world_state = world_state or {}
        params = world_state.get("params", {})
        model = world_state.get("model")
        if model is None:
            return {}
        if float(unit.get_state("age", 0) or 0) < float(
                params.get("min_working_age", 15) or 15):
            return {"state_updates": {"employer": "", "wage": 0.0}}
        base_radius = int(params.get("job_search_radius", 4) or 4)
        congestion = float(getattr(model, "traffic_congestion", 0.0) or 0.0)
        radius = max(1, base_radius - int(congestion * 3))
        employer = model.units.get(unit.get_state("employer") or "")
        if employer is None or not employer.alive or employer.unit_type != "firm":
            employer = _nearest_firm(unit, model, world_state.get("grid"), radius)
        if employer is None:
            return {"state_updates": {"employer": "", "wage": 0.0},
                    "events": [{"event_type": "unemployed"}]}

        employed = _employees(model, employer.unit_id)
        cap = int(employer.get_state("max_workers", 20) or 20)
        already = unit.get_state("employer") == employer.unit_id
        if (not already and employed >= cap):
            return {"state_updates": {"employer": "", "wage": 0.0},
                    "events": [{"event_type": "unemployed"}]}

        skill = _clamp(unit.get_state("skill", 0.5), 0.0, 1.0)
        base_wage = params.get(
            "wage_offer", employer.get_state("wage_offer", 2.0))
        wage = float(base_wage) * (0.5 + skill)
        if float(employer.get_resource("wealth", 0)) < wage:
            return {"state_updates": {"wage": 0.0},
                    "events": [{"event_type": "unemployed",
                                "firm_id": employer.unit_id}]}

        gain = float(params.get("skill_gain", 0.01) or 0.0)
        if not already:
            mapping = _employee_map(model)
            mapping.setdefault(employer.unit_id, []).append(unit.unit_id)
        return {
            "state_updates": {"employer": employer.unit_id,
                              "wage": round(wage, 3),
                              "skill": round(min(1.0, skill + gain), 3)},
            "resource_updates": {"wealth": round(wage, 3)},
            "unit_effects": [{"unit_id": employer.unit_id,
                              "resource_updates": {"wealth": round(-wage, 3)}}],
            "events": [{"event_type": "wage_paid", "amount": round(wage, 3),
                        "firm_id": employer.unit_id,
                        "worker_id": unit.unit_id}],
        }


class OperateBehavior(BaseBehavior):
    """Produce output from capital and employed labour; reinvest a share."""

    behavior_name = "operate"

    def execute(self, unit, world_state=None):
        world_state = world_state or {}
        params = world_state.get("params", {})
        model = world_state.get("model")
        if model is None:
            return {}

        labour = _employees(model, unit.unit_id)
        capital = max(0.0, float(unit.get_state("capital_stock", 0) or 0))
        productivity = float(unit.get_state("productivity", 1.0) or 1.0) \
            * float(params.get("firm_productivity", 1.0) or 1.0) \
            * (float(params.get("floor_space", 1.0) or 1.0) ** 0.2)
        reliability = _clamp(getattr(
            model, "power_reliability_actual",
            params.get("power_reliability", 0.9)), 0.0, 1.0)
        water_supply = _clamp(getattr(model, "water_supply", 1.0), 0.0, 1.0)
        scale = float(params.get("output_scale", 3.0) or 3.0)
        output = productivity * (capital ** 0.3) * (labour ** 0.7) \
            * reliability * (0.6 + 0.4 * water_supply) * scale
        price = float(unit.get_state("price", 2.0) or 2.0)
        transport = float(getattr(
            model, "transport_cost_actual",
            params.get("transport_cost", unit.get_state("transport_cost", 1.0))))
        base_transport = float(params.get("transport_cost", 1.0) or 1.0)
        water = labour * float(params.get("water_price", 1.0) or 0.0) * 0.05
        tax = output * price * float(params.get("property_tax_rate", 0.0) or 0.0)
        fuel = max(0.0, transport - base_transport) * output * 0.1
        revenue = output * (price - 0.1 * transport) - water - tax

        invest = 0.0
        if labour and revenue > 0:
            invest = min(float(unit.get_state("invest_amount", 5.0) or 0.0),
                         revenue * 0.3)
        # Profit pass-through (SIM-03 C): without it, utility gains stay in
        # firm wealth and welfare falls as Gini rises. Declared here, paid at
        # `finish_step`: paying mid-step drains the cash that hires the rest
        # of the step (Kanpur transport inversion).
        profit = revenue - invest
        share = _clamp(params.get("profit_share", 0.1), 0.0, 1.0)
        workers = _employee_map(model).get(unit.unit_id, [])
        paid = 0.0
        state = {}
        if workers and profit > 0 and share > 0:
            paid = round(profit * share, 3)
            state["pending_dividend"] = paid
        if invest > 0:
            state["capital_stock"] = round(capital + invest, 3)
        events = []
        if output > 0:
            events.append({"event_type": "output", "amount": round(output, 3),
                           "firm_id": unit.unit_id,
                           "sector": unit.get_state("sector", "manufacturing")})
        if invest > 0:
            events.append({"event_type": "invested", "firm_id": unit.unit_id,
                           "amount": round(invest, 3)})
        if paid > 0:
            events.append({"event_type": "dividend_declared",
                           "amount": paid, "firm_id": unit.unit_id,
                           "workers": len(workers)})
        public = tax + water + fuel
        if public > 0:
            events.append({"event_type": "public_revenue",
                           "amount": round(public, 3)})
        return {
            "state_updates": state,
            "resource_updates": {"wealth": round(revenue - invest, 3)},
            "unit_effects": [],
            "events": events,
        }
