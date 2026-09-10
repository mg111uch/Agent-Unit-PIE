"""Phase 1 Economic Object Model: Unit/Opportunity/Task/Transaction.

IDs are content-hash (same style as popula_dyn policy_id): e.g.
opp_<12hex> = sha256(canonical fields). Re-make → same id (idempotent).
Each validate_* raises ValueError on missing/bad fields.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

UNIT_KINDS = ("person", "firm", "agent", "org", "region")


def _hid(prefix: str, canon: Dict[str, Any]) -> str:
    return prefix + hashlib.sha256(
        json.dumps(canon, sort_keys=True, default=str).encode()).hexdigest()[:12]


@dataclass
class Unit:
    unit_id: str
    kind: str
    name: str
    region: str = ""
    capabilities: List[str] = field(default_factory=list)


@dataclass
class Opportunity:
    opportunity_id: str
    problem: str
    customer: str
    price: float
    cost: float
    margin: float
    startup_cost: float
    time_to_revenue: str = ""
    moonshot_relevance: float = 0.0
    scalability: float = 0.0
    adjacency: float = 0.0


@dataclass
class Task:
    task_id: str
    objective: str
    budget: float
    deadline: str = ""
    verification: str = ""
    reward: float = 0.0


@dataclass
class Transaction:
    tx_id: str
    from_: str
    to: str
    amount: float
    kind: str = "payment"
    ts: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["from"] = d.pop("from_")
        return d


def validate_unit(a: Dict[str, Any]) -> Dict[str, Any]:
    for k in ("kind", "name"):
        if not a.get(k) or not isinstance(a[k], str):
            raise ValueError(f"unit missing/bad '{k}'")
    if a["kind"] not in UNIT_KINDS:
        raise ValueError(f"unit kind '{a['kind']}' not in {UNIT_KINDS}")
    if "capabilities" in a and not isinstance(a["capabilities"], list):
        raise ValueError("unit 'capabilities' must be a list")
    return a


def validate_opportunity(o: Dict[str, Any]) -> Dict[str, Any]:
    for k in ("problem", "customer"):
        if not o.get(k) or not isinstance(o[k], str):
            raise ValueError(f"opportunity missing/bad '{k}'")
    for k in ("price", "cost", "margin", "startup_cost"):
        v = o.get(k)
        if not isinstance(v, (int, float)) or not (v >= 0):
            raise ValueError(f"opportunity '{k}' must be number >= 0")
    mr = o.get("moonshot_relevance", 0.0)
    if not isinstance(mr, (int, float)) or not 0.0 <= mr <= 1.0:
        raise ValueError("opportunity 'moonshot_relevance' must be in [0,1]")
    for k in ("scalability", "adjacency"):
        v = o.get(k, 0.0)
        if not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            raise ValueError(f"opportunity '{k}' must be in [0,1]")
    return o


def validate_task(t: Dict[str, Any]) -> Dict[str, Any]:
    if not t.get("objective") or not isinstance(t["objective"], str):
        raise ValueError("task missing/bad 'objective'")
    for k in ("budget", "reward"):
        v = t.get(k, 0.0)
        if not isinstance(v, (int, float)) or not (v >= 0):
            raise ValueError(f"task '{k}' must be number >= 0")
    return t


def validate_tx(x: Dict[str, Any]) -> Dict[str, Any]:
    frm = x.get("from", x.get("from_"))
    if not frm or not isinstance(frm, str):
        raise ValueError("tx missing/bad 'from'")
    if not x.get("to") or not isinstance(x["to"], str):
        raise ValueError("tx missing/bad 'to'")
    if not isinstance(x.get("amount"), (int, float)) or not (x["amount"] > 0):
        raise ValueError("tx 'amount' must be number > 0")
    return x


def make_unit(kind: str, name: str, region: str = "",
               capabilities: List[str] | None = None) -> Unit:
    caps = list(capabilities or [])
    d = {"kind": kind, "name": name, "region": region, "capabilities": caps}
    validate_unit(d)
    # id prefix stays "act_" so pre-rename rows keep identical ids.
    return Unit(unit_id=_hid("act_", d), kind=kind, name=name,
                 region=region, capabilities=caps)


def make_opportunity(problem: str, customer: str, price: float, cost: float,
                     startup_cost: float, time_to_revenue: str = "",
                     moonshot_relevance: float = 0.0,
                     margin: float | None = None,
                     scalability: float = 0.0,
                     adjacency: float = 0.0) -> Opportunity:
    m = (price - cost) / price if margin is None and price else (margin or 0.0)
    d = {"problem": problem, "customer": customer, "price": price, "cost": cost,
         "margin": m, "startup_cost": startup_cost,
         "time_to_revenue": time_to_revenue,
         "moonshot_relevance": moonshot_relevance,
         "scalability": scalability, "adjacency": adjacency}
    validate_opportunity(d)
    canon = {**d, "margin": round(float(m), 6),
             "scalability": float(scalability), "adjacency": float(adjacency)}
    return Opportunity(opportunity_id=_hid("opp_", canon), problem=problem,
                       customer=customer, price=float(price), cost=float(cost),
                       margin=float(m), startup_cost=float(startup_cost),
                       time_to_revenue=time_to_revenue,
                       moonshot_relevance=float(moonshot_relevance),
                       scalability=float(scalability),
                       adjacency=float(adjacency))


def make_task(objective: str, budget: float, deadline: str = "",
              verification: str = "", reward: float = 0.0) -> Task:
    d = {"objective": objective, "budget": budget, "deadline": deadline,
         "verification": verification, "reward": reward}
    validate_task(d)
    canon = {"objective": objective, "budget": budget, "deadline": deadline,
             "verification": verification, "reward": reward}
    return Task(task_id=_hid("tsk_", canon), objective=objective,
                budget=float(budget), deadline=deadline,
                verification=verification, reward=float(reward))


def make_tx(frm: str, to: str, amount: float, kind: str = "payment",
            ts: str = "") -> Transaction:
    validate_tx({"from": frm, "to": to, "amount": amount, "kind": kind, "ts": ts})
    canon = {"from": frm, "to": to, "amount": amount, "kind": kind, "ts": ts}
    return Transaction(tx_id=_hid("tx_", canon), from_=frm, to=to,
                       amount=float(amount), kind=kind, ts=ts)
