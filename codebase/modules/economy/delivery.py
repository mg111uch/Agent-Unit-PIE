"""RA-5 delivery bridge: template -> project tree -> margin-checked payouts.

build_project() expands an instantiated template into a parent delivery
task plus child microtasks. check_margin() enforces positive contribution
before any worker is promised money. worker_brief() is the instruction
a worker (human or agent) receives. Pure functions, no DB.
"""
from __future__ import annotations
from typing import Any, Dict, List

MIN_MARGIN = 0.10


def build_project(instantiated: Dict[str, Any]) -> Dict[str, Any]:
    """Instantiated template -> {parent, children} task dicts."""
    q = instantiated.get("quote", {})
    kids = instantiated.get("tasks", [])
    parent = {
        "objective": f"Deliver: {instantiated.get('template', '')} for {instantiated.get('prospect', '')}",
        "budget": q.get("price", 0.0),
        "verification": instantiated.get("verification", ""),
    }
    children = [{
        "objective": k.get("objective", ""),
        "budget": k.get("budget", 0.0),
        "verification": k.get("verification", ""),
    } for k in kids]
    return {"parent": parent, "children": children,
            "price": q.get("price", 0.0), "cost": q.get("cost", 0.0)}


def check_margin(price: float, budgets: List[float],
                 min_margin: float = MIN_MARGIN) -> Dict[str, Any]:
    """Worker payouts must leave a positive contribution margin."""
    total = round(sum(budgets or []), 2)
    price = float(price or 0)
    margin = round((price - total) / price, 3) if price else 0.0
    ok = price > 0 and margin >= min_margin
    return {"ok": ok, "price": price, "payout_total": total,
            "margin": margin, "min_margin": min_margin,
            "reason": "" if ok else f"margin {margin} < {min_margin}"}


def worker_brief(child: Dict[str, Any], project: str = "") -> Dict[str, Any]:
    """One microtask -> worker instruction (earn path entry point)."""
    return {"project": project,
            "objective": child.get("objective", ""),
            "pay": child.get("budget", 0.0),
            "verification": child.get("verification", ""),
            "done_when": "verifier accepts the deliverable"}


# --- REV-03: agent-first delivery capacity -------------------------------
# Agents execute, humans only QC. These are pure functions so the plan for a
# batch can be recomputed and compared against what actually happened.
DEFAULT_RECORDS_PER_AGENT_DAY = 120
DEFAULT_QC_MINUTES_PER_RECORD = 1.5
DEFAULT_SPOTCHECK_RATIO = 0.20
DEFAULT_QC_RATE_PER_HOUR = 300.0


def assign_executors(children: List[Dict[str, Any]],
                     agents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Least-loaded capable agent per microtask; never a silent assignment.

    A task with no capable agent comes back as `unassigned` with a reason, so
    a missing capability is visible instead of becoming late delivery.
    """
    load = {a.get("id", f"agent:{i}"): 0 for i, a in enumerate(agents)}
    out, unassigned = [], []
    for child in children:
        skill = child.get("skill") or ""
        capable = [a for a in agents
                   if not skill or skill in (a.get("capabilities") or [])]
        if not capable:
            unassigned.append({"objective": child.get("objective", ""),
                               "skill": skill, "reason": "no capable agent"})
            out.append({**child, "executor": None, "reason": "no capable agent"})
            continue
        pick = min(capable, key=lambda a: (load[a.get("id", "")],
                                           a.get("id", "")))
        aid = pick.get("id")
        load[aid] += 1
        out.append({**child, "executor": aid, "executor_type": "agent"})
    return {"tasks": out, "unassigned": unassigned, "load": load,
            "human_executors": 0}


def capacity_plan(records: int, agents: int = 1,
                  records_per_agent_day: int = DEFAULT_RECORDS_PER_AGENT_DAY,
                  qc_minutes_per_record: float = DEFAULT_QC_MINUTES_PER_RECORD,
                  spotcheck_ratio: float = DEFAULT_SPOTCHECK_RATIO,
                  qc_humans: int = 1) -> Dict[str, Any]:
    """How long a batch takes and how much human QC it needs."""
    import math
    records = max(0, int(records))
    per_agent = max(1, int(records_per_agent_day))
    agent_days = math.ceil(records / (max(1, agents) * per_agent))
    qc_minutes = records * spotcheck_ratio * qc_minutes_per_record
    qc_hours = round(qc_minutes / 60.0, 2)
    qc_days = math.ceil(qc_hours / 8.0 / max(1, qc_humans))
    return {"records": records, "agents": max(1, agents),
            "agent_days": agent_days, "qc_hours": qc_hours,
            "qc_humans": max(1, qc_humans), "qc_days": qc_days,
            "bottleneck": "qc" if qc_days > agent_days else "agents",
            "total_days": max(agent_days, qc_days)}


def cost_per_verified_record(verified: int, payouts: List[float] = (),
                             qc_hours: float = 0.0,
                             qc_rate_per_hour: float = DEFAULT_QC_RATE_PER_HOUR,
                             compute: float = 0.0,
                             min_margin: float = MIN_MARGIN) -> Dict[str, Any]:
    """The number REV-03 asks for, with the price floor it implies."""
    verified = max(0, int(verified))
    paid = round(sum(payouts or []), 2)
    qc_cost = round(qc_hours * qc_rate_per_hour, 2)
    total = round(paid + qc_cost + max(0.0, compute), 2)
    per = round(total / verified, 2) if verified else None
    floor = round(per / (1 - min_margin), 2) if per else None
    return {"verified": verified, "payouts": paid, "qc_cost": qc_cost,
            "compute": round(max(0.0, compute), 2), "total": total,
            "cost_per_verified_record": per, "price_floor": floor,
            "min_margin": min_margin,
            "note": "" if per else "no verified records yet; cost is unknown"}

