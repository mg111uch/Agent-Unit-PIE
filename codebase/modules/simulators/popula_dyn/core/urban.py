"""core/urban.py — urban pack init, environment and per-step finance (SIM-03).

Phase A: zoned parcels, workers, firms and the labour market.
Phase B: power/water capacity vs demand, congestion-priced transport, and a
municipal budget (property/water/fuel revenue against capex + maintenance).

Everything is a ratio per 1000 agents, so a 400- and a 10k-agent run see the
same utility regime when `auto_scale_grid` is on.
"""
from __future__ import annotations

import math
from typing import Any, Dict

ZONES = ("residential", "industrial", "commercial")


def _clamp(v, lo, hi):
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return lo


def _humans(model: Any):
    return [u for u in model.units.values()
            if u.unit_type == "human" and u.alive]


def _employed(model: Any):
    return [u for u in _humans(model) if u.get_state("employer")]


def _zone(rng) -> str:
    r = rng.random()
    return ("residential" if r < 0.55
            else "industrial" if r < 0.8 else "commercial")


def init_urban(model: Any) -> None:
    """Create parcels, workers and firms from the domain profile."""
    params = model.params
    rng = model.random
    grid_width = int(params.get("grid_width", 50))
    grid_height = int(params.get("grid_height", 50))
    floor_space = float(params.get("floor_space", 1.0) or 1.0)

    for x in range(grid_width):
        for y in range(grid_height):
            zone = _zone(rng)
            unit = model._create_unit("parcel", position=(x, y), zone=zone,
                                      floor_space=floor_space,
                                      seed=rng.randint(0, 100000))
            unit.set_state("zone", zone)

    initial_pop = int(params.get("initial_pop", 2000))
    max_age = int(params.get("max_age", 60))
    for _ in range(initial_pop):
        x, y = model.spatial_engine.get_random_position(rng)
        age = rng.randint(15, 55) if rng.random() < 0.85 else rng.randint(0, max_age)
        gender = rng.choice(["M", "F"])
        unit = model._create_unit("worker", position=(x, y), age=age,
                                  gender=gender, seed=rng.randint(0, 100000))
        unit.set_state("age", age)
        unit.set_state("gender", gender)

    firms = max(1, int(round(initial_pop
                             * float(params.get("firms_per_1000", 10)) / 1000.0)))
    max_workers = max(2, int(math.ceil(initial_pop / firms * 1.3)))
    industrial = [u for u in model.units.values()
                  if u.unit_type == "parcel"
                  and u.get_state("zone") == "industrial"]
    for i in range(firms):
        if industrial:
            position = industrial[i % len(industrial)].get_state("position")
        else:
            position = model.spatial_engine.get_random_position(rng)
        sector = "manufacturing" if i % 2 == 0 else "service"
        firm = model._create_unit(
            "urban_firm", position=position, sector=sector,
            productivity=float(1.1 if sector == "manufacturing" else 0.9),
            price=float(params.get("firm_price", 2.0)),
            wage_offer=float(params.get("wage_offer", 2.0)),
            max_workers=max_workers,
            transport_cost=float(params.get("transport_cost", 1.0)),
            seed=rng.randint(0, 100000),
        )
        firm.set_state("sector", sector)
    model.urban_firms = firms
    model.urban_parcels = grid_width * grid_height


def reset_step(model: Any) -> None:
    """Zero the per-step counters; keep cumulative upgrade stocks."""
    params = model.params
    for name in ("power_upgrade", "water_upgrade", "road_upgrade"):
        if not hasattr(model, name):
            setattr(model, name, 0.0)
    if not hasattr(model, "municipal_balance_total"):
        model.municipal_balance_total = 0.0
    model.power_capacity = round(
        float(params.get("power_capacity", 1.0) or 1.0) + model.power_upgrade, 5)
    model.water_capacity = round(
        float(params.get("water_capacity", 1.0) or 1.0) + model.water_upgrade, 5)
    model.road_capacity = round(
        float(params.get("road_capacity", 1.0) or 1.0) + model.road_upgrade, 5)
    model.urban_output = 0.0
    model.wage_bill = 0.0
    model.urban_wages = 0
    model.urban_hires = 0
    model.power_demand = 0.0
    model.power_reliability_actual = (
        _clamp(params.get("power_reliability", 0.9), 0.0, 1.0)
        if getattr(model, "domain", "") == "urban" else 0.0)
    model.water_demand = 0.0
    model.water_supply = 1.0 if getattr(model, "domain", "") == "urban" else 0.0
    model.traffic_congestion = 0.0
    model.transport_cost_actual = float(params.get("transport_cost", 1.0) or 1.0)
    model.municipal_revenue = 0.0
    model.municipal_spend = 0.0
    model.municipal_balance = 0.0


def begin_step(model: Any) -> None:
    """Utilities vs demand, congestion, and this step's municipal capex."""
    if getattr(model, "domain", "agrarian") != "urban":
        return
    params = model.params
    humans = _humans(model)
    pop = max(1, len(humans))
    per_k = pop / 1000.0
    employment = len(_employed(model)) / pop

    road = max(0.1, float(getattr(model, "road_capacity", 1.0)))
    congestion = max(0.0, 1.0 / road - 1.0)
    model.traffic_congestion = round(congestion, 4)
    model.transport_cost_actual = round(
        float(params.get("transport_cost", 1.0) or 1.0) * (1.0 + congestion), 4)

    quality = _clamp(params.get("power_reliability", 0.9), 0.0, 1.0)
    power_demand = 0.85 + 0.25 * employment + 0.15 * min(1.0, congestion)
    model.power_demand = round(power_demand, 4)
    model.power_reliability_actual = round(min(
        1.0, float(getattr(model, "power_capacity", 1.0))
        / max(1e-9, power_demand)) * quality, 4)

    water_demand = 0.9 + 0.1 * employment
    model.water_demand = round(water_demand, 4)
    model.water_supply = round(min(
        1.0, float(getattr(model, "water_capacity", 1.0))
        / max(1e-9, water_demand)), 4)

    spend = float(params.get("municipal_capex", 1.0) or 0.0) * per_k
    if getattr(model, "municipal_balance_total", 0.0) < 0:
        spend *= 0.5  # austerity: a deficit halves next-step capex
    model.municipal_spend = round(spend, 4)
    gain = (spend / max(per_k, 1e-9)
            * float(params.get("capex_efficiency", 0.01) or 0.0))
    model.power_upgrade = round(model.power_upgrade + gain * 0.5, 5)
    model.water_upgrade = round(model.water_upgrade + gain * 0.25, 5)
    model.road_upgrade = round(model.road_upgrade + gain * 0.25, 5)


def pay_dividends(model: Any) -> float:
    """Pay declared profit shares at step end, splitting equally per worker."""
    total = 0.0
    for firm in list(model.units.values()):
        if firm.unit_type != "firm" or not firm.alive:
            continue
        pending = float(firm.get_state("pending_dividend", 0) or 0)
        if pending <= 0:
            continue
        firm.set_state("pending_dividend", 0.0)
        cash = max(0.0, float(firm.get_resource("wealth", 0) or 0))
        pending = round(min(pending, cash), 3)
        if pending <= 0:
            continue
        workers = [u for u in model.units.values()
                   if u.unit_type == "human" and u.alive
                   and u.get_state("employer") == firm.unit_id]
        if not workers:
            continue
        per = round(pending / len(workers), 4)
        firm.modify_resource("wealth", -pending)
        for w in workers:
            w.modify_resource("wealth", per)
            w.set_state("profit_share", per)
        total += pending
    if total:
        model.profit_shared_total = round(
            float(getattr(model, "profit_shared_total", 0.0) or 0.0)
            + total, 3)
    return total


def finish_step(model: Any) -> None:
    """Pay dividends, add the municipal grant, close the budget."""
    if getattr(model, "domain", "agrarian") != "urban":
        return
    pay_dividends(model)
    per_k = max(1e-9, len(_humans(model)) / 1000.0)
    model.municipal_revenue += (
        float(model.params.get("municipal_grant", 5.0) or 0.0) * per_k)
    balance = model.municipal_revenue - model.municipal_spend
    model.municipal_balance = round(balance, 4)
    model.municipal_balance_total = round(
        getattr(model, "municipal_balance_total", 0.0) + balance, 4)


def note_event(model: Any, event: Dict[str, Any]) -> None:
    """Accumulate labour-market and public-revenue events."""
    kind = event.get("event_type")
    if kind == "wage_paid":
        amount = float(event.get("amount", 0) or 0)
        model.wage_bill += amount
        model.wage_bill_total += amount
        model.urban_wages += 1
    elif kind == "output":
        amount = float(event.get("amount", 0) or 0)
        model.urban_output += amount
        model.urban_output_total += amount
    elif kind == "public_revenue":
        model.municipal_revenue += float(event.get("amount", 0) or 0)


def metrics(model: Any) -> Dict[str, Any]:
    """Urban outputs shared by `society_state`, `summary` and the collector."""
    humans = _humans(model)
    employed = [u for u in humans if u.get_state("employer")]
    wages = [float(u.get_state("wage", 0) or 0) for u in employed]
    output = float(getattr(model, "urban_output", 0.0) or 0.0)
    return {
        "employment_rate": round(len(employed) / len(humans), 3) if humans else 0.0,
        "urban_output": round(output, 3),
        "avg_wage": round(sum(wages) / len(wages), 3) if wages else 0.0,
        "gva_per_worker": round(output / max(1, len(employed)), 4),
        "profit_shared": round(
            float(getattr(model, "profit_shared_total", 0.0) or 0.0), 3),
        "power_reliability": round(
            float(getattr(model, "power_reliability_actual", 0.0) or 0.0), 4),
        "water_supply": round(float(getattr(model, "water_supply", 0.0) or 0.0), 4),
        "traffic_congestion": round(
            float(getattr(model, "traffic_congestion", 0.0) or 0.0), 4),
        "municipal_revenue": round(
            float(getattr(model, "municipal_revenue", 0.0) or 0.0), 3),
        "municipal_spend": round(
            float(getattr(model, "municipal_spend", 0.0) or 0.0), 3),
        "municipal_balance": round(
            float(getattr(model, "municipal_balance", 0.0) or 0.0), 3),
        "municipal_balance_total": round(
            float(getattr(model, "municipal_balance_total", 0.0) or 0.0), 3),
    }
