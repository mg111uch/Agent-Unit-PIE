# popula_dyn Simulation Engine (Level 1)

> **For future agents:** keep this as wholesome feature docs — one-liner rows in §3; **no phase sections or phase-wise history**; labels like "Phase0/PhaseA/Adds" were removed here (DOC-02). Code is the ultimate source of truth.
> **Code:** `$PIE_ROOT/codebase/modules/simulators/popula_dyn/` · **Kernel simulator id:** `popu_sim` · **Master doc:** `00_README_master.md` · **Level-2 appendices (same dir):** `roadmap.md` (unimplemented work), `status.md` (last verified), `SimDvptPhases.md` (game UI notes + per-item design specs).

## 1. Clarification & relationship

- **popula_dyn** = a *general* civilization simulator, not tied to any real city. Use it for **"what if?"**: policy experiments, human-behavior patterns, emergent rules.
- **digital_twins** = 1:1 replicas of *real* cities (Kanpur, Delhi): **"what is?"**. Twin params/scenarios flow into popula_dyn via the kernel; results flow back to update the twin.
- Keep modules separate; connect via kernel: `digital_twins → real data → kernel → popula_dyn → scenarios → kernel → analysis → twin update`.

| Aspect | popula_dyn | digital_twins |
|---|---|---|
| Purpose | emergent simulation (dynamic forecasting) | real-world replica (static analysis) |
| Mode | "What if?" — hypothetical scenarios | "What is?" — current-state observation |
| Output | simulation runs + signals | digital twin models |
| Use | policy experiments, trend prediction, strategy testing | understanding current reality, anomaly detection |

**Design shape:** generic `UnitAgent` with a behavior list, pluggable behaviors in a registry, emergent behavior from behavior composition — domain-agnostic (humans, companies, cities).

**Original goal:** make the simulation as realistic as possible using real population-growth history from primitive agricultural societies to modern technological ones. It started as an agricultural ABM (farmers, healers, toolmakers, traders) demonstrating Malthusian traps, specialization and population dynamics.

## 2. Commands & interfaces

- `/auto "question"` — goal-autonomous research through the shared agent loop (`run_agent_turn()`; same parsing, failure breaker, streaming). No hard kernel dependency (works with file/shell tools if kernel is down); findings go to kernel memory if available; max iterations configurable, default 5.
- **Game/API server** (`python server.py`, default `http://localhost:8000/game`, docs at `/docs`): `POST /simulation/{start,stop,reset,step,params}`, `GET /simulation/state`, `GET /game`, `ws://localhost:8000/ws/simulation` (broadcast ≈ every 1 s, multi-client sync, parameter sharing, live result comparison).
- **Game controls:** start / stop / reset / step (one year). Parameters: initial population 100–5000, birth rate 0–0.2, death rate 0–0.1, healers/toolmakers/traders 0–50 each, grid 10×10…100×100. Colors: green land, red farmers, purple healers, orange toolmakers, teal traders.
- **Live statistics panel:** Year, Population, Total Wealth, Average Skill, Births/Deaths (cumulative), specialist counts. Real-time grid rendering, live dashboard, parameter sliders, responsive layout; grid rendering capped at 100×100 for performance.

[VERIFY SIM-05] Does `/game` still run on the generic UnitAgent core, or does it assume the old fixed roles? [/VERIFY]

## 3. Features (shipped)

### 3.1 Engine core
| Capability | Description |
|---|---|
| Generic UnitAgent + behavior registry | composable, domain-agnostic units with pluggable behaviors in `behaviours/`: move, harvest, consume_metabolism, reproduce, survival, heal, produce, trade_ag, regrow, learn, idle (+ firm hire/invest) |
| Agent factory | typed agents `farmer`/`healer`/`toolmaker`/`trader`/`land` via `create_unit_config`, `get_agent_behaviors`, `list_agent_types` |
| Firm behaviours | `firm` agent (`move`/`hire`/`invest`): hires willing nearby humans into payroll, converts surplus wealth to `capital_stock`; per-step `firms_hires`/`firms_invested` + cumulative `firms_hires_total`/`firms_invested_total` counters + `Firms_Hired`/`Hired_Cumul`/`Capital_Stock` reporters |
| Spatial engine | toroidal grid (`place_agent`/`remove_agent`/`move_agent`, `get_neighbors`/`get_neighborhood`/`get_cell_list_contents`), `summary` (`human_occupied_cells`/`human_units` separate from land) |
| Simulation model | unit initialization, `BehaviorRegistry` + `SpatialEngine` orchestration, stepwise `step`/`run`, `DataCollector` (Population, Wealth, Births/Births_Cumul, Deaths/Deaths_Cumul) |
| WorldEngine integration | `simulation_model` constructor param, `process_simulation()` tick, `with_agricultural_simulation(params)`, `health_check` |
| Simulation connector | `run_and_extract`/`compare_runs`/`inject_policy`/`get_signals`/`list_runs`; stores `params.yaml`, `signals.json`, `data.csv`, `summary.json` under `data/units/simulations/{sim}/{run}` (legacy `{run_id}` + `codebase/units/simulations` migrated) |
| Hot-reload | auto-detect tool-module file changes and reload without restart; explicit `kernel_reload` and `hot_reload` tools |

### 3.2 Determinism & integrity
| Capability | Description |
|---|---|
| Independent RNG | `world_state["rng"]=model.random` used by all stochastic behaviours (`reproduce`/`survival`/`move`/`heal`/`trade_ag`/`produce`); missing rng raises instead of a silent unseeded fallback; same-seed runs reproduce identical summaries |
| Return-intent behaviours | `reproduce`/`heal`/`trade_ag`/`produce` return intents only; model applies `spawn`/`unit_effects`/counters (deterministic, double-credit fixed) |
| Single spawn path | `reproduce` returns `{spawn, events}` (no direct `add_unit`/uuid); model assigns deterministic `child-s{step}-{n}` ids; child ids identical across same-seed runs |
| Deterministic init | model-owned `u00001…` ids (uuid fallback kept) + rng-routed placement; same-seed id sets identical |
| Behavior error logging | failures log `behavior {name} {unit} failed` instead of silent `pass` |
| Smoke test | `tests/test_popula_dyn_smoke.py` — same-cell 2 fertile `birth_rate 1.0` → `births_total>=1`; cumulative vs last-step; RNG independence |

### 3.3 Realism mechanics
| Capability | Description |
|---|---|
| Reproduction & mating | fertile window 15–50; `mate_radius`, `mate_global_fallback`, `require_opposite_gender`; cumulative `births_total`/`deaths_total` |
| Individual variation | heritable `fertility` trait + drawn `lifespan`; per-unit survival limit (real age pyramid) |
| Inheritance | 5%-per-parent wealth bequest at birth, conserved via `unit_effects` |
| Death causes | starvation / old_age / hazard split with counters/columns reconciling to deaths |
| Environment | per-cell carrying capacity caps regrow; heritable `adaptability`; `prospect` fertility-gradient move (no A*); counters `Prospect_Moves`, `Capacity_Capped`; `Avg_Adaptability` column |
| Supply–demand | `core/scarcity.py` index (food-per-capita + capacity pressure) damps births / raises deaths; scarcity-priced barter in `trade_ag`/`produce` (price in events); `Scarcity` column |
| Metrics export | 22-column `data.csv` (14 engine + 8 SocietyState series via cached `society_snapshot`, incl. `Healed_Cumul`); health index uses cumulative healings |
| Signals & trends | `population_growth`, `mortality_event`, `resource_scarcity`, `prosperity`, `population_decline`, `healthcare_gap`, `trade_gap`, `population_trend_declining`; pattern auto-detection (`population_trends`, `resource_cycles`, `collapse_signals`) closes the simulation→cognition loop |

### 3.4 Policy & scenario stack
| Capability | Description |
|---|---|
| Policy DSL + SocietyState | `core/policy.py`: 5 mechanisms → deltas + schedule/fiscal; `core/society.py`: gini/age/food/skilled/health |
| Scenario engine | `core/scenarios.py`: `branch` baseline→policies + `score_policy` welfare vs gini/food/fiscal |
| Robustness | `effect_chains` side-effect search (direct/secondary/distributional/unintended) + `sensitivity` assumption grid with pass-rate gate |
| Policy screen | `screen_policy`: registry-hit or static gates pre-simulation (~0.2 ms) |
| Policy registry | `policy_id` content-hash + JSON memo in `branch()` (dedups identical proposals) |
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

`event_bridge` connects simulation outputs into the kernel cognition pipeline; `resource_engine` handles resource creation, movement, allocation, consumption, scarcity, abundance and optimization.

**Next up (unbuilt):** generic resource system (food, money, energy, knowledge, cpu, trust) and **externalized YAML simulation definitions**:

```yaml
simulation:
  name: agriculture
unit_types:
  farmer: {count: 500, behaviors: [move, gather_resource, consume, reproduce]}
resources:
  food: {regeneration_rate: 0.1}
```

## 5. Roadmap (unbuilt unless noted — consolidated from `roadmap.md` + `SimDvptPhases.md`; those files remain the single plan of record for detail)

| Item | Status | Note |
|---|---|---|
| Baseline-vs-policy compare + visual diff (non-technical policy UI) | ⬜ | depends on connector `compare_runs` |
| Self-evolution loop (auto-summarize learnings, hypothesis→sim→validate, recursive refinement) | ⬜ | needs hypothesis engine + compression |
| Seasonal yields; soil degradation/fallow; weather events; pollution | ⬜ | highest realism/ease ratio; depends on regrow + environment |
| Specialist reproduction with role mutation + overwork deaths | ⬜ | agent factory |
| Innovator (R&D boosts skill caps) + Ecologist (heals fertility, forecasts yield) | ⬜ | composable behaviours only |
| Meso agents on demand (household/institution layers only when a policy needs them, e.g. taxation) | deferred | micro+macro answer current questions |
| Communities (>50 per cell) and Cities (>500), leaders, culture score | ⬜ | epoch engine covers macro regimes only; deferred until behaviours prove it |
| Conflict, expansion, `Civilization` entity, tech tree, diplomacy | 🟡 | epoch regimes/constraints exist; agent-level conflict ⬜ |
| Warrior raiding + Ruler taxation/revolt + Merchant Guild caravans | ⬜ | needs compete/coordinate behaviours + Group |
| Gender auto-balance, litter-size 1–2, migration votes | ⬜ | trait schema |
| A*/graph pathfinding; geospatial world map (GeoPandas, rivers/mountains/oceans, real density seeds) | ⬜ | `prospect` move exists (no A*) |
| Civ-style game layer (tech tree 20–30 nodes, victory paths, scenario editor, achievements, multiplayer) | ⬜ ⛔ | low priority; locked behind twin validation |
| Cumulative plots in game UI | ⬜ | UI policy change |
| Visualization (heatmaps, Plotly export, zoomable map, Leaflet overlay, aggregate distant agents into city blobs) | ⬜ | |
| Historical data persistence / real population-history calibration | 🟡 | via twins only |
| Pharma-style modules (`event_bridge`/`world_engine`/`resource_engine` redesign) | deferred | unread, do not redesign yet |

**Problem restatement (two mutation axes):** the agent has a *parameter sweep* axis (e.g. birth 0.04→0.08) and a *codebase mutation* axis (change `reproduction`/`starvation`). Both write to the same `popu_sim` graph, so old V1 runs accumulate and falsely contradict V2 runs — see SIM-02.

## 6. Suggestions & loopholes

[LOOPHOLE SIM-01 · S1] Calibration caps (pop 400, skill 1.0) vs real cities with millions of people; add weighted representative agents and a scale-invariance test (400/2k/10k). [/LOOPHOLE]
[LOOPHOLE SIM-02 · S2] `sim@commit` lineage doesn't change on parameter sweeps; the "Problem restatement" above is only partly solved. Use run key `(sim@commit, param_hash, seed_set)`. [/LOOPHOLE]
[LOOPHOLE SIM-03 · S2] An agricultural ABM is being asked manufacturing/transport/water/energy questions; list the mechanisms it can represent and extend (sector firms, labor market, logistics cost) before claiming insight; evaluate `eco_sim`. [/LOOPHOLE]
[SUGGESTION SIM-04 · P2] Implement the City Productive Capability Vector (19 dims) and mark each dim fed vs placeholder; a *null* Pareto verdict on placeholder data is expected. [/SUGGESTION]
[SUGGESTION SIM-06 · P2] Hybrid path: epoch-engine macro layer for city scale, ABM for local validation; vectorize hot behaviors. [/SUGGESTION]
[SUGGESTION SIM-07 · P3] Report seeds, CI width, effect size and falsify pass-rate on every policy finding; nothing above HYPOTHESIS without multi-seed + falsify (KRN-06). [/SUGGESTION]
[SUGGESTION DOC-06 · P2] `SimDvptPhases.md` mixes game-UI notes and an old design plan. It is **retained as a Level-2 appendix** (per-item data structures, thresholds, per-agent specs); §2 and §5 here are the summary — do not delete the appendix without porting its specs. [/SUGGESTION]
