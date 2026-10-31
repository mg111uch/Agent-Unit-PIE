# Digital Twins (Level 1) — city replicas (Kanpur + Delhi)

> Agent rule: shipped features → §3; unimplemented → `02_roadmap_master.md` + this dir's `roadmap.md`; next task → `status.md` (doc-set level: `04_iteration_log.md`). **One generic implementation, `city_id` config — never per-city modules.** No phase labels in feature rows (the old "Phase-3 bypass removed" label is renamed below — DOC-02).
> Code: `$PIE_ROOT/codebase/modules/digital_twins/` · Docs: `system_devpt_reports/digital_twins/` · Loop: twins observe → kernel → popula_dyn → kernel → twin (see `populaDyn_simu/README.md`).
> **Level-2 files (same dir, still live):** `roadmap.md` (unimplemented/deferred only), `status.md` (next task + recent changes).

## 1. Purpose & principles

A twin is a **versioned, provenance-tagged, uncertainty-aware data model** of a real system — *not* a 3D visual. The 90-day technical objective (adopted) is: **two calibrated, versioned, uncertainty-aware city models that reproduce selected historical indicators and run controlled policy experiments through popula_dyn** — and only then visualization.

Principles: start at city → zones → wards/census units → clusters with **representative synthetic populations** (never "citizen #1…#millions"); every field = value + timestamp + source + quality + confidence + geography; use history as a validation set (calibrate on one period, lock a held-out period, forecast, compare — the equivalent of the stock research OOS discipline); Delhi and Kanpur are deliberately **contrasting laboratories** ("which intervention is robust across different urban structures?"). Simulation says "under model assumptions A→B", never "real policy A causes B".

`CityState` domains: population, households, employment, income, firms, industries, production, infrastructure, transport, energy, water, sanitation, education, healthcare, housing, environment, government_finance, land_use.

## 2. Data flow

```
sources (KMC / UP · DDA / Delhi · census · GIS)  → city_adapters (shaped/static, no network)
   → canonical CityState (provenance + truth tier + confidence)
   → kernel (observation → event → signal → pattern)  → twin_versioning (v1 → HISTORICAL on change)
   → calibration_engine → popula_dyn baseline → baseline-vs-held-history validation
   → policy_experiments (lineage registry) → contrast_lab (same policy × both cities, Pareto verdict)
   → flywheel (sensor → twin → scenario → opportunity finding) → kernel finding → PIE → FireFlow
```

## 3. Features (shipped)

| Feature | Notes |
|---|---|
| Generic CityTwin (`city_id` kanpur/delhi) | `codebase/modules/digital_twins/city_twin.py` + manager/initializer; human/company twins share Unit ids via `kernel/unit_registry.py` |
| CityState with provenance | `city_state.py`: value+timestamp+source+quality+confidence+geography per field; placeholders labeled conf ≤ 0.35; census anchors 0.8–0.85 |
| Truth tiers on every field | OBSERVED / TRANSACTION_DERIVED / THIRD_PARTY_VERIFIED / OWNER_REPORTED / AI_INFERRED / SIMULATED; adapters set explicitly, `infer_truth` fallback; census→verified, placeholders→inferred; (14 fields tiered at last gate) |
| Reporter reliability + confirmations | `reporter_reliability.py`: Laplace per-capability scores, independent-confirmation counting, confirmation-weighted CityState confidence (scales, never replaces) |
| City adapters (KMC/DDA-shaped → canonical) | `city_adapters.py`; shaped/static inputs only, **no network** |
| Historical snapshots 2011→2025 | sparse anchors (2011 census) enabling baseline-vs-history validation |
| Twin versioning via kernel validity | `twin_versioning.py`: field change retires `v1→HISTORICAL` with changed-variables recorded |
| Kanpur capacity slice | `capacity_slice.py`: utilization observations → events → signals → trend pattern → cascade answer; candidates-only causality (answered "why is capacity…" from a 3/3/1 cascade + history) |
| Calibration → popula params | `calibration_engine.py`: honest fields mapped, placeholders as flagged ranges; **water/energy/air explicitly unmapped**; caps pop 400, skill 1.0 recorded on every record; baseline pop error 0.036 (≈4%) at last gate |
| Policy experiments + contrast lab + flywheel | `policy_experiments.py` (lineage registry), `contrast_lab.py` (same policy × both cities, Pareto verdict — **null** at last gate), `flywheel.py` (sensor→twin→scenario→opportunity finding) |
| Latent seam fixes (verified) | `create_pattern` source_ids preserved via `metadata.extra`; `signal_to_event` uses valid schema kwargs; an earlier bypass removed so the cascade runs the real path |

## 4. Candidate real data sources (from the planning chats — all **[verify availability/licensing]**)

- **Delhi:** DDA master-plan publications (Master Plan for Delhi 2047 gazette on the DDA site as of Aug 2026; earlier MPD-2041 draft whose chapters — environment, economy, transport, water/wastewater/drainage, waste, power/digital infrastructure, spatial development, monitoring — are an almost ready-made CityState schema).
- **Kanpur:** Kanpur Municipal Corporation pages (demographics, water/sewerage, solid waste, property, planning/development, GIS-related functions), UP sources.
- **National:** smart-cities GIS/GMIS layers (spatial/project layers, vendor repositories, dashboards); census anchors already used.

## 5. Policy objects & objectives

Each policy: intervention, target, cost, timing, affected units, mechanism, intended outcome, side-effect hypotheses (partially captured by the 5-mechanism DSL [VERIFY: which of these fields are first-class?]). Candidate city questions: manufacturing automation, transport bottleneck reduction, industrial land productivity, vocational training, logistics cost, wastewater treatment, energy reliability, robotics-manufacturing priority, local-supplier procurement, export cluster.
**Don't optimize GDP alone** — target a *City Productive Capability Vector* (economic_output, productivity, real_income, employment, industrial_capacity, entrepreneurship, infrastructure_utilization, human_capital, health, education, mobility, housing, water, energy, environment, inequality, fiscal_sustainability, resilience, innovation) and search for **Pareto improvements**; classify outcomes as universal policies / city-specific / interactions / threshold effects.

## 6. Relations as the city graph (planned)

`factory ─requires→ electricity`, `factory ─depends_on→ road`, `road ─serves→ industrial_cluster`, `household ─depends_on→ water_network`, `worker ─employed_by→ firm`, `firm ─supplied_by→ supplier`, `ward ─contains→ neighborhood`, `city ─contains→ ward`, `policy ─affects→ industry` — enabling graph reasoning (electricity shortage → utilization → employment → income → consumption → local business). Requires the dormant relation/hierarchy retrievers (KRN-02).

## 7. Open items & suggestions

Project-recorded: real city feeds for conf ≤ 0.35 placeholders; twin water/energy/air scoring dims once fed; split `city_twin.py` (741 lines) when next touched; multi-seed + falsify before any finding above HYPOTHESIS.
[LOOPHOLE TWN-01 · S1] The twin is mostly placeholder/static; policy findings built on it cannot exceed HYPOTHESIS. Feed ~10 real series per city first (population by ward, employment by sector, industrial units by district, power hours, water MLD, air quality, transport counts, municipal budget, land-use). [/LOOPHOLE]
[LOOPHOLE SIM-01 · S1] Representative-agent cap (400) vs real populations — see simulator doc. [/LOOPHOLE]
[SUGGESTION TWN-02 · P1] Rank missing fields by their effect in the sensitivity grid (value of information) and collect those first. [/SUGGESTION]
[SUGGESTION TWN-03 · P2] Prove "no per-city modules" by adding a third small city with config + adapter only. [/SUGGESTION]
[SUGGESTION TWN-04 · P2] When a twin version retires, list `invalidated_simulations` and queue reruns (retain unrelated experiments, e.g., water change invalidates water-dependent policies only). [/SUGGESTION]
[SUGGESTION INT-07 · P2] Reconcile PIE `CompanyTwin` with FireFlow's enterprise twin under one versioned schema + truth tiers. [/SUGGESTION]
[SUGGESTION STR-02 · P1] Moonshot ladder stays LOCKED (city twin → industrial capability → India twin → industry/technology graph → space industry → cislunar → lunar); unlock only after STR-02 criteria. [/SUGGESTION]
[VERIFY TWN-01] Placeholder vs observed/verified field counts per city? [/VERIFY]

## 8. Roadmap hand-off (detail lives in `roadmap.md` / `status.md`)

`roadmap.md` remains the single plan of record for this module; the table below is the direction-session summary.

| Item | Status | Note |
|---|---|---|
| Real city data feeds (KMC/DDA/GMIS-shaped) | open | adapters ready, feeds missing — also listed as `status.md` next-task #1 |
| 3D/visual map layer | deferred | data model first, per `FixesIssues` §12; needs working model + spatial graph |
| Baseline-vs-policy non-technical UI | deferred | popula track owns it; depends on `compare_runs` |
| Per-city modules (`kanpur_twin/`, `delhi_twin/`) | rejected | one generic implementation + adapters |
| Individual-person resolution | rejected | representative stats first, per `FixesIssues` §8 |

**Doc reconciliation:** `status.md` still lists "fix logged latent breaks (`create_pattern` illegal `source_ids`, `signal_to_event:289`)" as next-task #2, but §3 records both as verified fixed. Treat §3/code as current and drop that status entry when it is next refreshed (DOC-03).
