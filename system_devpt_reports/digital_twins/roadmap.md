# Digital Twins — roadmap

> Agent rule: UNIMPLEMENTED work only. Ship → move row to `README.md` Features, delete here.

## Next up

| Item | Status | Depends on |
|---|---|---|
| Real city data feeds (KMC/DDA/GMIS-shaped) | open (adapters ready; 3–4 series/city collected, rest missing) | data source access |
| Promote urban levers (multi-seed + falsification) | ✅ 3 levers `FALSIFICATION_PASSED`; Kanpur transport `MIXED` → `HYPOTHESIS` | popula `stability(seeds=…)` + `falsify_policy` |
| Municipal fiscal calibration (model revenue 2.2–4.5× budget index) | open (SIM-03 C finding; grant-only vs tax-side) | tax/water pricing calibration |
| 3D/visual map layer | deferred (data model first, per FixesIssues §12) | working model + spatial graph |
| Baseline-vs-policy non-technical UI | deferred (popula track owns it) | popula compare_runs |

## Shipped (moved from Next up)

| Item | Shipped | Where |
|---|---|---|
| Urban domain pack calibration to real series | 2026-11-04 | `calibration_engine.calibrate(domain="urban")`, `popula_dyn/core/calibration.py`, `scripts/calibrate_urban.py`, `data/twins/calibration/` |
| Urban profit-share + re-gate + kernel findings | 2026-11-05 | `behaviours/urban.py` (`profit_share`), `observation_metrics.py`, 4 findings in `popu_sim` |
| Urban promotion gate (3 seeds + falsification) | 2026-11-05 | `core/calibration.py` (`stability(seeds=…)`), `core/falsify.py` (`falsify_policy`), `scripts/calibrate_urban.py --falsify` |

## Deferred

| Item | Status |
|---|---|
| Per-city modules (kanpur_twin/, delhi_twin/) | rejected (one generic implementation + adapters) |
| Individual-person resolution | rejected (representative stats first, per FixesIssues §8) |
