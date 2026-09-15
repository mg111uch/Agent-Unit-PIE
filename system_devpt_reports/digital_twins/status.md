# Digital Twins Status
_Last verified: 2026-09-15_

## Current State
- Kanpur + Delhi replicas live on one generic `CityTwin`: versioned CityState with provenance, KMC/DDA adapters, 2011→2025 anchors, validity-backed versioning; calibration → popula baseline (4% pop error) → policy registry → contrast lab (null Pareto on industrial policy) → sensor flywheel. 

## Next (single source for the next task)
1. Real city data for conf≤0.35 placeholders (employment, industrial_capacity, water, energy, air_quality + non-2011 history years) — adapters ready, feeds missing.
2. Fix logged latent breaks before scaling: `pattern_engine.create_pattern` illegal `source_ids`, `signal_to_event:289`.
3. Baseline-vs-policy UI deferred (popula track).

## Recent (newest first, max 5)
- 2026-09-15: Sensors both halves — in-repo reliability/confirmations + FireFlow anti-fraud fields, confirm flow, capability scores (26/26 jest).
- 2026-09-15: IN-1+2 shipped — truth tiers on all fields, opportunity evidence gating + EV (see README Features).
- 2026-09-15: PhasePlan 0–6 shipped — twins v1, calibration, experiments, contrast lab, flywheel (see README Features).
