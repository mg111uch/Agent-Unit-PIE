"""Policy DSL (FeatureIdeas #13, Phase A): LLM proposes policy, sim executes deltas.

Policy = {target, mechanism, scope, magnitude, duration, cost, start}.
`compile()` maps supported mechanisms onto existing sim params (no behaviour
edits); unsupported mechanisms raise instead of silently pretending.
`at_step()` yields effective params for a step (schedule window); the scenario
engine (Phase B) applies it. Fiscal cost accrues per active step.
"""
from __future__ import annotations
from typing import Any, Dict
import hashlib
import json

REQUIRED = ("target", "mechanism", "scope", "magnitude", "duration", "cost", "start")

# mechanism -> {param: scale} applied as param *= (1 + scale*magnitude)
MECHANISMS: Dict[str, Dict[str, float]] = {
    "fertility_incentive": {"birth_rate": 1.0},
    "healthcare": {"death_rate": -1.0, "healer_healing_rate": 1.0},
    "food_subsidy": {"metabolism": -1.0},
    "education_expansion": {"toolmaker_production_rate": 1.0, "toolmaker_quality": 1.0},
    "industrial_policy": {"toolmaker_production_rate": 1.5, "trader_margin": 0.5},
}


def compile(policy: Dict[str, Any], base_params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate + precompute deltas. magnitude in (-0.9, +3.0)."""
    for k in REQUIRED:
        if k not in policy:
            raise ValueError(f"policy missing '{k}'")
    mech = policy["mechanism"]
    if mech not in MECHANISMS:
        raise ValueError(f"unsupported mechanism '{mech}'; supported: {sorted(MECHANISMS)}")
    m = float(policy["magnitude"])
    if not -0.9 < m < 3.0:
        raise ValueError(f"magnitude {m} out of (-0.9, 3.0)")
    deltas = {}
    for param, scale in MECHANISMS[mech].items():
        if param in base_params:
            deltas[param] = base_params[param] * (1 + scale * m)
    sched = {"start": int(policy["start"]), "duration": int(policy["duration"])}
    fiscal = float(policy["cost"]) * max(0, sched["duration"])
    return {"policy": dict(policy), "deltas": deltas, "schedule": sched,
            "fiscal_cost": fiscal}


def at_step(base_params: Dict[str, Any], compiled: Dict[str, Any], step: int) -> Dict[str, Any]:
    """Effective params at `step`: deltas inside [start, start+duration), else base."""
    s = compiled["schedule"]
    if s["start"] <= step < s["start"] + s["duration"]:
        return {**base_params, **compiled["deltas"]}
    return dict(base_params)


def policy_id(policy: Dict[str, Any], base_version: str = "") -> str:
    """Idempotent content-hash ID: same policy+base → same id (dedup like stock).

    Covers mechanism/magnitude/duration/start/scope/target + base version/epoch
    so identical proposals memoize instead of re-running."""
    canon = {k: policy.get(k) for k in
             ("mechanism", "magnitude", "duration", "start", "scope", "target")}
    canon["base"] = base_version
    return "pol_" + hashlib.sha256(
        json.dumps(canon, sort_keys=True).encode()).hexdigest()[:12]
