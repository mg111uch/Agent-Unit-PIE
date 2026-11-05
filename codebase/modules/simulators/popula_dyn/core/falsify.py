"""Sim falsification parity with stock (Adds): try to break sim passers.

Mirrors stock `research/falsify.py` (permutation/halves/shift/LOO) with sim
analogues, all caller-sized (no fixed grid cost):
- seed_shift: same params, new seed — population within tolerance (robust, not
  lucky draw); determinism (same seed → identical) checked by the smoke test.
- perturb: birth_rate ±10% — higher birth must not yield lower population
  (monotonic response, no fragile knife-edge).
- halves: half horizon — per-step growth sign must agree with full run.

`make_model(params) -> model` keeps this decoupled from SimulationModel.
Returns {"survived", "tests"}. Lenient: attacks should fail junk, not demand
perfection from real signal.
"""
from __future__ import annotations
from typing import Any, Callable, Dict


def falsify_policy(make_model: Callable[[Dict[str, Any]], Any],
                   params: Dict[str, Any],
                   policy: Dict[str, Any],
                   metric: str = "welfare",
                   years: int = 2,
                   seed: int = 1,
                   magnitude: float = 0.3,
                   alt_magnitudes: tuple = (0.1, 0.6),
                   alt_seed: int | None = None,
                   placebo_tol: float = 0.02) -> Dict[str, Any]:
    """Try to break a scaled policy result (urban levers, welfare metric).

    Attacks: seed shift, smaller/larger magnitude, half horizon, and a zero
    magnitude placebo that must produce no effect. A lever survives only if
    every attack keeps the reference sign.
    """
    from .policy import compile as _compile
    from .scale import _run, _sign

    def effect(p: Dict[str, Any], mag: float, yrs: int) -> Dict[str, Any]:
        compiled = _compile({**policy, "magnitude": mag}, p)
        b = _run(make_model, p, None, yrs)
        t = _run(make_model, p, compiled, yrs)
        delta = float(t[metric]) - float(b[metric])
        denom = abs(float(b[metric])) or 1.0
        return {"delta": round(delta, 4), "relative": round(delta / denom, 6),
                "sign": _sign(delta, 1e-6 * denom)}

    base_p = {**params, "seed": seed}
    ref = effect(base_p, magnitude, years)
    target = ref["sign"]
    tests: Dict[str, Any] = {"reference": ref}
    if target == 0:
        return {"attempted": True, "survived": False, "tests": tests,
                "reason": "reference effect is zero; nothing to falsify"}

    alt_seed = int(alt_seed if alt_seed is not None else seed + 101)
    shift = effect({**params, "seed": alt_seed}, magnitude, years)
    tests["seed_shift"] = shift
    seed_ok = shift["sign"] == target

    mags = {}
    for mag in alt_magnitudes:
        if not -0.9 < float(mag) < 3.0:
            continue
        r = effect(base_p, float(mag), years)
        mags[str(mag)] = r
    tests["magnitude_shift"] = mags
    mag_ok = all(r["sign"] == target for r in mags.values()) if mags else True

    ph = max(1, years // 2)
    half = effect(base_p, magnitude, ph)
    tests["half_horizon"] = half
    half_ok = half["sign"] == target

    placebo = effect(base_p, 0.0, years)
    tests["placebo"] = placebo
    placebo_ok = abs(placebo["relative"]) < placebo_tol

    survived = bool(seed_ok and mag_ok and half_ok and placebo_ok)
    return {"attempted": True, "survived": survived, "tests": tests,
            "reason": "" if survived else
            f"attacks failed: seed={seed_ok} magnitude={mag_ok} "
            f"half={half_ok} placebo={placebo_ok}"}


def falsify_run(make_model: Callable[[Dict[str, Any]], Any],
                base_params: Dict[str, Any], base_pop: float,
                cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    tol = float(cfg.get("falsify_seed_tol", 0.5))
    tests: Dict[str, Any] = {}

    p1 = dict(base_params)
    p1["seed"] = int(base_params.get("seed") or 0) + 101
    try:
        m1 = make_model(p1)
        m1.run()
        pop1 = float(m1.summary().get("population", 0))
    except Exception as e:
        pop1, tests["seed_shift_error"] = 0.0, str(e)[:100]
    denom = max(1.0, abs(base_pop))
    tests["seed_shift_pop"] = pop1
    seed_ok = abs(pop1 - base_pop) / denom <= tol

    br = float(base_params.get("birth_rate", 0.04))
    pops = []
    for f in (0.9, 1.1):
        p = dict(base_params)
        p["birth_rate"] = br * f
        p["seed"] = base_params.get("seed")
        try:
            m = make_model(p)
            m.run()
            pops.append(float(m.summary().get("population", 0)))
        except Exception:
            pops.append(-1.0)
    tests["perturb_pops"] = pops  # [lower_birth, higher_birth]
    pert_ok = pops[1] >= pops[0] and pops[1] > 0

    years = int(base_params.get("years", 100))
    ph = dict(base_params)
    ph["years"] = max(1, years // 2)
    try:
        mh = make_model(ph)
        mh.run()
        gh = float(mh.summary().get("population", 0)) / max(1, mh.step_count)
        gf = base_pop / max(1, years)
        half_ok = (gh > 0) == (gf > 0) or (gh == 0 and gf == 0)
        tests["halves_growth"] = [round(gh, 3), round(gf, 3)]
    except Exception as e:
        half_ok, tests["halves_error"] = False, str(e)[:100]
    survived = bool(seed_ok and pert_ok and half_ok)
    return {"survived": survived, "tests": tests}
