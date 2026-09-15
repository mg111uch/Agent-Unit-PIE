# Digital Twins — city replicas (Kanpur + Delhi)

> Agent rule: shipped features → Features table here; unimplemented → `roadmap.md`; next task → `status.md`. One generic implementation, `city_id` config — never per-city modules.

## Features

| Feature | Notes |
|---|---|
| Generic CityTwin (`city_id` kanpur/delhi) | `codebase/modules/digital_twins/city_twin.py` + manager/initializer; human/company twins share Unit ids via `kernel/unit_registry.py` |
| CityState with provenance | `city_state.py`: every field = value+timestamp+source+quality+confidence+geography; placeholders labeled conf≤0.35, census anchors 0.8–0.85 |
| Truth tiers on every field | OBSERVED / TRANSACTION_DERIVED / THIRD_PARTY_VERIFIED / OWNER_REPORTED / AI_INFERRED / SIMULATED; adapters set explicitly, `infer_truth` fallback; census→verified, placeholders→inferred |
| Reporter reliability + confirmations | `reporter_reliability.py`: Laplace per-capability scores, independent-confirmation counting, confirmation-weighted CityState confidence (scales, never replaces) |
| City adapters (KMC/DDA-shaped → canonical) | `city_adapters.py`; shaped/static inputs only, no network |
| Historical snapshots 2011→2025 | sparse anchors (2011 census) enabling baseline-vs-history validation |
| Twin versioning via kernel validity | `twin_versioning.py`: field change retires `v1→HISTORICAL` with changed-variables recorded |
| Kanpur capacity slice (observation→pattern→cascade) | `capacity_slice.py`: utilization observations → events → signals → trend pattern → cascade answer, candidates-only causality |
| Calibration → popula params | `calibration_engine.py`: honest fields mapped, placeholders as flagged ranges, water/energy/air explicitly unmapped |
| Policy experiments + contrast lab + flywheel | `policy_experiments.py` (lineage registry), `contrast_lab.py` (same policy × both cities, Pareto verdict), `flywheel.py` (sensor→twin→scenario→opportunity finding) |
| Latent seam fixes verified | `create_pattern` source_ids preserved via metadata.extra; `signal_to_event` uses valid schema kwargs; Phase-3 bypass removed, cascade runs the real path |

## Identity

- Code: `codebase/modules/digital_twins/`
- Docs: `system_devpt_reports/digital_twins/`
- Loop: twins observe → kernel → popula_dyn → kernel → twin (see populaDyn_simu README Relationship)
