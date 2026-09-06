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
