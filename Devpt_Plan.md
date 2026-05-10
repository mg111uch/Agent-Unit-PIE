# Agent_Unit_PIE — Development Plan

## Project Vision

**Agent_Unit_PIE** is a Universal Unit Pattern Intelligence Engine — a system that continuously observes, structures, compresses, pattern-detects, simulates, predicts, and improves across all types of units (humans, organizations, cities, countries, codebases, simulations).

The system transforms raw observations into evolving structured knowledgebases using a signal-centric architecture that scales beyond LLM context limits.

---

## Core Concept: Everything is a Unit

A **Unit** is any entity that has: state, signals, behaviors, relations, patterns, and a timeline.

### Supported Unit Types

| Category | Examples |
|----------|----------|
| Human | body, mind, behavior, psychology |
| Organization | company, agency, institution |
| Geographic | city, state, country, region |
| Digital | codebase, server, software project |
| Abstract | market, economy, policy, ideology |
| Simulated | population agents, digital twins |

### Universal Unit Schema

```json
{
  "unit_id": "unique_id",
  "unit_type": "human|company|city|...",
  "subtype": "optional_specific_type",
  "state": {},
  "traits": {},
  "resources": {},
  "signals": [],
  "events": [],
  "patterns": [],
  "relations": [],
  "subunits": [],
  "timeline": [],
  "health_score": 0.0,
  "risk_flags": [],
  "improvement_suggestions": [],
  "digital_twin": {}
}
```

---

## System Architecture

```
agent_unit_pie/
├── kernel/                    # Core cognition engine
│   ├── unit_schema.py
│   ├── signal_schema.py
│   ├── pattern_schema.py
│   ├── relation_schema.py
│   ├── hypothesis_schema.py
│   ├── memory_engine.py       # Multi-layer memory system
│   ├── signal_engine.py       # Extract structured signals
│   ├── pattern_engine.py     # Detect patterns
│   ├── relation_engine.py    # Build relationships
│   ├── timeline_engine.py     # Temporal reasoning
│   ├── hypothesis_engine.py   # Generate/test hypotheses
│   ├── compression_engine.py  # Recursive self-compression
│   ├── retrieval_engine.py    # Layered cognitive retrieval
│   └── ontology_engine.py     # Define and manage ontologies
│
├── modules/                   # Domain-specific engines
│   ├── debate_engine/         # Contradiction detection
│   ├── bodymap/              # Health tracking
│   ├── mindmap/              # Psychological modeling
│   ├── behavior_engine/       # Human behavior mapping
│   ├── economic_engine/       # Financial/economic intelligence
│   ├── spatial_engine/        # Geographic/spatial intelligence
│   ├── simulation_connector/  # Connect to simulation engine
│   ├── digital_twin_engine/   # Persistent world models
│   └── ingestion_engine/      # Multi-modal data ingestion
│
├── simulation_engine/         # Universal simulation kernel
│   ├── core/
│   │   ├── unit_agent.py      # Generic unit-based agent
│   │   ├── unit_registry.py
│   │   └── world_engine.py
│   ├── behaviors/             # Modular behavior library
│   │   ├── move.py
│   │   ├── consume.py
│   │   ├── exchange.py
│   │   ├── reproduce.py
│   │   ├── learn.py
│   │   └── ...
│   └── configurations/        # YAML-based simulation definitions
│
├── llm/                       # LLM orchestration
│   ├── providers/             # Gemini, OpenAI, Anthropic
│   ├── orchestrator.py
│   ├── extractor.py
│   ├── summarizer.py
│   └── hypothesis_generator.py
│
├── units/                     # Unit knowledge bases
│   ├── humans/
│   ├── organizations/
│   ├── cities/
│   ├── countries/
│   ├── codebases/
│   ├── simulations/
│   └── global_patterns/       # Cross-unit patterns
│
├── storage/                   # Hybrid storage layers
│   ├── raw_data/              # Layer 1: Archive
│   ├── signals/               # Layer 2: Structured signals
│   ├── events/                # Layer 3: Important events
│   ├── patterns/              # Layer 4: Pattern memory
│   ├── knowledge/             # Layer 5: Abstract knowledge
│   ├── hypotheses/            # Layer 6: Uncertain ideas
│   └── working_memory/        # Layer 7: Active context
│
├── tools/
└── visualization/
```

---

## Core Data Flow

```
Observe → Extract → Store → Detect Pattern → Update Knowledgebase
     ↓
  [Signals → Patterns → Hypotheses → Predictions → Simulations]
     ↓
[Self-Compress → Working Memory → LLM Reasoning → Action]
```

---

## Major Engine Specifications

### 1. Signal Engine

Converts raw observations into structured signals.

**Universal Signal Format:**
```json
{
  "signal_id": "sig_xxx",
  "unit_id": "unit_xxx",
  "signal_type": "pain|bug_frequency|cpu_spike|...",
  "category": "body|code|devops|economic|...",
  "location": "body_region|file|server|...",
  "intensity": 0-10,
  "timestamp": "ISO8601",
  "metadata": {},
  "source": "conversation|pdf|website|...",
  "confidence": 0.0-1.0,
  "trend": "increasing|decreasing|stable"
}
```

**Signal Extraction Examples:**

| Unit Type | Observation | Signal Generated |
|-----------|-------------|------------------|
| Human Body | "knee hurts after running" | pain, intensity=3, trigger=running |
| Codebase | repeated auth failures | error_frequency, increasing |
| City | newspaper reports | economic_stress, infrastructure_gap |
| Stock | quarterly filing | revenue_growth, debt_pressure |

### 2. Pattern Engine

Detects patterns from signals across temporal, correlation, trend, and structural dimensions.

**Pattern Types:**

| Type | Description | Example |
|------|-------------|---------|
| Temporal | Repeated over time | knee pain every Monday |
| Trend | Increasing/decreasing | bug frequency rising |
| Correlation | A correlates with B | stress → headaches |
| Contradiction | A and not-A both true | contradictory beliefs |
| Structural | Missing data/weak coverage | no test coverage |
| Recursive | Self-reinforcing loops | stress → poor sleep → more stress |

### 3. Self-Compressing Memory (7 Layers)

LLMs have limited context. The system recursively compresses information:

| Layer | Purpose | Size | LLM Access |
|-------|---------|------|------------|
| 1. Raw Observation | Documents, podcasts, reports | Unlimited | Never direct |
| 2. Signal Memory | Structured observations | Large | Rare |
| 3. Event Memory | Important events only | Medium | Selective |
| 4. Pattern Memory | Detected patterns | Small | Frequent |
| 5. Knowledge Memory | Abstract models | Tiny | Regular |
| 6. Hypothesis Memory | Evolving theories | Very small | When testing |
| 7. Working Memory | Active context | 5-50 KB | Always |

**Cognitive Compilation Pipeline:**
```
raw_data → signals → patterns → abstractions → compressed_model → working_memory_packet
```

### 4. Retrieval Engine

Layered retrieval instead of pure vector similarity:

1. **Unit relevance** — Is this unit relevant?
2. **Relation relevance** — Are units connected?
3. **Temporal relevance** — Is timing relevant?
4. **Pattern relevance** — Are patterns relevant?
5. **Semantic similarity** — Vector comparison (secondary)

### 5. Hypothesis Engine

The system automatically generates and tests hypotheses:

```json
{
  "hypothesis": "Cities near river systems maintain stronger cultural continuity",
  "evidence_count": 45,
  "contradiction_count": 12,
  "confidence": 0.65,
  "test_results": []
}
```

### 6. Digital Twin Engine

Continuously updated synthetic models of real units.

**Human Twin Tracks:** behavior, speech, beliefs, habits, psychology, health, astrology, social patterns, decision trends

**City Twin Tracks:** economy, population, migration, crime, infrastructure, culture, transport, spatial patterns, historical events, politics

**Company Twin Tracks:** revenue, org structure, capital allocation, risk, market position, leadership behavior

### 7. Behavioral Intelligence Engine

Tracks human behavior maps including:
- speech patterns, decision patterns, emotional cycles
- social tendencies, conflict tendencies, learning style
- belief evolution, risk behavior, goal persistence

**Cross-references behavior maps with astrology/soft science hypotheses:**
```json
{
  "hypothesis_system": "vedic_astrology",
  "claim": "mars_in_1st_house_correlates_with_assertiveness",
  "confidence": 0.31,
  "supporting_cases": 154,
  "contradicting_cases": 93
}
```

### 8. Economic Intelligence Engine

| Component | Purpose |
|-----------|---------|
| capital_flow_engine | Track fund movements, detect anomalies |
| opportunity_engine | Find underserved sectors, high-leverage industries |
| corruption_engine | Detect abnormal routing, budget mismatches |
| gdp_engine | Model productivity, find friction points |
| investment_engine | Personal advisor for stocks/companies |

### 9. Debate/Contradiction Engine

Epistemic validation — finds contradictions, tests hypotheses, simulates counterfactuals, compares conflicting models.

---

## Simulation Engine Refactor

Current: civilization-specific classes (FarmerAgent, TraderAgent, HealerAgent)

Target: Universal Unit Simulation Engine

**Key Changes:**

1. Replace role-based inheritance with data-driven unit composition
2. Create `UnitAgent` base class with configurable behaviors
3. Modular behaviors as separate functions:
   - move, consume, exchange, reproduce, gather_resource, heal, produce_tool, learn, compete, cooperate
4. Generic resource system (food, money, energy, knowledge, cpu, trust)
5. Externalized YAML-based simulation definitions

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

## Knowledgebase Organization

Hierarchical markdown structure for human readability + LLM access:

```
units/
├── city/
│   └── lucknow/
│       ├── identity/
│       │   └── summary.md
│       ├── economy/
│       │   ├── metro_expansion.md
│       │   ├── informal_sector.md
│       │   └── patterns.md
│       ├── politics/
│       ├── infrastructure/
│       ├── culture/
│       ├── transport/
│       ├── spatial/
│       ├── risks/
│       ├── patterns/
│       ├── hypotheses/
│       └── timeline/
│           ├── 1920.md
│           ├── 1980.md
│           └── 2026.md
├── company/
│   └── tcs/
│       ├── financials/
│       ├── leadership/
│       └── patterns.md
└── human/
    └── user_001/
        ├── body/
        ├── mind/
        ├── finance/
        ├── behavior/
        └── system_summary.md
```

**Small modular files instead of giant documents** — enables structural retrieval.

---

## Storage Architecture

| Layer | Technology | Purpose |
|-------|------------|---------|
| Source of Truth | Markdown + JSON | Human-readable, LLM-editable |
| Machine State | Structured JSON | Fast parsing |
| Relations | Graph (internal) | Causality, dependencies |
| Semantic Index | Vector DB (optional) | Discovery only |
| Patterns | Pattern DB | Emergent abstractions |
| Timeline | Time-series | Temporal evolution |

**Important:** Vector DB is secondary — NOT primary cognition.

---

## Development Phases

### Phase 1: Kernel Foundation
- [ ] Create universal unit schema
- [ ] Create signal schema and extraction system
- [ ] Create pattern schema and detection
- [ ] Build basic memory engine (7 layers)
- [ ] Create retrieval engine with layered scoring
- [ ] Build LLM orchestration layer

### Phase 2: Core Loop Implementation
- [ ] Implement observe → extract → store → pattern → update cycle
- [ ] Create hypothesis engine
- [ ] Build self-compression pipeline
- [ ] Implement contradiction detection (extend argu_god)

### Phase 3: Unit Refactor
- [ ] Convert all existing systems to unit-centric model
- [ ] Refactor simulation engine to universal UnitAgent
- [ ] Create behavior registry
- [ ] Build externalized simulation configurations

### Phase 4: Digital Twins
- [ ] Build digital twin engine
- [ ] Create human twin (body + mind + behavior)
- [ ] Create city twin (economy + spatial + social)
- [ ] Create company twin (growth + structure + market)

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

---

## Starting Point Recommendation

Start with **ONE unit type** to prove architecture:
- **Human + Codebase** (since you interact with both daily)

First concrete steps:
1. Create `kernel/unit_schema.py`
2. Create `kernel/signal_schema.py`
3. Create `storage/signals/` directory
4. Build simple signal extraction from conversations
5. Implement basic pattern detection
6. Build unit filesystem structure

---

## Key Principles

1. **Signals, not documents** — Everything eventually becomes signal → pattern → hypothesis
2. **Schema-first** — Define structure before building
3. **Self-compressing** — System must recursively compress itself to scale
4. **Modular** — Core kernel + independent domain modules
5. **Evolutionary** — KB evolves from LLM latent prior → evidence-grounded model
6. **Confidence-tracked** — Every claim needs evidence, source, confidence, counterarguments

---

## Final Vision

Agent_Unit_PIE becomes:

**A Recursive World Modeling Infrastructure**

that continuously:
- observes reality
- compresses knowledge
- finds patterns
- simulates futures
- generates strategies
- improves itself

across every type of unit — human, organization, city, country, codebase, market, simulation.