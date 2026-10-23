# popula_dyn Simulation Engine (Level 1)

> **For future agents:** keep this as wholesome feature docs — one-liner rows in §3; **no phase sections or phase-wise history**; labels like "Phase0/PhaseA/Adds" were removed here (DOC-02). Code is the ultimate source of truth.
> Code: `$PIE_ROOT/codebase/modules/simulators/popula_dyn/` · Kernel simulator id: `popu_sim` · Master doc: `README.md`.

## 1. Clarification & relationship

- **popula_dyn** = a *general* civilization simulator, not tied to any real city. Use it for **"what if?"**: policy experiments, human-behavior patterns, emergent rules.
- **digital_twins** = 1:1 replicas of *real* cities (Kanpur, Delhi): **"what is?"**. Twin params/scenarios flow into popula_dyn via the kernel; results flow back to update the twin.
- Keep modules separate; connect via kernel: `digital_twins → real data → kernel → popula_dyn → scenarios → kernel → analysis → twin update`.

| Aspect | popula_dyn | digital_twins |
|---|---|---|
| Purpose | emergent simulation (forecasting) | real-world replica (state estimation) |
| Mode | hypothetical scenarios | current-state observation |
| Output | simulation runs + signals | twin models |
| Use | policy experiments, trend prediction, strategy testing | understanding reality, anomaly detection |

**Original goal:** make the simulation as realistic as possible using real population-growth history from primitive agricultural societies to modern technological ones. It started as an agricultural ABM (farmers, healers, toolmakers, traders) demonstrating Malthusian traps, specialization and population dynamics.

## 2. Commands & interfaces

- `/auto "question"` — goal-autonomous research through the shared agent loop (`run_agent_turn()`; same parsing, failure breaker, streaming). No hard kernel dependency (works with file/shell tools if kernel is down); findings go to kernel memory if available; max iterations default 5.
- **Game/API server** (`python server.py`, default `http://localhost:8000/game`, docs at `/docs`): `POST /simulation/{start,stop,reset,step,params}`, `GET /simulation/state`, `ws://localhost:8000/ws/simulation` (broadcast ≈ every 1 s, multi-client sync). Controls: initial population (100–5000), birth rate (0–0.2), death rate (0–0.1), healers/toolmakers/traders (0–50), grid 10×10…100×100. Colors: green land, red farmers, purple healers, orange toolmakers, teal traders.
[VERIFY SIM-05] Does `/game` still run on the generic UnitAgent core, or does it assume the old fixed roles? [/VERIFY]

## 3. Features (shipped)

### 3.1 Engine core
| Capability | Description |
|---|---|
| Generic UnitAgent + behavior registry | composable, domain-agnostic units (humans, companies, cities) with pluggable behaviors: move, harvest, consume_metabolism, reproduce, survival, heal, produce, trade_ag, regrow, learn, idle |
| Agent factory | typed agents `farmer`/`healer`/`toolmaker`/`trader`/`land` via `create_unit_config`, `get_agent_behaviors`, `list_agent_types` |
| Firm behaviours | `firm` agent (`move`/`hire`/`invest`): hires willing nearby humans into payroll, converts surplus wealth to `capital_stock`; counters `firms_hires`/`firms_invested` (+ cumulative) and reporters |
| Spatial engine | toroidal grid: place/remove/move agent, neighbors/neighborhood/cell contents, `summary` (human_occupied_cells, human_units separate from land) |
| Simulation model | unit init, registry + spatial orchestration, step/run, `DataCollector` (Population, Wealth, Births/Deaths + cumulative) |
| WorldEngine integration | `simulation_model` constructor param, `process_simulation()` tick, `with_agricultural_simulation(params)`, `health_check` |
| Simulation connector | `run_and_extract/compare_runs/inject_policy/get_signals/list_runs`; stores `params.yaml`, `signals.json`, `data.csv`, `summary.json` under `data/units/simulations/{sim}/{run}` |
| Hot-reload | tool-module changes reload without restart |

### 3.2 Determinism & integrity
| Capability | Description |
|---|---|
| Independent RNG | `world_state["rng"]=model.random` used by all stochastic behaviours; missing rng raises (no silent unseeded fallback); same-seed runs reproduce identical summaries |
| Return-intent behaviours | `reproduce/heal/trade_ag/produce` return intents only; model applies `spawn/unit_effects/counters` (double-credit fixed) |
| Single spawn path | `reproduce` returns `{spawn, events}`; model assigns deterministic `child-s{step}-{n}` ids |
| Deterministic init | model-owned `u00001…` ids + rng-routed placement |
| Behavior error logging | failures log `behavior {name} {unit} failed` instead of silent `pass` |
| Smoke test | `tests/test_popula_dyn_smoke.py` — same-cell 2 fertile `birth_rate 1.0` → `births_total>=1`; cumulative vs last-step; RNG independence |

### 3.3 Realism mechanics
| Capability | Description |
|---|---|
| Reproduction & mating | fertile window 15–50; `mate_radius`, `mate_global_fallback`, `require_opposite_gender`; cumulative births/deaths |
| Individual variation | heritable `fertility` trait + drawn `lifespan`; per-unit survival limit (real age pyramid) |
| Inheritance | 5%-per-parent wealth bequest at birth, conserved via `unit_effects` |
| Death causes | starvation / old_age / hazard split with counters/columns reconciling to deaths |
| Environment | per-cell carrying capacity caps regrow; heritable `adaptability`; `prospect` fertility-gradient move (no A*); counters `Prospect_Moves`, `Capacity_Capped`; `Avg_Adaptability` column |
| Supply–demand | `core/scarcity.py` index (food-per-capita + capacity pressure) damps births / raises deaths; scarcity-priced barter in `trade_ag`/`produce`; `Scarcity` column |
| Metrics export | 22-column `data.csv` (14 engine + 8 SocietyState series via cached `society_snapshot`, incl. `Healed_Cumul`) |
| Signals & trends | `population_growth`, `mortality_event`, `resource_scarcity`, `prosperity`, `population_decline`, `healthcare_gap`, `trade_gap`, `population_trend_declining`; pattern auto-detection (population_trends, resource_cycles, collapse_signals) closes the simulation→cognition loop |

### 3.4 Policy & scenario stack
| Capability | Description |
|---|---|
| Policy DSL + SocietyState | `core/policy.py`: 5 mechanisms → deltas + schedule/fiscal; `core/society.py`: gini/age/food/skilled/health |
| Scenario engine | `core/scenarios.py`: `branch` baseline→policies + `score_policy` welfare vs gini/food/fiscal |
| Robustness | `effect_chains` side-effect search + `sensitivity` assumption grid with pass-rate gate |
| Policy screen | `screen_policy`: registry-hit or static gates pre-simulation (~0.2 ms) |
| Policy registry | `policy_id` content-hash + memo in `branch()` (dedup identical proposals) |
| Falsification | `core/falsify.py`: `falsify_run` seed-shift/perturb/halves attacks on passers; parity with stock research |
| Epoch engine | `core/epoch.py`: 5 regimes, 6 macro vars, constraint gates, multi-scale `run_until_transition`, `compile_epoch` calibration/scenario; `SimulationModel.epoch` |
| Paradigm search | `ARCHITECTURE` hypothesis + `develop_propose_architecture` gate: `decide_branch→propose_architecture→modify_code` for epoch jumps (behaviours→macro→epoch engine) |
| Twin-driven scenarios | `digital_twins/calibration_engine.py` maps CityState → sim params (honest fields only; placeholders as ranges); baseline-vs-held-history validation; `policy_experiments.py` + `contrast_lab.py` reuse `core/scenarios.py` with full lineage — sim code unchanged |
| Per-sim isolation & lineage | kernel scopes findings/versions/topics per simulator (`sim@commit`, sharded runs, ACTIVE→HISTORICAL validity) |

## 4. Layout

```
popula_dyn/
  core/  unit_agent · agent_factory · resource_engine · spatial_engine · event_bridge · simulation_model · world_engine
         policy · society · scenarios · scarcity · epoch · falsify
  behaviours/  move · harvest · consume · reproduce · survival · heal · produce · trade · regrow · learn · idle · hire · invest
  simulations_config/  agriculture.yaml        constants.py · ontology.yaml · behavior_registry.py
```
Planned: generic resource system (food, money, energy, knowledge, cpu, trust) and **externalized YAML simulation definitions** (unit_types with counts/behaviors; resources with regeneration rates).

## 5. Roadmap items carried from the original plan (unbuilt unless noted)

| Item | Status | Note |
|---|---|---|
| Communities (>50 per cell) and Cities (>500), leaders, culture score | ⬜ | epoch engine covers macro regimes only |
| Conflict, expansion, `Civilization` entity, tech tree, diplomacy | 🟡 | epoch regimes/constraints exist; agent-level conflict ⬜ |
| Seasonal yields; soil degradation/fallow; weather events; pollution | ⬜ | highest realism/ease ratio per original table |
| A*/graph pathfinding; geospatial world map (GeoPandas, rivers/mountains/oceans, real density seeds) | ⬜ | prospect move exists (no A*) |
| Specialist reproduction & evolution; raiding/cooperation | ⬜ | |
| New agents: Warrior, Innovator, Merchant Guild, Ecologist, Ruler | ⬜ | `firm` is closest to Ruler/investor |
| Civ-style game layer (tech tree 20–30 nodes, victory paths, scenario editor, achievements, multiplayer) | ⬜ ⛔ | low priority; locked behind twin validation |
| Visualization (heatmaps, Plotly export, zoomable map, Leaflet overlay, aggregate distant agents into city blobs) | ⬜ | |
| Historical data persistence / real population-history calibration | 🟡 | via twins only |

## 6. Suggestions & loopholes

[LOOPHOLE SIM-01 · S1] Calibration caps (pop 400, skill 1.0) vs real cities with millions of people; add weighted representative agents and a scale-invariance test (400/2k/10k). [/LOOPHOLE]
[LOOPHOLE SIM-02 · S2] `sim@commit` lineage doesn't change on parameter sweeps; the old "Problem Restatement" (param sweep vs code mutation writing to one graph) is only partly solved. Use run key `(sim@commit, param_hash, seed_set)`. [/LOOPHOLE]
[LOOPHOLE SIM-03 · S2] An agricultural ABM is being asked manufacturing/transport/water/energy questions; list the mechanisms it can represent and extend (sector firms, labor market, logistics cost) before claiming insight; evaluate `eco_sim`. [/LOOPHOLE]
[SUGGESTION SIM-04 · P2] Implement the City Productive Capability Vector (19 dims) and mark each dim fed vs placeholder; a *null* Pareto verdict on placeholder data is expected. [/SUGGESTION]
[SUGGESTION SIM-06 · P2] Hybrid path: epoch-engine macro layer for city scale, ABM for local validation; vectorize hot behaviors. [/SUGGESTION]
[SUGGESTION SIM-07 · P3] Report seeds, CI width, effect size and falsify pass-rate on every policy finding; nothing above HYPOTHESIS without multi-seed + falsify (KRN-06). [/SUGGESTION]
[SUGGESTION DOC-06 · P2] The game README (`SimDvptPhases.md`) mixes UI notes and an old plan — keep §2 here and §5 above as the replacement. [/SUGGESTION]
