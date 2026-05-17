# Claude Development Plan

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

# ⚠️ Important Files

* kernel/observation_pipeline.py
    FIRST integration backbone.
    Connects ingestion → events → signals → patterns.

* kernel/compression_engine.py
    Critical for infinite KB scaling.
    Prevents memory explosion.

* kernel/memory/working_memory_generator.py
    MOST IMPORTANT LLM-context file.
    Generates compressed cognition packets.

* kernel/memory/memory_router.py
    Routes episodic/semantic/pattern memory access.

* kernel/retrieval/unit_retriever.py
    Enables ontology/unit-aware retrieval.

* kernel/retrieval/pattern_retriever.py
    Retrieves high-level intelligence abstractions.

* storage/unit_storage.py
    Converts fragmented storage into unit-centric storage.

* storage/pattern_storage.py
    Persistent global pattern memory layer.

* simulation_engine/unit_agent.py
    Replaces FarmerAgent/TraderAgent architecture.

* simulation_engine/behavior_registry.py
    Enables modular reusable behaviors.

* simulation_engine/event_bridge.py
    Connects simulation outputs into kernel cognition pipeline.

* ingestion/observation_extractor.py
    Converts raw docs/web/news into observations/signals.

* llm/context_builder.py
    Builds optimized context using working memory.

* units/cities/city_initializer.py
    First real-world pilot unit for architecture validation.

---

# 🚧 Development Direction

## The current focus is:

```text
1. Kernel refactor
2. Universal ontology
3. Unit-centric architecture
4. Signal/event/pattern pipeline
5. Hierarchical memory
6. Universal simulation engine
7. Digital twin infrastructure
8. Economic intelligence systems
9. Self-evolving cognition
```

## Starting Point Recommendation
* Connect old systems to new kernel.
* Create `storage/signals/` directory
* Connect simulation outputs to kernel events/signals.
* Build simple signal extraction from conversations.
* Implement basic pattern detection.

## WHAT YOU SHOULD NOT GENERATE YET

Avoid these until architecture stabilizes:

astrology engine
GDP optimizer
stock predictor
corruption detector
autonomous agents
global human DB

## Future Roadmap

* Bias detection
* Persuasion tracking
* Multi-agent debate simulation
* Real-time graph visualization
* Cross-topic reasoning graphs
* Self-improving knowledge base

## Development Phases

### Phase 1: Kernel Foundation
- [X] Create universal unit schema
- [X] Create signal schema and extraction system
- [X] Create pattern schema and detection
- [X] Build basic memory engine (7 layers)
- [X] Create retrieval engine with layered scoring
- [X] Build LLM orchestration layer

### Phase 2: Core Loop Implementation
- [X] Implement observe → extract → store → pattern → update cycle
- [X] Create hypothesis engine
- [X] Build self-compression pipeline
- [ ] Implement contradiction detection (extend argu_god)

### Phase 3: Unit Refactor
- [X] Convert all existing systems to unit-centric model
- [X] Refactor simulation engine to universal UnitAgent
- [X] Create behavior registry
- [X] Build externalized simulation configurations

### Phase 4: Digital Twins
- [X] Build digital twin engine
- [X] Create human twin (body + mind + behavior)
- [X] Create city twin (economy + spatial + social)
- [X] Create company twin (growth + structure + market)

### Phase 5: Intelligence Engines
- [ ] Build economic intelligence engine
- [ ] Build behavioral intelligence engine
- [ ] Build spatial/temporal engine
- [ ] Build opportunity discovery engine
- [ ] Build corruption detection engine

### Phase 6: Advanced Systems
- [ ] Cross-unit pattern extraction (global patterns)
- [ ] Simulation ↔ Real-world feedback loop
- [ ] Autonomous self-reorganization
- [ ] Strategic recommendation engine

## 5. Development Phases

**1.4 Replace the LLM pipeline:**

Create `kernel/llm_client.py` with a single `call_llm(prompt, system, model, expect_json=True)` function that:
- Makes a direct API call (no subprocess, no file bridge)
- Strips markdown code fences
- Validates JSON if `expect_json=True`
- Retries once on invalid JSON
- Returns the parsed object or raises a structured error

All LLM calls in the system go through this function. Never write another file-based bridge.

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
