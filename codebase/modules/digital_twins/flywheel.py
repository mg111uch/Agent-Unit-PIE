"""FireFlow-as-sensor loop, in-repo only (Phase 6 flywheel).

Shaped payload (event_adapter/score_cli proxy pattern, no external calls)
-> kernel observation -> twin field update + version bump -> re-run
affected-city scenario -> economy-shaped opportunity dict scored by the
real scoring engine -> kernel finding. Nothing leaves the repo.
"""
from __future__ import annotations

from typing import Any, Dict


def sensor_loop(
    payload: Dict[str, Any],
    twin: Any,
    policy: Dict[str, Any],
    seed: int = 7,
    years: int = 12,
) -> Dict[str, Any]:
    """One full loop. Returns ids + opportunity + finding."""
    from kernel import kernel_bus as bus
    from modules.digital_twins import calibration_engine as ce
    from modules.digital_twins import policy_experiments as pe
    from modules.economy import scoring as sc
    from modules.simulators.popula_dyn.core.simulation_model import (
        SimulationModel as _SM)
    from modules.simulators.popula_dyn.core.scenarios import branch as _br
    city_id = payload["city_id"]
    field_name = payload["field"]
    obs = bus.publish_observation({
        "unit_id": f"city_{city_id}",
        "content": {field_name: payload["value"]},
        "event_type": "capacity_observed",
        "category": "economic",
        "signal_type": "capacity_underutilized",
        "signal_value": float(payload["value"]),
        "title": f"sensor {field_name}={payload['value']} at {city_id}",
        "description": f"fireflow-shaped sensor reading for {city_id}",
        "confidence": float(payload.get("confidence", 0.6)),
        "metadata": {"source": payload.get("source", "fireflow_shaped"),
                     "quality": payload.get("quality", "reported")},
    })
    vals = {
        k: {kk: v.get(kk, "") for kk in (
            "value", "source", "quality", "confidence", "geography", "truth")}
        for k, v in twin.state["fields"].items()
    }
    vals[field_name] = {
        "value": payload["value"], "source": payload.get("source", "x"),
        "quality": payload.get("quality", "reported"),
        "confidence": float(payload.get("confidence", 0.6)), "geography": {},
        "truth": payload.get("truth", ""),
    }
    twin.set_state(vals)
    bump = twin.bump_version([field_name], [payload.get("source", "x")])
    cal = ce.calibrate(twin.state["fields"], seed=seed, years=years)
    base = dict(cal["params"])
    base["grid_width"] = base["grid_height"] = 20
    out = _br(_SM, base, [dict(policy)])
    rows = {r["name"]: r for r in out["rows"]}
    pkey = f"policy:{policy['mechanism']}"
    gain = round(rows[pkey]["welfare"] - rows[
        "baseline:no_intervention"]["welfare"], 3)
    opp = {
        "opportunity_id": f"opp_{city_id}_{field_name}",
        "problem": f"{city_id} {field_name} signal -> industrial services demand",
        "margin": max(0.0, min(1.0, gain)),
        "startup_cost": float(rows[pkey]["fiscal"]),
        "time_to_revenue": "90d",
        "moonshot_relevance": 0.2,
        "scalability": 0.5,
        "adjacency": 0.6,
    }
    scored = sc.score_opportunity(opp)
    exp_id = f"fly_{city_id}_{obs['event'].event_id[:8]}"
    finding = {
        "exp_id": exp_id,
        "claim": f"sensor {field_name}={payload['value']} -> {city_id} "
                 f"twin {bump['current']['version_id']}: opp "
                 f"{opp['opportunity_id']} scores {scored['score']} "
                 f"({scored['verdict']})",
        "opportunity": {**opp, **scored},
        "status": "HYPOTHESIS",
    }
    pe.save_finding(exp_id, finding)
    return {
        "event_id": obs["event"].event_id,
        "signal_id": obs["signal"].signal_id,
        "twin_version": bump["current"]["version_id"],
        "opportunity": opp,
        "scored": scored,
        "finding_id": exp_id,
        "finding": finding,
    }
