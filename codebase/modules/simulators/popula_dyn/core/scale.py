"""Scale invariance (SIM-01): same policy, same direction, more agents.

Calibration tops out at a few hundred agents while real cities have millions in
effect, so the honest claim is not "the numbers match" but "the sign of the
policy effect does not depend on how many representative agents we simulate".

    result = scale_invariance(make_model, params, policy, scales=(400, 2000))
    result["passed"], result["by_scale"]

Each agent can be read as a weighted representative (agent = N people), which
is why direction is the test and magnitude is reported only as a range.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Callable, Dict, List, Sequence, Tuple

from .policy import at_step as _at_step, compile as _compile
from .society import society_state as _society
from .domain import apply as _apply_domain

DEFAULT_SCALES = (400, 2000, 10_000)
DEFAULT_YEARS = 5
DEFAULT_SEEDS = (1,)


def _run(make_model: Callable[[Dict[str, Any]], Any],
         params: Dict[str, Any], compiled: Dict[str, Any] | None,
         years: int) -> Dict[str, Any]:
    m = make_model(dict(params))
    base = dict(m.params)
    for i in range(max(1, years)):
        if compiled is not None:
            m.params = _at_step(base, compiled, i)
        m.step()
    m.params = dict(base)
    soc = _society(m)
    if soc.get("domain") == "urban":
        output_pc = soc.get("urban_output", 0.0) / max(1, soc["population"])
        welfare = (min(1.0, soc.get("employment_rate", 0.0))
                   + min(1.0, output_pc / 2.0)
                   - 0.5 * soc["gini"])
    else:
        welfare = (min(soc["food_security"], 1.5)
                   + min(soc["wealth_total"] / max(1, soc["population"]) / 20.0, 1.0)
                   - soc["gini"])
    return {"domain": soc.get("domain"),
            "population": soc["population"], "gini": soc["gini"],
            "food_security": soc["food_security"],
            "wealth_total": soc["wealth_total"],
            "urban_output": soc.get("urban_output", 0.0),
            "employment_rate": soc.get("employment_rate", 0.0),
            "grid_side": m.params.get("grid_width"),
            "land_per_agent": getattr(m, "land_per_agent", None),
            "welfare": round(welfare, 6)}


def _sign(x: float, eps: float = 1e-9) -> int:
    if abs(x) <= eps:
        return 0
    return 1 if x > 0 else -1


def scale_invariance(
    make_model: Callable[[Dict[str, Any]], Any],
    base_params: Dict[str, Any],
    policy: Dict[str, Any] | None = None,
    scales: Sequence[int] = DEFAULT_SCALES,
    years: int = DEFAULT_YEARS,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    metric: str = "welfare",
    eps_relative: float = 1e-6,
    resource_scaled: bool = True,
) -> Dict[str, Any]:
    """Run baseline vs policy at each scale; the sign must not flip.

    `resource_scaled` keeps land per agent constant (SIM-01), so a 10k run is
    the same economy, not 10k people on a 2k food stock.
    """
    compiled = _compile(policy, _apply_domain(base_params)) if policy else None
    by_scale: List[Dict[str, Any]] = []
    for n in scales:
        params = {**base_params, "initial_pop": int(n)}
        if resource_scaled:
            params["auto_scale_grid"] = True
            params.setdefault("land_per_agent", 1.25)
        effects = []
        for seed in seeds:
            p = {**params, "seed": seed}
            baseline = _run(make_model, p, None, years)
            treated = _run(make_model, p, compiled, years) if compiled else baseline
            delta = float(treated[metric]) - float(baseline[metric])
            denom = abs(float(baseline[metric])) or 1.0
            effects.append({"seed": seed, "baseline": baseline[metric],
                            "treated": treated[metric], "delta": round(delta, 4),
                            "relative": round(delta / denom, 6),
                            "sign": _sign(delta, eps_relative * denom)})
        rel = [e["relative"] for e in effects]
        by_scale.append({
            "agents": int(n),
            "grid_side": effects[0].get("grid_side") if effects else None,
            "land_per_agent": effects[0].get("land_per_agent") if effects else None,
            "agents_plus_land": int(n) + int(effects[0].get("grid_side") or 0) ** 2
            if effects else int(n),
            "effects": effects,
            "mean_relative": round(statistics.fmean(rel), 6) if rel else 0.0,
            "sign": _sign(statistics.fmean(rel), eps_relative) if rel else 0,
        })

    signs = {row["sign"] for row in by_scale}
    consistent = len(signs) == 1 and 0 not in signs
    baselines = [statistics.fmean([e["baseline"] for e in row["effects"]])
                 for row in by_scale]
    drift = level_drift(baselines)
    return {
        "policy": compiled.get("policy_id") if compiled else None,
        "metric": metric, "years": years, "seeds": list(seeds),
        "scales": [int(s) for s in scales],
        "by_scale": by_scale,
        "baseline_by_scale": [round(b, 6) for b in baselines],
        "level_drift": drift,
        "passed": bool(consistent) if compiled else None,
        "direction": "none" if not compiled else
                     ("+" if signs == {1} else "-" if signs == {-1} else "mixed/zero"),
        "magnitude_range": [min(r["mean_relative"] for r in by_scale),
                            max(r["mean_relative"] for r in by_scale)],
        "claim": ("same direction across scales" if consistent
                  else "direction does not survive scale-up; keep the finding "
                       "flagged HYPOTHESIS (SIM-01)"),
        "claim_detail": ((drift.get("warning") or "")
                         if consistent else ""),
        "note": ("Agents are representative (agent = N people); this tests "
                 "direction, not level. Levels still need ward-level weighting."),
    }


def weight_per_agent(city_population: int, agents: int) -> float:
    """How many people one simulated agent stands for at this scale."""
    return round(max(0.0, float(city_population)) / max(1, agents), 2)


def stratified(rows: List[Dict[str, Any]], strata: Sequence[str]) -> Dict[str, Any]:
    """Check nothing was sampled from a single ward/age/income bucket."""
    counts = {s: 0 for s in strata}
    for r in rows or []:
        for s in strata:
            if r.get(s):
                counts[s] += 1
    missing = [s for s in strata if counts[s] == 0]
    return {"counts": counts, "missing": missing, "ok": not missing}


def level_drift(baselines: Sequence[float], threshold: float = 0.5) -> Dict[str, Any]:
    """Warn when the baseline itself collapses as agents are added.

    A consistent direction on a collapsing baseline is still not evidence:
    the model ran out of food/wealth, so the policy was judged in a degenerate
    regime. Direction-only scale tests hide that, so it is reported explicitly.
    """
    vals = [float(v) for v in baselines or []]
    if len(vals) < 2 or vals[0] == 0:
        return {"baselines": vals, "ratio": None, "warning": None}
    ratio = round(vals[-1] / vals[0], 3)
    warning = None
    if ratio < threshold:
        warning = (f"baseline {vals[0]:.4g} → {vals[-1]:.4g} ({ratio:.0%}) as "
                   f"agents grow: direction is not enough, the model is in a "
                   f"degenerate regime at this scale")
    return {"baselines": vals, "ratio": ratio, "warning": warning}


def confidence_interval(values: Sequence[float]) -> Tuple[float, float]:
    """Tiny-N interval; reported so a 3-seed result is not read as precise."""
    vals = [float(v) for v in values]
    if len(vals) < 2:
        return (vals[0] if vals else 0.0, vals[0] if vals else 0.0)
    half = 1.96 * statistics.stdev(vals) / math.sqrt(len(vals))
    return (round(statistics.fmean(vals) - half, 6),
            round(statistics.fmean(vals) + half, 6))
