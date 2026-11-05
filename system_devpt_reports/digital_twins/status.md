# Digital Twins Status
_Last verified: 2026-09-15_

## Current State
- Kanpur + Delhi replicas live on one generic `CityTwin`: versioned CityState with provenance, KMC/DDA adapters, 2011→2025 anchors, validity-backed versioning; calibration → popula baseline (4% pop error) → policy registry → contrast lab (null Pareto on industrial policy) → sensor flywheel. 
- SIM-03 Phases C–D (2026-11-04/05): real TWN-01 rows now feed the urban domain pack through `calibration_engine.calibrate(domain="urban")` → `popula_dyn.core.calibration`. Fit is on target (firms per 1000 1.0%/3.8% off; Delhi road 1.5%); budget mapped by construction. Promotion gate (3 seeds × 400/2k/10k + falsification) puts power capex both cities and Delhi transport at `FALSIFICATION_PASSED` (n=37,200); Kanpur transport is `MIXED` and stays `HYPOTHESIS`. Fit + stability: `data/twins/calibration/urban_fit.{json,md}`; four `... stability promotion` findings are registered in `popu_sim`, older ones superseded.

## Next (single source for the next task)
1. Real city data for conf≤0.35 placeholders (employment, industrial_capacity, water, energy, air_quality + non-2011 history years) — adapters ready, feeds missing; Kanpur `road_km`/`power_supply_hours`, Delhi `power_supply_hours` still absent.
2. Close the urban fiscal gap: model municipal revenue is 2.3–4.6× the real budget index because firm taxes dominate; either calibrate the tax side or report budgets as grant-only.
3. Baseline-vs-policy UI deferred (popula track).

## Recent (newest first, max 5)
- 2026-11-05: Promotion gate — 3 seeds × 400/2k/10k + falsification: power capex (both cities) and Delhi transport `FALSIFICATION_PASSED`; Kanpur transport `MIXED`.
- 2026-11-05: Profit-share channel re-gate — utility gains now reach workers; power capex `+` at 400/2k/10k in both cities.
- 2026-11-04: Urban calibration (SIM-03 C) — real rows → firms/budget/road ratios, fit report with explicit `missing`/`unmapped`, 400/2k/10k direction runs.
- 2026-09-15: Sensors both halves — in-repo reliability/confirmations + FireFlow anti-fraud fields, confirm flow, capability scores (26/26 jest).
- 2026-09-15: IN-1+2 shipped — truth tiers on all fields, opportunity evidence gating + EV (see README Features).
- 2026-09-15: PhasePlan 0–6 shipped — twins v1, calibration, experiments, contrast lab, flywheel (see README Features).
