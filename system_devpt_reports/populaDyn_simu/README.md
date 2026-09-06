# Simulation Engine

> **For future agents:** Keep this README as wholesome feature docs — add/update features as one-liner prose rows in `## Features Overview`; do not add phase sections or phase-wise history. Code is the ultimate source of truth.

## New system
- Generic `UnitAgent` with behavior list
- Pluggable behaviors in registry
- Emergent behavior from behavior composition

## Architecture Comparison

| Aspect | popula_dyn | digital_twins |
|--------|---------------|---------------|
| **Purpose** | Emergent simulation (dynamic forecasting) | Real-world replica (static analysis) |
| **Mode** | "What if?" - runs hypothetical scenarios | "What is?" - current state observation |
| **Output** | Simulation runs + signals | Digital twin models |
| **Use Case** | Policy experiments, trend prediction, strategy testing | Understanding current reality, anomaly detection |

### Relationship
```
digital_twins → observes real data → kernel → popula_dyn → runs scenarios → kernel → analyzes → updates twin
```

Keep as separate modules, connect via kernel.

---

## Commands

## /auto - Auto-Research
Goal-autonomous research using the shared agent loop.

```
>> /auto "research question"
>> /auto Why is population declining?
```

**Behavior:**
- Uses `run_agent_turn()` from the shared loop (same parsing, failure breaker, streaming)
- No hard kernel dependency — proceeds with file/shell tools if kernel is unavailable
- Findings stored to kernel memory if available
- Max iterations configurable (default: 5)

---

## Features Overview

| Capability | Description |
|------------|-------------|
| Hot-Reload | Auto-detect tool module file changes and reload without restart; explicit `kernel_reload` and `hot_reload` tools |
| Behavior Registry | Pluggable registry with modular `behaviours/` (move, harvest, consume_metabolism, reproduce, survival, heal, produce, trade_ag, regrow) |
| Agent Factory | Typed agents `farmer`/`healer`/`toolmaker`/`trader`/`land` via `create_unit_config`, `get_agent_behaviors`, `list_agent_types` |
| Firm Behaviours | `firm` agent (`move`/`hire`/`invest`): hires willing nearby humans into payroll, converts surplus wealth to `capital_stock`; per-step `firms_hires`/`firms_invested` + cumulative `firms_hires_total`/`firms_invested_total` counters + `Firms_Hired`/`Hired_Cumul`/`Capital_Stock` reporters |
| Spatial Engine | Toroidal grid with `place_agent`/`remove_agent`/`move_agent`, `get_neighbors`/`get_neighborhood`/`get_cell_list_contents`, `summary` (`human_occupied_cells`/`human_units` separate from land) |
| Simulation Model | Unit initialization, `BehaviorRegistry` + `SpatialEngine` orchestration, stepwise `step`/`run`, `DataCollector` (Population, Wealth, Births/Births_Cumul, Deaths/Deaths_Cumul) |
| WorldEngine Integration | `simulation_model` constructor param, `process_simulation()` tick, `with_agricultural_simulation(params)`, `health_check` |
| Simulation Connector | `run_and_extract`/`compare_runs`/`inject_policy`/`get_signals`/`list_runs`; stores `params.yaml`, `signals.json`, `data.csv`, `summary.json` under `data/units/simulations/{run_id}` |
| Per-Sim Isolation & Lineage | Kernel scopes findings, versions and topics per simulator (`sim@commit` via Git, `data/units/simulations/{sim}/{run}` sharded, `ACTIVE→HISTORICAL` validity) — code is source of truth |
| Pattern Auto-Detection | Simulation signals → kernel pattern engine (population_trends, resource_cycles, collapse_signals), closes simulation → cognition loop |
| Reproduction & Mating | Fertile window 15–50, `mate_radius`/`mate_global_fallback`/`require_opposite_gender`, `births_total`/`deaths_total` cumulative, independent `model.random` RNG |
| Single Spawn Path | Return-intent: `reproduce` returns `{spawn, events}` (no direct `add_unit`/uuid); model assigns deterministic `child-s{step}-{n}` ids and applies spawn; child ids identical across same-seed runs |
| Independent RNG | `world_state["rng"]=model.random` used by all stochastic behaviours (`reproduce`/`survival`/`move`/`heal`/`trade_ag`/`produce`); missing rng raises instead of silent unseeded fallback; same-seed runs reproduce identical summaries |
| Behavior Error Logging | `simulation_model.py:255` logs `behavior {name} {unit} failed` instead of silent `pass` |
| Smoke Test | `tests/test_popula_dyn_smoke.py` — same-cell 2 fertile `birth_rate 1.0` → `births_total>=1`, cumulative vs last-step, RNG independence |
| Paradigm Search (Phase0) | `ARCHITECTURE` hypothesis + `develop_propose_architecture` gate: `decide_branch→propose_architecture→modify_code` for epoch jumps (behaviours→macro→epoch engine) |
| Epoch Engine (Phase3) | `core/epoch.py`: 5 regimes, 6 macro vars, constraint gates, multi-scale `run_until_transition`, `compile_epoch` calibration/scenario; `SimulationModel.epoch` |
| Sim Falsification (Adds) | `core/falsify.py`: `falsify_run` seed-shift/perturb/halves attacks on passers, parity with stock |
| Policy DSL + SocietyState (PhaseA) | `core/policy.py`: 5 mechanisms→deltas + schedule/fiscal; `core/society.py`: gini/age/food/skilled/health |
| Scenario Engine (PhaseB) | `core/scenarios.py`: `branch` baseline→policies + `score_policy` welfare vs gini/food/fiscal |
| Robustness (PhaseC) | `effect_chains` side-effect search + `sensitivity` assumption grid with pass-rate gate |
| Policy Screen | `screen_policy`: registry-hit or static gates pre-simulation (0.2ms) |
| Death Causes | starvation/old_age/hazard split + counters/columns (reconciles with deaths) |
| Deterministic Init | model-owned `u00001…` ids + rng-routed placement (same-seed id sets identical) |
| Policy Registry | `policy_id` content-hash + memo in `branch()` (dedup identical proposals) |
| Metrics Export | 22-col `data.csv`: 14 engine + 8 SocietyState series via cached `society_snapshot` (incl. `Healed_Cumul`; health index uses cumulative healings) |
| Individual Variation | heritable `fertility` trait + drawn `lifespan`; `survival` per-unit limit (real age pyramid) |
| Return-Intent Behaviours | `reproduce`/`heal`/`trade_ag`/`produce` return intents only; model applies `spawn`/`unit_effects`/counters (deterministic, double-credit fixed) |
| Signals & Trends | `population_growth`, `mortality_event`, `resource_scarcity`, `prosperity`, `population_decline`, `healthcare_gap`, `trade_gap`, `population_trend_declining` |

---

## Current Implementation

```
popula_dyn/
├── core/
│   ├── unit_agent.py      # Generic agent with behavior list
│   ├── agent_factory.py   # Creates typed agents
│   ├── resource_engine.py # Simulates resource creation, movement, allocation, consumption, scarcity, abundance, and optimization across all unit systems.
│   ├── spatial_engine.py # Manages unit positions in toroidal space.
│   ├── event_bridge.py # Connects simulation outputs into the kernel cognition pipeline.
│   ├── simulation_model.py # Main model
│   └── world_engine.py   # Integration layer
├── behaviours/            # Modular behaviors
│   ├── move, harvest, consume, reproduce
│   ├── survival, heal, produce, trade
│   └── regrow, learn, idle
├── simulations_config/            # Modular behaviors
│   └── agriculture.yaml
├── constants.py
├── ontology.yaml
└── behavior_registry.py  # Registry
```

- **Behavior-driven** - separate reusable modules
- **Composable** - units have multiple behaviors
- **Domain-agnostic** - works for humans, companies, cities

---

### Next Steps

1. Generic resource system (food, money, energy, knowledge, cpu, trust)
2. Externalized YAML-based simulation definitions

**Example:**
```yaml
simulation:
  name: agriculture
unit_types:
  farmer:
    count: 500
    behaviors:
      - move
      - gather_resource
      - consume
      - reproduce
resources:
  food:
    regeneration_rate: 0.1
```

## Problem Restatement
Agent has 2 mutation axes: param sweep (birth 0.04→0.08) vs codebase mutation (change reproduction.py, starvation.py). Both write to same popu_sim graph; old V1 runs accumulate and falsely contradict V2 runs.

---
