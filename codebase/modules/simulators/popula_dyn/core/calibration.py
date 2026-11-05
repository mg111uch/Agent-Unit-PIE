"""Urban calibration (SIM-03 Phase C): real city series -> urban pack params.

The urban pack speaks in ratios (firms per 1000 people, budget per capita), so
a real city row can be mapped onto it without inventing an absolute scale.
Three real series are enough to calibrate the pack; everything else is listed
as `missing` (no row collected) or `unmapped` (no equivalent inside the model)
and never filled with a made-up number.

Usage:
    calib = from_fields({"population": {...}, "industrial_units": {...}})
    report = fit_report(fields, make_model, agents=400)
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from . import domain as _domain

# Model-index references. 1.0 = "the default urban pack"; a city above the
# reference gets a proportionally larger lever.
REFERENCE = {
    "firms_per_1000": 10.0,
    "budget_per_capita_rs": 6900.0,
    "road_km_per_1000": 1.0,
    "municipal_grant": 5.0,
    "road_capacity": 0.8,
}

# Collected by TWN-01 but with no counterpart in the urban pack.
UNMAPPED = ("employment_rate", "industrial_capacity", "water_supply_mld",
            "energy_reliability", "power_supply_hours", "air_quality_pm25")

DERIVED = ("firms_per_1000", "municipal_grant", "road_capacity",
           "initial_pop", "weight_per_agent")

CORE_FIELDS = ("population", "industrial_units", "municipal_budget_cr")


def _val(fields: Dict[str, Any], key: str) -> Optional[float]:
    """Accept a CityState field dict, a bare number, or nothing."""
    raw = (fields or {}).get(key)
    if isinstance(raw, dict):
        raw = raw.get("value")
    try:
        out = float(raw)
    except (TypeError, ValueError):
        return None
    return out if out > 0 else None


def _source(fields: Dict[str, Any], key: str) -> str:
    raw = (fields or {}).get(key)
    if isinstance(raw, dict):
        return str(raw.get("source") or "unspecified")
    return "observed" if raw is not None else "missing"


def from_fields(fields: Dict[str, Any], agents: int = 400) -> Dict[str, Any]:
    """Map observed rows to urban params. Only observed values are emitted."""
    pop = _val(fields, "population")
    units = _val(fields, "industrial_units")
    budget = _val(fields, "municipal_budget_cr")
    road = _val(fields, "road_km")
    agents = max(1, int(agents))

    params: Dict[str, Any] = {"domain": "urban", "initial_pop": agents}
    provenance: Dict[str, Dict[str, Any]] = {}
    missing: List[str] = []
    derived: Dict[str, Optional[float]] = {}

    def note(name: str, value: Optional[float], source: str,
             formula: str) -> None:
        provenance[name] = {"value": value, "source": source,
                            "formula": formula, "status": "observed"
                            if value is not None else "missing"}

    # firms_per_1000 <- industrial_units / population
    fps = round(units / pop * 1000.0, 3) if units and pop else None
    if fps is not None:
        params["firms_per_1000"] = fps
    derived["firms_per_1000"] = fps
    note("firms_per_1000", fps, _source(fields, "industrial_units"),
         "industrial_units / population * 1000")
    if units is None:
        missing.append("industrial_units")

    # municipal_grant <- budget per capita, as an index off the reference city
    budget_pc = budget * 1e7 / pop if budget and pop else None
    index = round(budget_pc / REFERENCE["budget_per_capita_rs"], 3) \
        if budget_pc else None
    if index is not None:
        params["municipal_grant"] = round(REFERENCE["municipal_grant"] * index, 3)
    derived["municipal_grant"] = index
    note("municipal_grant", index, _source(fields, "municipal_budget_cr"),
         "budget_per_capita / reference (model index, not rupees)")
    if budget is None:
        missing.append("municipal_budget_cr")

    # road_capacity <- km per 1000 people; absent rows keep the default.
    km_pk = round(road / pop * 1000.0, 3) if road and pop else None
    if km_pk is not None:
        params["road_capacity"] = round(
            REFERENCE["road_capacity"] * km_pk / REFERENCE["road_km_per_1000"], 3)
    derived["road_capacity"] = km_pk
    note("road_capacity", km_pk, _source(fields, "road_km"),
         "road_km_per_1000 / reference")
    if road is None:
        missing.append("road_km")

    weight = round(pop / agents, 2) if pop else None
    note("weight_per_agent", weight, _source(fields, "population"),
         "population / agents")
    if pop is None:
        missing.append("population")

    return {
        "params": params,
        "anchors": derived,
        "weight_per_agent": weight,
        "provenance": provenance,
        "missing": sorted(set(missing)),
        "unmapped": list(UNMAPPED),
        "agents": agents,
    }


def _quality(rel: Optional[float]) -> str:
    if rel is None:
        return "unavailable"
    if rel <= 0.05:
        return "on_target"
    if rel <= 0.5:
        return "within_2x"
    return "off_target"


def _simulated(model: Any) -> Dict[str, float]:
    humans = [u for u in model.units.values()
              if u.unit_type == "human" and u.alive]
    pop = max(1, len(humans))
    firms = sum(1 for u in model.units.values()
                if u.unit_type == "firm" and u.alive)
    return {
        "population": float(pop),
        "firms_per_1000": round(firms / pop * 1000.0, 3),
        "municipal_grant_index": round(
            float(getattr(model, "municipal_revenue", 0.0) or 0.0)
            / max(1e-9, pop / 1000.0) / REFERENCE["municipal_grant"], 3),
        "road_capacity_index": round(
            float(getattr(model, "road_capacity", 0.0) or 0.0)
            / REFERENCE["road_capacity"], 3),
        "traffic_congestion": round(
            float(getattr(model, "traffic_congestion", 0.0) or 0.0), 4),
    }


def fit_report(fields: Dict[str, Any],
               make_model: Callable[[Dict[str, Any]], Any],
               agents: int = 400, years: int = 2,
               seed: int = 1) -> Dict[str, Any]:
    """Calibrated params vs what the model actually produces.

    An anchor is only compared when the real row exists; a missing row is
    reported as null, never back-filled.
    """
    calib = from_fields(fields, agents)
    params = _domain.apply({**calib["params"]})
    params.update({"initial_pop": agents, "seed": seed, "years": years})
    model = make_model(params)
    for _ in range(max(1, years)):
        model.step()
    sim = _simulated(model)
    rows = []
    for name in ("firms_per_1000", "municipal_grant", "road_capacity"):
        target = calib["anchors"].get(name)
        sim_key = {"firms_per_1000": "firms_per_1000",
                   "municipal_grant": None,
                   "road_capacity": "road_capacity_index"}[name]
        if name == "municipal_grant":
            # Configured index, not realized revenue (see fiscal_diagnostic).
            simulated = round(
                float(model.params.get("municipal_grant", 0.0) or 0.0)
                / REFERENCE["municipal_grant"], 3)
        else:
            simulated = sim.get(sim_key) if target is not None else None
        rel = (abs(simulated - target) / abs(target)
               if target and simulated is not None else None)
        if target is None:
            status = "missing"
        elif name == "municipal_grant":
            # The grant is set directly from the row, so this anchor only
            # confirms the mapping, it does not validate behaviour.
            status = "by_construction"
        else:
            status = _quality(rel)
        rows.append({"anchor": name,
                     "target": round(target, 3) if target else None,
                     "simulated": simulated,
                     "relative_error": round(rel, 4) if rel is not None else None,
                     "status": status})
    # Diagnostic, not an anchor: the pack's own firm taxes make municipal
    # revenue larger than the exogenous grant. Reported as a model gap.
    per_k = max(1e-9, sim["population"] / 1000.0)
    revenue_pk = (float(getattr(model, "municipal_revenue", 0.0) or 0.0)
                  / max(1, years) / per_k)
    budget_index = calib["anchors"].get("municipal_grant")
    gap = (revenue_pk / REFERENCE["municipal_grant"] / budget_index
           if budget_index else None)
    return {
        "domain": "urban",
        "agents": agents, "years": years, "seed": seed,
        "weight_per_agent": calib["weight_per_agent"],
        "parameters": {k: params[k] for k in sorted(params)
                       if k in DERIVED or k in ("domain", "initial_pop")},
        "provenance": calib["provenance"],
        "anchors": rows,
        "fiscal_diagnostic": {
            "revenue_per_1000_per_year_index": round(
                revenue_pk / REFERENCE["municipal_grant"], 3),
            "budget_index": round(budget_index, 3) if budget_index else None,
            "ratio": round(gap, 3) if gap is not None else None,
            "status": ("unavailable" if gap is None
                       else "consistent" if gap <= 2.0 else "model_gap"),
            "note": "model revenue includes firm taxes, so it exceeds the "
                    "grant-only budget index; a gap is a pack limitation, "
                    "not a calibrated result",
        },
        "raw_simulated": sim,
        "missing": calib["missing"],
        "unmapped": calib["unmapped"],
        "real_series_used": [k for k in CORE_FIELDS
                             if _val(fields, k) is not None]
        + (["road_km"] if _val(fields, "road_km") is not None else []),
    }


def finding_observation(result: Dict[str, Any], city: str,
                        mechanism: str,
                        magnitude: float = 0.3) -> Dict[str, Any]:
    """Typed observation for one stability run (largest scale, with the table).

    A mechanism that flips sign across scales is recorded as `UNSTABLE` with
    direction `MIXED`, never as an IMPROVED finding.
    """
    run = (result.get("runs") or {}).get(mechanism)
    if not run:
        raise KeyError(f"no stability run for {mechanism!r}")
    by_scale = run["by_scale"]
    if not by_scale:
        raise ValueError(f"{mechanism!r} has no scale rows")
    idx = max(range(len(by_scale)), key=lambda i: by_scale[i]["agents"])
    base = float(run["baseline_by_scale"][idx])
    rel = float(by_scale[idx]["mean_relative"])
    stable = bool(run.get("passed"))
    outcome = ("IMPROVED" if rel > 0 else "DEGRADED") if stable else "UNSTABLE"
    direction = ("INCREASE" if rel > 0 else "DECREASE") if stable else "MIXED"
    return {
        "experiment": f"urban_{city}_{mechanism}",
        "simulator": "popula_dyn",
        "metric": result.get("metric", "welfare"),
        "scenario": {"city": city, "mechanism": mechanism,
                     "magnitude": magnitude,
                     "scales": list(result.get("scales") or [])},
        "baseline": "scale_run",
        "baseline_value": round(base, 6),
        "observed_value": round(base * (1.0 + rel), 6),
        "delta": round(rel * 100.0, 2),
        "direction": direction,
        "outcome": outcome,
        "horizon": result.get("years"),
        "population": by_scale[idx]["agents"],
        "by_scale": [{"agents": r["agents"],
                      "mean_relative": r["mean_relative"]}
                     for r in by_scale],
        "level_drift": run.get("level_drift"),
        "claim_strength": "HYPOTHESIS",
    }


def stability(make_model: Callable[[Dict[str, Any]], Any],
              fields: Dict[str, Any],
              mechanisms: Iterable[str] = ("power_reliability_capex",
                                           "transport_subsidy"),
              scales: Iterable[int] = (400, 2000, 10_000),
              years: int = 2, seed: int = 1,
              metric: str = "welfare",
              seeds: Iterable[int] = None,
              magnitude: float = 0.3) -> Dict[str, Any]:
    """Run each urban lever at every scale on the calibrated param set.

    `passed` needs the mean sign to hold at every scale *and* every seed to
    agree at the largest (decision) scale: small-scale per-seed noise is
    reported, not used to veto. `n` counts the agent-level samples that enter
    the metric (agents x seeds), which is what `claim_strength` consumes.
    """
    from .scale import scale_invariance
    seeds = tuple(int(s) for s in (seeds or (seed,)))
    base = {**_domain.apply(from_fields(fields, 400)["params"]),
            "years": years, "seed": seeds[0]}
    base.pop("initial_pop", None)
    out = {"metric": metric, "years": years, "scales": [int(s) for s in scales],
           "seeds": list(seeds), "runs": {}}
    for mech in mechanisms:
        policy = {"target": "all", "mechanism": mech, "scope": "all",
                  "magnitude": magnitude, "duration": 3, "cost": 5, "start": 0}
        result = scale_invariance(make_model, base, policy,
                                  scales=tuple(scales), years=years,
                                  seeds=seeds, metric=metric)
        per_seed: Dict[int, List[int]] = {}
        for row in result["by_scale"]:
            for e in row["effects"]:
                per_seed.setdefault(int(e["seed"]), []).append(e["sign"])
        decision = per_seed and [signs[-1] for signs in per_seed.values()]
        seed_ok = bool(decision) and 0 not in decision and len(set(decision)) == 1
        passed = bool(result["passed"]) and seed_ok
        n_agents = sum(int(r["agents"]) for r in result["by_scale"]) * len(seeds)
        out["runs"][mech] = {
            "direction": result["direction"] if passed else "mixed/zero",
            "passed": passed,
            "scale_passed": result["passed"],
            "seeds": list(seeds),
            "per_seed_signs": {str(k): v for k, v in per_seed.items()},
            "n": n_agents,
            "baseline_by_scale": result["baseline_by_scale"],
            "magnitude_range": result["magnitude_range"],
            "level_drift": result["level_drift"],
            "by_scale": [{"agents": r["agents"],
                          "mean_relative": r["mean_relative"],
                          "sign": r["sign"]} for r in result["by_scale"]],
        }
    out["claim"] = ("calibrated and direction-stable at "
                    f"{out['scales']} x seeds {out['seeds']}" if all(
                        r["passed"] for r in out["runs"].values())
                    else "HYPOTHESIS: direction does not survive all scales")
    return out


def _seed_signs_at_decision_scale(run: Dict[str, Any]) -> List[int]:
    """Per-seed signs at the largest scale (the decision scale)."""
    by_scale = run.get("by_scale") or []
    if not by_scale:
        return []
    idx = max(range(len(by_scale)), key=lambda i: by_scale[i]["agents"])
    out = []
    for signs in (run.get("per_seed_signs") or {}).values():
        if len(signs) > idx:
            out.append(int(signs[idx]))
    return out


def regrade(run: Dict[str, Any]) -> Dict[str, Any]:
    """Re-apply the promotion rule to a stored stability row (no rerun).

    Direction must hold across scale means *and* every seed must agree at the
    decision (largest) scale. Small-scale per-seed noise is reported, not
    used to veto.
    """
    run = dict(run)
    signs = _seed_signs_at_decision_scale(run)
    seed_ok = bool(signs) and 0 not in signs and len(set(signs)) == 1
    scale_ok = bool(run.get("scale_passed", run.get("passed")))
    run["seed_ok"] = seed_ok
    run["passed"] = scale_ok and seed_ok
    by_scale = run.get("by_scale") or []
    if by_scale:
        idx = max(range(len(by_scale)), key=lambda i: by_scale[i]["agents"])
        rel = float(by_scale[idx].get("mean_relative", 0.0))
        sign = "+" if rel > 0 else "-" if rel < 0 else "mixed/zero"
    else:
        sign = "mixed/zero"
    run["direction"] = sign if run["passed"] else "mixed/zero"
    return run


def claim_evidence(run: Dict[str, Any],
                   falsification: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Evidence dict for `kernel.hypothesis.claim_strength.check`."""
    ev = {"seeds": len(run.get("seeds") or []), "n": int(run.get("n") or 0),
          "claim_strength": ("FALSIFICATION_PASSED" if falsification
                             else "REPLICATED")}
    if falsification:
        ev["falsification"] = {"attempted": True,
                               "passed": bool(falsification.get("survived")),
                               "tests": falsification.get("tests")}
    return ev
