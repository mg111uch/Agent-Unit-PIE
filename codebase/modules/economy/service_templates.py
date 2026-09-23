"""RA-3 service templates: pre-built work before selling it.

A template turns a YES into execution: objective, deliverable, workflow,
worker tasks with verification, cost/time estimates. quote() prices it;
instantiate() emits FireFlow-ready task dicts + a PIE proposal envelope.
Pure functions, no DB.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

MARGIN_TARGET = 0.4


def _hid(prefix: str, canon: Dict[str, Any]) -> str:
    return prefix + hashlib.sha256(
        json.dumps(canon, sort_keys=True, default=str).encode()).hexdigest()[:12]


@dataclass
class ServiceTemplate:
    template_id: str
    name: str
    objective: str
    deliverable: str
    workflow: List[str] = field(default_factory=list)
    worker_tasks: List[Dict[str, Any]] = field(default_factory=list)
    verification: str = ""
    est_cost: float = 0.0
    est_days: float = 7.0
    required_capabilities: List[str] = field(default_factory=list)


def validate_template(t: Dict[str, Any]) -> Dict[str, Any]:
    for k in ("name", "objective", "deliverable"):
        if not t.get(k) or not isinstance(t[k], str):
            raise ValueError(f"template missing/bad '{k}'")
    if not isinstance(t.get("est_cost", 0), (int, float)) or t.get("est_cost", 0) < 0:
        raise ValueError("template 'est_cost' must be number >= 0")
    for k in ("workflow", "worker_tasks", "required_capabilities"):
        if k in t and not isinstance(t[k], list):
            raise ValueError(f"template '{k}' must be a list")
    return t


def make_template(name: str, objective: str, deliverable: str,
                  workflow: List[str] | None = None,
                  worker_tasks: List[Dict[str, Any]] | None = None,
                  verification: str = "", est_cost: float = 0.0,
                  est_days: float = 7.0,
                  required_capabilities: List[str] | None = None) -> ServiceTemplate:
    d = {"name": name, "objective": objective, "deliverable": deliverable,
         "workflow": list(workflow or []),
         "worker_tasks": list(worker_tasks or []),
         "verification": verification, "est_cost": float(est_cost),
         "est_days": float(est_days),
         "required_capabilities": list(required_capabilities or [])}
    validate_template(d)
    return ServiceTemplate(template_id=_hid("tpl_", d), **d)


def _task(objective: str, verification: str) -> Dict[str, str]:
    return {"objective": objective, "verification": verification}


SEEDS: List[ServiceTemplate] = [
    make_template(
        name="supplier_discovery_100",
        objective="Identify and verify 100 suppliers matching spec",
        deliverable="100-row supplier sheet (capability, location, MOQ, lead time)",
        workflow=["collect candidates", "verify capability", "verify contact", "compile sheet"],
        worker_tasks=[
            _task("Collect 35 candidate suppliers with sources", "sheet rows + source links"),
            _task("Verify capability + MOQ for 35 suppliers", "verification notes per row"),
            _task("Verify contact + lead time for 30 suppliers", "contact proof per row"),
        ],
        verification="random 10-row re-check passes >= 8",
        est_cost=3000.0, est_days=7.0,
        required_capabilities=["web_research", "phone_verification"]),
    make_template(
        name="price_collection_50",
        objective="Collect 50 verified product prices from market",
        deliverable="50-row price sheet with shop/source evidence",
        workflow=["list SKUs", "collect prices", "photo/evidence check", "compile sheet"],
        worker_tasks=[
            _task("Collect 25 prices with shop evidence", "photo or bill reference per row"),
            _task("Collect 25 prices with shop evidence", "photo or bill reference per row"),
        ],
        verification="random 8-row re-check passes >= 6",
        est_cost=1500.0, est_days=5.0,
        required_capabilities=["field_collection"]),
]


def get_template(name: str) -> ServiceTemplate:
    for t in SEEDS:
        if t.name == name:
            return t
    raise ValueError(f"unknown template '{name}'")


def quote(t: Any, margin_target: float = MARGIN_TARGET) -> Dict[str, Any]:
    """Cost-plus price. Margin target discovered experimentally, not hardcoded law."""
    d = asdict(t) if not isinstance(t, dict) else dict(t)
    cost = float(d.get("est_cost", 0) or 0)
    m = max(0.05, min(0.9, float(margin_target)))
    price = round(cost / (1 - m), 2)
    return {"price": price, "cost": cost,
            "margin": round((price - cost) / price, 3) if price else 0.0,
            "est_days": d.get("est_days", 7.0)}


def instantiate(t: Any, prospect: Dict[str, Any]) -> Dict[str, Any]:
    """Template + prospect -> FireFlow-ready tasks + PIE proposal envelope."""
    from modules.economy.pie_protocol import build_proposal
    d = asdict(t) if not isinstance(t, dict) else dict(t)
    q = quote(d)
    co = prospect.get("company", "")
    tasks = [{**w, "budget": round(q["cost"] / max(1, len(d.get("worker_tasks", []) or [1])), 2)}
             for w in d.get("worker_tasks", [])]
    proposal = build_proposal(
        objective=f"{d['objective']} for {co}",
        action=f"offer:{d['name']}",
        budget_paise=q["price"] * 100, risk="low",
        required_capabilities=d.get("required_capabilities", []),
        expected_outcome={"deliverable": d["deliverable"],
                          "prospect_id": prospect.get("prospect_id", ""),
                          "price": q["price"]})
    return {"template": d["name"], "prospect": co, "quote": q,
            "tasks": tasks, "verification": d.get("verification", ""),
            "proposal": proposal}
