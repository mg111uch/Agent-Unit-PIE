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
