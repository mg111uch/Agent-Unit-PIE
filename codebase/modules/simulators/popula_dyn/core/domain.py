"""Domain profiles (SIM-03): the same engine runs a countryside or a city.

A profile only chooses agent mix, land use, coefficients and policy vocabulary.
No behaviour is hard-coded to a domain; behaviours read `params["domain"]` and
the coefficients published here.
"""
from __future__ import annotations

from typing import Any, Dict

PROFILES: Dict[str, Dict[str, Any]] = {
    "agrarian": {
        "label": "Agricultural countryside",
        "policy_domain": "agrarian",
        "land_type": "land",
        "land_per_agent": 1.25,
        "human_behaviors": ["move", "prospect", "harvest",
                            "consume_metabolism", "reproduce", "survival"],
        "defaults": {},
    },
    "urban": {
        "label": "Urban industrial",
        "policy_domain": "urban",
        "land_type": "parcel",
        "land_per_agent": 0.35,
        "human_behaviors": ["move", "work", "consume_metabolism",
                            "reproduce", "survival"],
        "defaults": {
            "firms_per_1000": 10,
            "firm_productivity": 1.0,
            "firm_price": 2.0,
            "wage_offer": 5.0,
            "food_price": 2.0,
            "power_reliability": 0.9,
            "power_capacity": 0.85,
            "water_capacity": 0.95,
            "road_capacity": 0.8,
            "transport_cost": 1.0,
            "water_price": 1.0,
            "output_scale": 3.0,
            "skill_gain": 0.01,
            "property_tax_rate": 0.01,
            "profit_share": 0.1,
            "municipal_capex": 1.0,
            "municipal_grant": 5.0,
            "capex_efficiency": 0.05,
            "floor_space": 1.0,
        },
    },
}

_ALIASES = {"agriculture": "agrarian", "rural": "agrarian",
            "city": "urban", "industrial": "urban"}


def resolve(name: str = "") -> str:
    key = str(name or "agrarian").strip().lower()
    return _ALIASES.get(key, key if key in PROFILES else "agrarian")


def get(name: str = "") -> Dict[str, Any]:
    return PROFILES[resolve(name)]


def apply(params: Dict[str, Any]) -> Dict[str, Any]:
    """Fill a params dict with the profile defaults (never overwrites)."""
    out = dict(params or {})
    key = resolve(out.get("domain", "agrarian"))
    profile = PROFILES[key]
    out["domain"] = key
    out.setdefault("human_behaviors", list(profile["human_behaviors"]))
    out.setdefault("land_per_agent", profile["land_per_agent"])
    for k, v in profile["defaults"].items():
        out.setdefault(k, v)
    return out


def policy_mechanisms(params: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """The mechanism table a policy can use in this domain."""
    from modules.simulators.popula_dyn.core.policy import DOMAIN_MECHANISMS
    return DOMAIN_MECHANISMS[resolve((params or {}).get("domain", "agrarian"))]


def augment_summary(model, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Add the labour-market counters that only exist in the urban pack."""
    from modules.simulators.popula_dyn.core import urban
    out = dict(summary)
    out["domain"] = getattr(model, "domain", "agrarian")
    out["domain_label"] = get(out["domain"])["label"]
    out.update(urban.metrics(model))
    out["wage_bill"] = round(getattr(model, "wage_bill", 0.0), 3)
    return out
