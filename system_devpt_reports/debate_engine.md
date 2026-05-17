# 🧠 ArguGod Debate Engine

ArguGod transforms the agent into a system that:

* Continuously learns from data
* Builds a structured knowledge base
* Improves its reasoning over time

> From execution → to intelligence → to pattern awareness

> **Interactive reasoning + debate + belief tracking system** with:
* 🧠 AI reasoning engine
* ⚖️ Debate simulator
* 📚 Knowledge explorer
* 🧬 Belief evolution tracker

# 🎮 ArguGod Modes (Slash Commands)

## `/argu explore <topic>`

Interactive guided exploration.

### Behavior:

* Shows one argument at a time
* User selects from **4 options only**

```
1. Agree (argument)
2. Counter (relevant opposing argument)
3. Explore / unsure
4. Write own response
```

* Stores response
* Moves to next argument
* Resumes from previous state

## (Planned Modes)

* `/argu debate` → deeper multi-step debate
* `/argu reflect` → summarize beliefs + contradictions
* `/argu expand` → grow knowledge base

# 🔄 Interaction Loop

```
Load topic graph
↓
Select next argument
↓
Fetch semantic counter (vector DB)
↓
Generate 3 options + 1 custom
↓
User selects
↓
Store response
↓
Update belief state
↓
Detect contradictions
↓
Repeat
```

---

# 🧠 Phase-wise Capabilities

## ✅ Phase 1 — Interaction Engine

* Slash command routing
* Argument navigation
* 4-option MCQ system
* Persistent interaction log
* Resume + no repetition

## ✅ Phase 2 — Debate + Retrieval

* Graph-based argument indexing
* Counterargument generation
* Semantic retrieval (vector RAG)
* Context-aware options
* Debate-style interaction

## ✅ Phase 2 Advanced — Vector Intelligence

* ChromaDB integration
* Sentence embeddings
* Semantic similarity search
* Relevant argument retrieval

## ✅ Phase 3 — Belief System

* Belief state tracking per argument
* Confidence scoring
* Belief history over time
* Contradiction detection
* Adaptive argument selection

---

# 🧠 Belief Model

Each argument stores:

```json
{
  "stance": "agree | disagree | neutral | custom",
  "confidence": 0.0–1.0,
  "history": [],
  "last_updated": ""
}
```

---

# ⚠️ Contradiction Detection

System detects:

> When user agrees with arguments that refute each other

Example:

```
⚠️ You agreed with both:
- Argument A
- Argument B (which refutes A)
```

---

# ⚡ Adaptive Intelligence

System prioritizes:

* Arguments user disagrees with
* Uncertain areas
* Conflicting beliefs

---

# 🔍 Retrieval System

## Graph RAG

* Uses argument relationships (edges)

## Vector RAG

* Uses semantic similarity (embeddings)

---

# 🎯 Key Constraints

* Only **4 options per question**
* Always include **custom response option**
* Break complex reasoning into multiple steps
* Never overwrite user history
* Maintain separation:

  * LLM knowledge
  * Human beliefs

# ARGU_GOD INTEGRATION

Convert from standalone system into module.
`modules/debate_engine/`
* debate_orchestrator.py
* contradiction_detector.py
* hypothesis_tester.py
* belief_tracker.py

Debate engine becomes **epistemic validation layer**, NOT main architecture.

---

# 🧠 System Evolution

The system evolves from:

```
Static Knowledge → Interactive Debate → Belief Tracking → Adaptive Intelligence
```

---