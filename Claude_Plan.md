# Claude Development Plan
# agent_unit_pie — Refined  

**Current State:** Two loosely coupled subsystems (`argu_god` + `popula_dyn`) with a thin agent wrapper.  
**Target State:** Universal Unit Intelligence Engine — a filesystem-backed, LLM-powered pattern intelligence system.

---

## 1. What You Actually Have Right Now

Before any planning, it helps to be precise about the current state of the code.

**`argu_god`** is a working debate-graph explorer. It compiles topics into a `graph.json` via an LLM (currently broken — the file-based subprocess pipeline is commented out), renders the graph with Three.js over WebSocket, tracks the user's belief state in a JSON file, detects simple logical contradictions, and indexes argument nodes in ChromaDB for semantic retrieval. The mindmap layer exists only as a schema stub. The `datetime` module is imported incorrectly (`from datetime import datetime` is not done — `datetime.now()` will crash). The `beliefs` argument to `get_next_argument` is missing from the call in `loop.py`.

**`popula_dyn`** is a fully working Mesa-inspired agricultural ABM. It has a clean model/agent/grid separation, a FastAPI + WebSocket game server, real-time PixiJS rendering, and a good data-collection layer. It has placeholder interactions (healers, toolmakers, traders reference each other but don't fully communicate yet), and fertility-based movement is wired into the model but not called from `FarmerAgent.move()`.

**`agent.py`** is the top-level orchestrator. It routes `/argu` commands to the argu_god CLI and general text to a Gemini interaction-based loop. The agent loop is fragile — it uses `client.interactions.create`, which is not the standard Gemini SDK call pattern, and the workspace path is hardcoded to `/home/manigupt/...`.

---

## 2. The Core Architectural Shift

Everything from here forward is built around one insight: **the system must become unit-centric, not topic-centric**.

Current mental model:

```
Topic → compile → graph → visualize
```

Target mental model:

```
Unit → observe → extract signal → store → detect pattern → update KB → act
```

This means `argu_god` stops being the core. It becomes one module — the debate module — that processes one type of unit (an intellectual topic). The same loop runs for a human body, a codebase, a simulation run, or a company.

---

## 3. The Universal Unit Schema

This is the single most important design decision. Every part of the system depends on it being stable.

```json
{
  "unit_id": "user_001",
  "unit_type": "human",
  "subtype": "body | mind | finance | codebase | org | city | sim_agent",
  "created_at": "ISO-8601",
  "state": {},
  "signals": [],
  "events": [],
  "metrics": {},
  "patterns": [],
  "relations": [],
  "subunits": [],
  "timeline": [],
  "health_score": 0.0,
  "risk_flags": [],
  "improvement_suggestions": []
}
```

Every signal also needs its own stable schema:

```json
{
  "signal_id": "sig_001",
  "unit_id": "user_001",
  "signal_type": "pain | bug | cpu_spike | revenue_decline | population_drop",
  "category": "body | code | infra | finance | social",
  "intensity": 3,
  "timestamp": "ISO-8601",
  "metadata": {},
  "source": "conversation | simulation | api | file_watch",
  "confidence": 0.82
}
```

Do not skip this step. Defining this schema first prevents the information chaos that will otherwise make the system unusable at scale.

---

## 4. Filesystem Knowledgebase Structure

The filesystem is the ground truth layer. Everything the LLM writes and reads lives here. The structure must be strict from the start.

```
units/
  humans/
    user_001/
      profile/
        identity.md
        preferences.md
      body/
        symptoms/
          left_knee.md
          stomach.md
        patterns.md
        timeline.md
      mind/
        beliefs.md
        biases.md
        emotions.md
        patterns.md
      finance/
        income.md
        spending.md
        patterns.md
      development/
        goals.md
        productivity.md
      system_summary.md
      improvement_suggestions.md

  codebases/
    argu_god/
      modules.md
      bugs.md
      patterns.md
      improvement_suggestions.md

  simulations/
    popula_dyn_run_001/
      config.json
      timeline.json
      signals.json
      patterns.md
      global_insights.md

  organizations/
    org_x/
  cities/
  countries/
```

Each `patterns.md` file is written by the LLM pattern engine, not by hand. Each `improvement_suggestions.md` file is also LLM-generated. These two files are the product of the system; everything else feeds into them.

---

## 5. Development Phases

### Phase 1 — Kernel Refactor (~1 week)

This phase restructures the repository without adding features. The goal is to make the architecture match the vision.

**1.1 New directory layout:**

```
agent_unit_pie/
  kernel/
    unit_schema.py          # Dataclasses + validation for Unit and Signal
    signal_engine.py        # Ingest, validate, store signals
    memory_engine.py        # Read/write/summarize KB files
    pattern_engine.py       # Detect patterns from signal history
    relation_engine.py      # Manage cross-unit links
    timeline_engine.py      # Temporal queries over signals
    improvement_engine.py   # Generate improvement suggestions

  modules/
    debate/                 # Current argu_god → moved here
    bodymap/
    mindmap/
    simulation_connector/   # Bridge between popula_dyn and kernel

  simulators/
    popula_dyn/             # Moved here unchanged

  units/                    # Filesystem KB (as above)

  agents/
    observer_agent.py
    pattern_agent.py
    summarizer_agent.py
    debate_agent.py
    simulation_agent.py
    improvement_agent.py

  visualization/            # Three.js frontend → moved here

  agent.py                  # Top-level orchestrator (refactored)
  system_instruction.md
```

**1.2 Migrate `argu_god` to a module:**

Move everything under `codebase/argu_god/` to `modules/debate/`. Update imports. The debate module's `graph.json`, `belief_state.json`, and `mindmap.json` become unit KB files for a `unit_type: "topic"` unit stored under `units/topics/`.

**1.3 Create `kernel/unit_schema.py`:**

Define Python dataclasses for `Unit`, `Signal`, `Pattern`, `Relation`. Add a JSON validator that ensures every file written to `units/` conforms to schema.

**1.4 Replace the LLM pipeline:**

Create `kernel/llm_client.py` with a single `call_llm(prompt, system, model, expect_json=True)` function that:
- Makes a direct API call (no subprocess, no file bridge)
- Strips markdown code fences
- Validates JSON if `expect_json=True`
- Retries once on invalid JSON
- Returns the parsed object or raises a structured error

All LLM calls in the system go through this function. Never write another file-based bridge.

---

### Phase 2 — Signal Engine + Basic Pattern Detection (~1 week)

The signal engine is the most important new component. It is the difference between a chat system and an intelligence system.

**2.1 Build `kernel/signal_engine.py`:**

```python
class SignalEngine:
    def ingest(self, unit_id: str, raw_text: str) -> Signal:
        """Call LLM to extract structured signal from natural language."""
        
    def store(self, signal: Signal) -> None:
        """Append to units/{type}/{id}/signals.json"""
        
    def query(self, unit_id: str, filters: dict) -> list[Signal]:
        """Return signals matching filters (type, time range, intensity)"""
        
    def get_timeline(self, unit_id: str) -> list[Signal]:
        """Return signals sorted by timestamp"""
```

The LLM extraction prompt should follow the pattern already used in `argu_god` for argument extraction — same idea, different schema.

**2.2 Build `kernel/pattern_engine.py`:**

Start with rule-based pattern detection. LLM-based detection comes in Phase 3. Rules to implement first:

- **Temporal recurrence**: same `signal_type` appears more than N times within window W
- **Trend detection**: intensity of same signal type increasing over last K observations
- **Correlation**: two signal types appear together more than chance (simple co-occurrence counting)
- **Contradiction**: existing contradiction detector from `argu_god/analyzer.py` — generalize it to work on any unit type

Each detected pattern is written to `units/{type}/{id}/patterns.md` with confidence score, evidence, and timestamp.

**2.3 Build `kernel/improvement_engine.py`:**

After pattern detection, run a second LLM pass that reads `patterns.md` and generates `improvement_suggestions.md`. The prompt instructs the LLM to identify structural weaknesses, escalating risks, and concrete next actions. This is the "auto-critique" idea from the ideas file, generalized.

**2.4 Wire into the agent loop:**

The top-level `agent.py` loop becomes:

```python
observe(user_input)
→ signal_engine.ingest(unit_id, user_input)
→ signal_engine.store(signal)
→ pattern_engine.run(unit_id)
→ improvement_engine.run(unit_id)
→ respond(summary)
```

---

### Phase 3 — Simulation Integration (~1 week)

This is where `popula_dyn` becomes a first-class subsystem rather than a separate project.

**3.1 Add an event logging layer to `popula_dyn`:**

Modify `model.py` to emit structured events at each step. Create a `simulation_connector/event_logger.py`:

```python
def log_step_events(model: AgriculturalModel, year: int) -> list[dict]:
    events = []
    if model.deaths > model.births * 2:
        events.append({"type": "population_decline", "severity": ..., "year": year})
    if avg_wealth < threshold:
        events.append({"type": "resource_scarcity", "severity": ..., "year": year})
    # etc.
    return events
```

The events are structured signals — same schema as the human body signals. They get stored under `units/simulations/run_001/signals.json`.

**3.2 Create `modules/simulation_connector/`:**

This module bridges `popula_dyn` and the kernel:

```python
class SimulationConnector:
    def run_and_extract(self, params: dict, run_id: str) -> str:
        """Run simulation, extract signals, store in KB, return summary"""
    
    def get_patterns(self, run_id: str) -> str:
        """Read patterns.md for this simulation run"""
    
    def compare_runs(self, run_ids: list[str]) -> str:
        """Graph diff between simulation runs"""
    
    def inject_policy(self, run_id: str, policy: dict) -> str:
        """Modify simulation params and re-run a scenario branch"""
```

**3.3 Implement "Experiment Mode":**

Allow running multiple simulation variants with different params and storing each as a separate unit under `units/simulations/`. The pattern engine then runs over all variants and generates a comparative `diff.md`. This is the "Graph Diff applied to worlds" idea from the notes.

**3.4 Convert simulation agents to unit schema:**

Each `FarmerAgent` can optionally serialize itself as a lightweight unit. This is not needed for basic integration — only enable it for specific analysis queries where per-agent intelligence is needed.

---

### Phase 4 — Cross-Unit Intelligence (~2 weeks)

This is the differentiating layer. No other system does this.

**4.1 Build `kernel/relation_engine.py`:**

```python
class RelationEngine:
    def link(self, source_unit: str, target_unit: str, relation_type: str, confidence: float):
        """Create directed edge: user_001 → project_x (works_on, 0.9)"""
    
    def get_relations(self, unit_id: str) -> list[Relation]:
        """Return all outbound and inbound relations for a unit"""
    
    def detect_cross_unit_correlations(self, unit_ids: list[str]) -> list[Pattern]:
        """Find patterns that span multiple units"""
```

**4.2 Cross-unit pattern examples to implement:**

- Mind stress ↑ → commits ↓ (link `human/user_001/mind` to `codebases/argu_god`)
- Sleep ↓ → bug rate ↑ (link body signals to codebase signals)
- Simulation scarcity → real-world budget pressure (link simulation to human finance)

**4.3 Multi-unit health score:**

Generalize the concept of "unit health" to work across all unit types:

```
Human body:  weighted(pain frequency, energy, sleep)
Codebase:    weighted(bug rate, test coverage, complexity trend)
Company:     weighted(revenue trend, churn, hiring velocity)
Simulation:  weighted(population stability, wealth distribution, Gini)
```

This becomes the single number at the top of each `system_summary.md`.

**4.4 Causal chain detection:**

Move beyond correlation. When the pattern engine finds A correlates with B and B correlates with C, attempt to order them temporally. If A precedes B precedes C consistently, record a probable causal chain with confidence. This is the "stress → sleep → code quality → revenue" insight.

---

### Phase 5 — Autonomous Agent Roles (~2 weeks)

Replace the single monolithic `run_agent()` function with specialized subagents that run in background or on-demand.

**Observer Agent** — watches for new input (user messages, simulation events, file changes) and routes to signal ingestion.

**Pattern Agent** — runs periodically over all active units. Detects new patterns. Updates `patterns.md`. Flags when a pattern exceeds a risk threshold.

**Summarizer Agent** — compresses old timeline entries into episodic memories. Prevents unbounded growth of signal logs. Runs on a schedule or when logs exceed a size threshold.

**Debate Agent** — the current `argu_god` loop, reframed. Takes any proposition and runs the explore/contradict/defend cycle. Can be triggered by the pattern agent when a contradiction is found in a unit's belief state.

**Simulation Agent** — wraps the simulation connector. Can be asked "what happens if X?" and runs the appropriate scenario.

**Improvement Agent** — reads the latest patterns and generates concrete, timestamped suggestions. Writes to `improvement_suggestions.md`. Flags high-priority suggestions to the user.

Each agent has a `system_instruction.md` in its directory. Each agent is a thin wrapper around `kernel/llm_client.py` with a specialized prompt and context-loading strategy.

---

### Phase 6 — Visualization Evolution (~1 week)

The current Three.js visualization is topic-graph-only. It needs to evolve into a unit-graph viewer.

**6.1 Replace the circle layout with force-directed:**

Use d3-force instead of the current circle layout in `graph.js`. Node mass = unit health score. Edge thickness = relation confidence.

**6.2 Node types → visual differentiation:**

Humans, codebases, simulation runs, topics, and organizations should have distinct visual representations. Use different geometries (sphere, cube, cylinder, torus) to indicate unit type.

**6.3 Click → full unit panel:**

Replace the current `alert()` on node click with a side panel that shows:
- Unit health score and trend
- Recent signals (last 5)
- Active patterns
- Top improvement suggestions
- Linked units

**6.4 Timeline view:**

Add a second view mode that shows signals for a single unit on a time axis. Patterns appear as overlays on the timeline.

**6.5 Streaming updates:**

The WebSocket is already set up in `main.py`. Wire it so that every signal ingestion and pattern detection event broadcasts a `graph_update` message to the frontend, causing the visualization to animate in real time.

## 7. Storage Strategy Summary

The layered storage design should be implemented as written here and not changed casually, because changing it breaks the agent's ability to recall history.

**Layer 1 — Markdown files** are the human-readable source of truth. They are what the LLM reads and writes. Every `patterns.md` and `improvement_suggestions.md` is here. The LLM treats these as its "notes."

**Layer 2 — JSON structured data** lives alongside the markdown. `signals.json`, `timeline.json`, `relations.json`. These are machine-parseable. The pattern engine reads these directly without LLM.

**Layer 3 — ChromaDB vector index** is the semantic retrieval layer. The existing `vector_store.py` already handles this for arguments. Extend it to index all signal and pattern content, not just debate arguments.

**Layer 4 — Graph database** (Neo4j or Memgraph) is a future option when relation queries become complex enough to require graph traversal. Do not add this in Phases 1–3. The relation engine can use an in-memory graph (NetworkX) backed by `relations.json` for now.

---

## 9. Development Directions

Beyond the build plan, these are the directions in which the project can grow, ordered by feasibility and impact.

**Direction 1 — Personal Intelligence OS.** The most natural near-term direction. A human user interacts daily with the agent, reporting body symptoms, mental state, work progress, and financial events. The system builds a longitudinal personal intelligence profile. Weekly summaries are generated automatically. Early signals of burnout, health deterioration, or financial stress are flagged. This is achievable within Phases 1–3 using only the human unit type.

**Direction 2 — Codebase Intelligence.** The agent watches a codebase directory, detects changes, runs analysis (complexity, test coverage, error frequency from logs), and maintains a living `patterns.md` for the project. Integration with git history adds temporal signal. This pairs naturally with the existing ArguGod codebase as the first target unit.

**Direction 3 — Simulation-as-Hypothesis-Tester.** The population simulation becomes a tool for testing "what if" questions about real-world units. "What happens to my organization's productivity if I lose two senior developers?" runs a parameterized simulation variant and returns a pattern analysis. This is the most intellectually ambitious direction and requires solid Phase 3 integration.

**Direction 4 — Organizational Intelligence.** Extend the unit schema to cover companies and teams. Track hiring, revenue, product signals, and team health. Generate improvement suggestions for organizational structure. The simulation layer can model organizational dynamics the same way it models population dynamics.

**Direction 5 — Debate + Bodymap Fusion.** The mindmap tracks intellectual beliefs. The bodymap tracks physical signals. When the pattern engine finds that stress (mind signal) correlates with physical symptoms (body signal), the debate module can be invoked to reason about the causal structure. This creates a system that thinks about itself.

**Direction 6 — Multi-Agent Coordination.** When the specialized agents from Phase 5 are working, allow them to communicate. The observer agent can trigger the pattern agent, which can trigger the debate agent to challenge a belief that contradicts a new pattern. This is an emergent intelligence loop — the system updates its own worldview in response to new observations.

**Direction 7 — Population Simulation as Civilization Engine.** Following the `DevptPhases.md` plan already in `popula_dyn`, extend the simulation toward Phase 5 (social structures) and Phase 6 (conflict and civilization). When this is integrated with the unit intelligence layer, the system can detect emergent phenomena (city formation, resource collapse, inequality cycles) and store them as cross-unit patterns. The simulation becomes a synthetic experience generator for the intelligence engine.
