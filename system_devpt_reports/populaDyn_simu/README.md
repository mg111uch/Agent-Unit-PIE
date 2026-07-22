# Simulation Engine Development Report

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

## Simulation Usage

### Via Agent
```
Run a simulation with 50 years and 100 initial population
```

### Via Python
```python
from modules.simulators.simulation_connector import SimulationConnector
conn = SimulationConnector()
result = conn.run_and_extract({'years': 20, 'initial_pop': 50}, 'run_001')
print(conn.compare_runs(['run_001', 'run_002']))
```

### Parameters
| Parameter | Default |
|-----------|----------|
| `years` | 50 |
| `initial_pop` | 50 |
| `initial_healers` | 1 |
| `grid_width` | 10 |

---

### Phase 1 Completed: Behavior Registry Refactoring

**What was done:**
- Split monolithic `behavior_registry.py` into modular `behaviours/` directory
- Created 14 behavior classes in separate files

---

### Phase 2 Completed: Agent Factory

**Created:** `core/agent_factory.py`

**Agent Configs:**
| Agent Type | Unit Type | Behaviors |
|-----------|----------|----------|
| `farmer` | `human` | move, harvest, consume_metabolism, reproduce, survival |
| `healer` | `specialist` | move, heal |
| `toolmaker` | `specialist` | move, produce |
| `trader` | `specialist` | move, trade_ag |
| `land` | `land` | regrow |

**Functions:**
- `create_unit_config()` - Creates unit with unique ID, behaviors, state, resources
- `get_agent_behaviors()` - Returns behavior list for type
- `list_agent_types()` - Lists all available types

---



### Phase 3 Completed: Spatial Engine

**Created:** `core/spatial_engine.py`

**SpatialEngine provides:**
- `place_agent()` / `remove_agent()` / `move_agent()` - Position management
- `get_neighbors()` - Find nearby units
- `get_neighborhood()` - Get adjacent positions
- `get_cell_list_contents()` - Get units at positions
- Toroidal (wrap-around) grid support
- `summary()` - Statistics

---

### Phase 4 Completed: Simulation Model

**Created:** `core/simulation_model.py`

**SimulationModel provides:**
- Unit initialization from `agent_factory.py`
- Behavior execution via `BehaviorRegistry`
- Spatial management via `SpatialEngine`
- Data collection (population, wealth, births, deaths, etc.)
- Step-by-step simulation

---

### Phase 5 Completed: WorldEngine Integration

**Modified:** `core/world_engine.py`

**Changes:**
- Added `simulation_model` parameter to constructor
- Added `process_simulation()` method - advances simulation each tick
- Added `with_agricultural_simulation(params)` - convenience factory
- Updated `health_check()` - includes simulation_model status

**Usage:**
```python
from modules.simulators.popula_dyn.core.world_engine import WorldEngine

world = WorldEngine.with_agricultural_simulation()
world.start()

for _ in range(100):
    world.tick()
```

---

## Phase 6 Completed: Simulation Connector

Created `modules/simulators/simulation_connector.py`:

| Method | Purpose |
|--------|---------|
| `run_and_extract()` | Run sim → extract signals → store in KB |
| `compare_runs()` | Diff between simulation runs |
| `inject_policy()` | Modify params, re-run scenario |
| `get_signals()` | Read signals for run |
| `list_runs()` | List all runs |

Stores under `units/simulations/{run_id}/`:
- `params.yaml` - simulation parameters
- `signals.json` - extracted signals
- `data.csv` - time series data
- `summary.json` - run summary

Signals extracted:
- population_growth, mortality_event
- resource_scarcity, prosperity
- population_decline
- healthcare_gap, trade_gap
- population_trend_declining

### Priority 2: Event Logging

Add signal emission at each simulation step:
- population_decline events
- resource_scarcity events
- Store under `units/simulations/run_XXX/signals.json`

### Priority 3: Experiment Mode

Store multiple simulation variants under `units/simulations/` for pattern analysis.

---

## Phase 7 : Pattern Auto-Detection ✅ IMPLEMENTED
Connect simulation signals → kernel pattern engine:
- Auto-detect: population_trends, resource_cycles, collapse_signals
- Enable proactive alerts via kernel_retrieve
- ✅ Closes simulation → cognition loop

---

## Current Implementation

```
popula_dyn/
├── core/
│   ├── unit_agent.py      # Generic agent with behavior list
│   ├── agent_factory.py   # Creates typed agents
│   ├── spatial_engine.py # Grid management
│   ├── simulation_model.py # Main model
│   └── world_engine.py   # Integration layer
├── behaviours/            # Modular behaviors
│   ├── move, harvest, consume, reproduce
│   ├── survival, heal, produce, trade
│   └── regrow, learn, idle
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

---

## Development Directions

### Option A: Digital Twin Integration
Connect twin data → simulation experiments:
- city_twin/human_twin data → simulation params
- Run "what-if" scenarios based on real-world data
- Strategy generation from twin → sim → analysis

### Option B: Policy Injection UI
Expose to user interface:
- Allow non-technical users to test scenarios
- Compare baseline vs policy outcomes
- Visual diff between runs

### Option C: Self-Evolution Foundations
Build recursive improvement loop:
- Auto-summarize simulation learnings
- Track hypothesis → simulation → validation
- Recursive hypothesis refinement

---