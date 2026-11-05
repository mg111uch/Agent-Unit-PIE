"""Calibrate the urban domain pack to real city series (SIM-03 Phase C).

    conda run -n myenv python scripts/calibrate_urban.py
    conda run -n myenv python scripts/calibrate_urban.py --scales 400,2000
    conda run -n myenv python scripts/calibrate_urban.py --no-stability

Reads `data/twins/series/<city>.json` (TWN-01 rows, provenance required), maps
the real series onto urban-pack ratios, then runs baseline vs lever at each
scale. Writes `data/twins/calibration/urban_fit.{json,md}`. A missing series is
reported as null; it is never replaced with a guess.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.digital_twins import city_adapters, city_series  # noqa: E402
from modules.simulators.popula_dyn.core.simulation_model import (  # noqa: E402
    SimulationModel,
)
from modules.simulators.popula_dyn.core import calibration  # noqa: E402

CITIES = {
    "kanpur": ("city_kanpur", city_adapters.kanpur_fields),
    "delhi": ("city_delhi", city_adapters.delhi_fields),
}
OUT_DIR = ROOT / "data" / "twins" / "calibration"


def city_fields(name: str) -> dict:
    """Adapter placeholders + validated real rows; only real rows calibrate."""
    city_id, adapter = CITIES[name]
    path = ROOT / "data" / "twins" / "series" / f"{name}.json"
    base = adapter()
    if path.exists():
        out = city_series.ingest(path, base)
        if out.get("ok"):
            return out["state"]["fields"]
    from modules.digital_twins import city_state
    return city_state.build_state(city_id, base)["fields"]


def real_only(fields: dict) -> dict:
    """Drop placeholder rows: `from_fields` must not calibrate on estimates."""
    from modules.digital_twins import city_state
    return {k: v for k, v in fields.items()
            if not city_state.is_placeholder(v)}


def report_for(name: str, agents: int, years: int, seed: int) -> dict:
    fields = real_only(city_fields(name))
    rep = calibration.fit_report(fields, SimulationModel, agents=agents,
                                 years=years, seed=seed)
    rep["city"] = name
    return rep


def render(reports: dict, stab: dict) -> str:
    lines = ["# Urban pack calibration (SIM-03 Phase C)", "",
             "Real TWN-01 rows only; placeholders are excluded. A null target "
             "means the series is missing, not zero.", ""]
    for name, rep in reports.items():
        lines += [f"## {name}", "",
                  f"- agents: {rep['agents']} (1 agent = "
                  f"{rep['weight_per_agent']} people)",
                  f"- real series used: {', '.join(rep['real_series_used']) or 'none'}",
                  f"- missing: {', '.join(rep['missing']) or 'none'}",
                  f"- unmapped in model: {', '.join(rep['unmapped'])}", "",
                  "| anchor | target | simulated | rel err | status |",
                  "|---|---|---|---|---|"]
        for a in rep["anchors"]:
            lines.append(
                f"| {a['anchor']} | {a['target']} | {a['simulated']} | "
                f"{a['relative_error']} | {a['status']} |")
        diag = rep.get("fiscal_diagnostic") or {}
        if diag:
            lines += ["", f"Fiscal diagnostic: model revenue is "
                      f"{diag.get('ratio')}x the budget index "
                      f"({diag.get('status')}) — pack limitation, not a fit."]
        lines.append("")
    if stab:
        lines += ["## Policy stability (calibrated params)", ""]
        for name, run in stab.items():
            lines += [f"### {name}", "",
                      f"metric `{run['metric']}`, {run['years']} years, "
                      f"scales {run['scales']}, seeds {run.get('seeds')}", "",
                      "| mechanism | direction | passed | n | magnitude range | falsify | claim |",
                      "|---|---|---|---|---|---|---|"]
            for mech, row in run["runs"].items():
                f = row.get("falsification") or {}
                fstate = ("not run" if "falsification" not in row
                          else "passed" if f.get("passed")
                          else f.get("reason") or "failed")
                lines.append(
                    f"| {mech} | {row['direction']} | {row['passed']} | "
                    f"{row.get('n')} | {row['magnitude_range']} | {fstate} | "
                    f"{row.get('claim_strength', 'HYPOTHESIS')} |")
            lines += ["", f"**Claim ({name}):** {run['claim']}", ""]
    return "\n".join(lines)


def falsify_and_grade(name: str, stab: dict, scales, years: int,
                      seed: int) -> None:
    """Attack each stable lever, then let the evidence ladder grade it."""
    from kernel.hypothesis import claim_strength
    from modules.simulators.popula_dyn.core import falsify
    from modules.simulators.popula_dyn.core import domain as _domain

    fields = real_only(city_fields(name))
    mid = int(scales[len(scales) // 2])
    for mech, run in stab["runs"].items():
        if not run.get("passed"):
            run["falsification"] = {"attempted": False, "passed": False,
                                    "reason": "direction not stable at scale"}
            run["claim_strength"] = "HYPOTHESIS"
            continue
        params = {**_domain.apply(calibration.from_fields(fields, mid)["params"]),
                  "years": years, "seed": seed}
        params.pop("initial_pop", None)
        params["initial_pop"] = mid
        params["auto_scale_grid"] = True
        params.setdefault("land_per_agent", 1.25)
        policy = {"target": "all", "mechanism": mech, "scope": "all",
                  "magnitude": 0.3, "duration": 3, "cost": 5, "start": 0}
        f = falsify.falsify_policy(SimulationModel, params, policy,
                                   metric=stab["metric"], years=years,
                                   seed=seed, magnitude=0.3,
                                   alt_seed=seed + 101)
        run["falsification"] = {"attempted": bool(f.get("attempted")),
                                "passed": bool(f.get("survived")),
                                "reason": f.get("reason", ""),
                                "tests": f.get("tests")}
        if f.get("survived"):
            verdict = claim_strength.check(calibration.claim_evidence(run, f))
            run["claim_strength"] = verdict["effective"]
            run["claim_check"] = verdict
        else:
            run["claim_strength"] = "HYPOTHESIS"


def register_stability(city: str, run: dict, conn, tag: str = "") -> list:
    """Persist one run per mechanism and register its typed observation."""
    names = []
    suffix = f" {tag}" if tag else ""
    for mech in run["runs"]:
        obs = calibration.finding_observation(run, city, mech)
        obs["claim_strength"] = run["runs"][mech].get("claim_strength",
                                                      "HYPOTHESIS")
        obs["falsification"] = run["runs"][mech].get("falsification")
        agents = max(r["agents"] for r in obs["by_scale"])
        params = {"domain": "urban", "city": city, "mechanism": mech,
                  "magnitude": 0.3, "scales": run["scales"],
                  "seeds": run.get("seeds"), "years": run["years"],
                  "tag": tag}
        base_id = f"run_urban_{city}_{mech}{'_' + tag if tag else ''}_base"
        pol_id = f"run_urban_{city}_{mech}{'_' + tag if tag else ''}"
        conn.save_run_summary(base_id, params, {
            "population": agents, "welfare": obs["baseline_value"],
            "outcome_override": "STABLE", "claim_strength": "HYPOTHESIS"})
        conn.save_run_summary(pol_id, params, {
            "population": agents, "welfare": obs["observed_value"],
            "outcome_override": obs["outcome"], "by_scale": obs["by_scale"],
            "claim_strength": obs["claim_strength"]})
        premise = (f"Urban {city}: {mech} +30% over {run['years']}y at scales "
                   f"{run['scales']} x seeds {run.get('seeds')} -> "
                   f"{obs['outcome']} (welfare {obs['delta']:+.1f}% at "
                   f"{agents} agents). Direction: {obs['direction']}. "
                   f"Claim: {obs['claim_strength']}.{suffix}")
        reg = conn.register_to_kernel(pol_id, premise, base_id,
                                      metric="welfare", observation=obs,
                                      name=f"urban {city} {mech} stability"
                                           f"{suffix}")
        names.append(reg.get("name") or pol_id)
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agents", type=int, default=2000,
                    help="fit-report agent count (default 2000)")
    ap.add_argument("--years", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seeds", default="",
                    help="comma list for the stability gate (default: --seed)")
    ap.add_argument("--scales", default="400,2000,10000")
    ap.add_argument("--no-stability", action="store_true")
    ap.add_argument("--falsify", action="store_true",
                    help="attack each stable lever and grade its claim")
    ap.add_argument("--no-register", action="store_true",
                    help="skip kernel finding registration")
    ap.add_argument("--city", choices=sorted(CITIES) + ["all"], default="all")
    ap.add_argument("--from-report", default="",
                    help="register findings from an existing urban_fit.json "
                         "instead of rerunning")
    ap.add_argument("--regrade", action="store_true",
                    help="re-apply the promotion rule to a --from-report file")
    ap.add_argument("--tag", default="",
                    help="suffix for run ids / finding names (new code version)")
    args = ap.parse_args()

    if args.from_report:
        src = Path(args.from_report)
        payload = json.loads(src.read_text())
        stab = payload.get("stability") or {}
        reports = payload.get("reports") or {}
        if args.regrade:
            for run in stab.values():
                run["runs"] = {m: calibration.regrade(r)
                               for m, r in run["runs"].items()}
            payload["stability"] = stab
            src.write_text(json.dumps(payload, indent=1))
            print(render(reports, stab))
        if stab and not args.no_register:
            from modules.simulators.simulation_connector import SimulationConnector
            conn = SimulationConnector(simulator="popula_dyn")
            names = []
            for city, run in stab.items():
                if args.falsify:
                    scales = tuple(int(s) for s in run["scales"])
                    falsify_and_grade(city, run, scales, run["years"],
                                      (run.get("seeds") or [1])[0])
                names += register_stability(city, run, conn, args.tag)
            payload["stability"] = stab
            src.write_text(json.dumps(payload, indent=1))
            md_path = src.with_suffix(".md")
            md = render(reports, stab)
            md_path.write_text(md + "\n")
            print(md)
            print(f"registered {len(names)} finding(s): {', '.join(names)}")
        return 0

    names = sorted(CITIES) if args.city == "all" else [args.city]
    reports = {n: report_for(n, args.agents, args.years, args.seed)
               for n in names}

    stab = {}
    if not args.no_stability:
        scales = tuple(int(s) for s in args.scales.split(",") if s.strip())
        seeds = tuple(int(s) for s in args.seeds.split(",") if s.strip()) \
            or (args.seed,)
        for name in names:
            run = calibration.stability(
                SimulationModel, real_only(city_fields(name)),
                scales=scales, years=args.years, seed=args.seed,
                seeds=seeds)
            run["city"] = name
            if args.falsify:
                falsify_and_grade(name, run, scales, args.years, seeds[0])
            stab[name] = run

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"reports": reports, "stability": stab,
               "generated_by": "scripts/calibrate_urban.py"}
    (OUT_DIR / "urban_fit.json").write_text(json.dumps(payload, indent=1))
    md = render(reports, stab)
    (OUT_DIR / "urban_fit.md").write_text(md + "\n")
    print(md)

    if stab and not args.no_register:
        try:
            from modules.simulators.simulation_connector import SimulationConnector
            conn = SimulationConnector(simulator="popula_dyn")
            registered = []
            for name, run in stab.items():
                registered += register_stability(name, run, conn, args.tag)
            print(f"\nregistered {len(registered)} finding(s): "
                  f"{', '.join(registered)}")
        except Exception as e:  # registration must never break calibration
            print(f"\nregister skipped: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
