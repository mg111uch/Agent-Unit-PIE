"""Twin-bridge Phase A: digital twins -> economy Units (read-only vs twins).
Phase B: CityTwin -> popula_dyn SimulationModel params + epoch heuristic.

No twin edits, no kernel imports, no score persistence. Missing twin
fields are omitted from capabilities (never invented); the Unit stays
valid. Uses objects.make_unit + ledger.record_unit (idempotent).
"""
from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from . import ledger
from .objects import make_unit


def _top(d: Any, n: int) -> List[str]:
    if not isinstance(d, dict):
        return []
    return [k for k, _ in sorted(d.items(), key=lambda kv: kv[1] or 0,
                                 reverse=True)[:n] if k]


def _size_band(n: Any) -> str:
    n = n or 0
    if n <= 0:
        return ""
    for lim, b in ((10, "micro"), (50, "small"), (500, "mid"), (5000, "large")):
        if n <= lim:
            return f"size:{b}"
    return "size:xl"


def city_to_unit(twin: Any) -> Dict[str, Any]:
    """CityTwin -> Unit dict (kind=region). Caps: top-3 industries,
    labor band from employment_rate, infra power/water presence flags."""
    p = getattr(twin, "profile", {}) or {}
    eco = getattr(twin, "economic_model", {}) or {}
    infra = getattr(twin, "infrastructure_model", {}) or {}
    name = p.get("name") or getattr(twin, "city_id", "unknown")
    region = ", ".join(s for s in (p.get("state"), p.get("country")) if s)
    caps = _top(eco.get("industries"), 3)
    emp = eco.get("employment_rate") or 0.0
    if emp > 0:
        caps.append("labor:" + ("high" if emp >= 0.9 else "mid" if emp >= 0.6 else "low"))
    if infra.get("power_grid"):
        caps.append("infra:power")
    if infra.get("water_network"):
        caps.append("infra:water")
    return asdict(make_unit("region", str(name), region, caps))


def company_to_unit(twin: Any) -> Dict[str, Any]:
    """CompanyTwin -> Unit dict (kind=firm). Caps: industry,
    top-3 employee_distribution keys (skill proxy), employee size band."""
    p = getattr(twin, "profile", {}) or {}
    org = getattr(twin, "organization_model", {}) or {}
    name = p.get("name") or getattr(twin, "company_id", "unknown")
    caps = ([p["industry"]] if p.get("industry") else []) \
        + _top(org.get("employee_distribution"), 3)
    band = _size_band(p.get("employees"))
    if band:
        caps.append(band)
    return asdict(make_unit("firm", str(name), p.get("country") or "", caps))


def snapshot_to_ledger(twin: Any, db_path: Optional[str] = None) -> str:
    """Record twin-derived Unit; idempotent via INSERT OR IGNORE. Returns unit_id."""
    if hasattr(twin, "company_id"):
        a = company_to_unit(twin)
    elif hasattr(twin, "city_id"):
        a = city_to_unit(twin)
    else:
        raise ValueError("twin has neither company_id nor city_id")
    return ledger.record_unit(a, db_path)


def twin_to_params(twin: Any, base: Optional[Dict[str, Any]] = None):
    """CityTwin -> SimulationModel params. Mapping (missing/zero -> base default + note):

    - population_model.population (or profile.population) -> initial_pop,
      clamped to [10, 20000] (sim-scale cap, not a claim about the city)
    - population_model.growth_rate -> birth_rate = 0.04 + growth_rate,
      clamped to [0.01, 0.10]
    - economic_model.employment_rate -> specialist split: total =
      clamp(round(emp*30), 2, 60); traders = total//3, toolmakers = rest
    - len(economic_model.industries) -> toolmaker_production_rate =
      base + 0.02*n, capped at 0.30

    Returns (params, notes); every key of params is a valid PARAMS key.
    Translation only: no ledger writes.
    """
    from modules.simulators.popula_dyn.constants import PARAMS
    p = dict(base or PARAMS)
    notes: List[str] = []
    popm = getattr(twin, "population_model", {}) or {}
    prof = getattr(twin, "profile", {}) or {}
    eco = getattr(twin, "economic_model", {}) or {}

    pop = popm.get("population") or prof.get("population") or 0
    if pop > 0:
        p["initial_pop"] = min(20000, max(10, int(pop)))
    else:
        notes.append("initial_pop: no twin population -> base default")

    g = popm.get("growth_rate") or 0.0
    if g:
        p["birth_rate"] = min(0.10, max(0.01, 0.04 + float(g)))
    else:
        notes.append("birth_rate: no twin growth_rate -> base default")

    emp = eco.get("employment_rate") or 0.0
    if emp > 0:
        total = min(60, max(2, round(float(emp) * 30)))
        p["initial_traders"], p["initial_toolmakers"] = total // 3, total - total // 3
    else:
        notes.append("initial_traders/toolmakers: no employment_rate -> base defaults")

    n = len(eco.get("industries") or {})
    if n:
        p["toolmaker_production_rate"] = min(0.30, float(p.get("toolmaker_production_rate",
                                                              0.1)) + 0.02 * n)
    else:
        notes.append("toolmaker_production_rate: no industries -> base default")
    return p, notes


def twin_to_epoch(twin: Any) -> str:
    """Epoch heuristic (pure): employment>=0.7 & industries>=5 -> Industrial;
    population>=8000 -> Urban-industrial; else Agricultural."""
    popm = getattr(twin, "population_model", {}) or {}
    prof = getattr(twin, "profile", {}) or {}
    eco = getattr(twin, "economic_model", {}) or {}
    pop = popm.get("population") or prof.get("population") or 0
    emp = eco.get("employment_rate") or 0.0
    n = len(eco.get("industries") or {})
    if emp >= 0.7 and n >= 5:
        return "Industrial"
    if pop >= 8000:
        return "Urban-industrial"
    return "Agricultural"


# Phase C: sim -> twin write-back (twin in-memory by design; no ledger writes).
_SOC_KEYS = ("population", "gini", "food_security")
# society -> economic_model slots. Skipped (no slot, noted): population lives
# in population_model; gini/age_structure/health_index/epoch have no slot.
GDP_MAP = {"wealth_total": "gdp", "skilled_share": "employment_rate",
           "food_security": "food_security"}


def record_outcome(twin: Any, branch_row: Dict[str, Any], policy_desc: str = "",
                   baseline_soc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Append branch_row outcome via twin.add_timeline_event. Levels always;
    deltas vs baseline_soc only when provided (None -> levels only)."""
    soc = branch_row.get("society", {}) or {}
    base = baseline_soc or {}
    event = {"type": "sim_outcome", "policy": branch_row.get("name", ""),
             "policy_desc": policy_desc, "welfare": branch_row.get("welfare"),
             "pass": branch_row.get("pass"), "fiscal": branch_row.get("fiscal"),
             "levels": {k: soc[k] for k in _SOC_KEYS if k in soc}}
    if baseline_soc is not None:
        event["deltas"] = {k: round(soc[k] - base[k], 3) for k in _SOC_KEYS
                           if k in soc and k in base}
    twin.add_timeline_event(event)
    return event


def sync_economy(twin: Any, society: Dict[str, Any]) -> List[str]:
    """Push society outputs into twin.update_economy (GDP_MAP only).
    Missing society keys skipped. Returns updated economic_model keys."""
    society = society or {}
    upd = {slot: society[k] for k, slot in GDP_MAP.items() if k in society}
    if upd:
        twin.update_economy(upd)
    return sorted(upd)
