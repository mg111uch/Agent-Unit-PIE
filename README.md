# 🧠 Agent_Unit_PIE + ArguGod

### Pattern Intelligence Engine + Human-in-Loop Argument Intelligence System

---

# 🚀 Overview

**Agent_Unit_PIE** is a tool-driven autonomous AI agent designed to :

> Observe → Execute → Learn → Store → Evolve

It is extended with **ArguGod**, a reasoning engine that enables:

> Human-in-loop argument exploration, debate, and belief evolution.

---

# 🧩 System Architecture

```
User ↔ Agent_Unit_PIE (LLM + Tools)
           ↓
      Command Router
           ↓
   ┌───────────────┐
   │ ArguGod Engine│
   └───────────────┘
           ↓
   ┌───────────────┐
   │ Knowledge Base│ (Graph + Vector DB)
   └───────────────┘
           ↓
   ┌───────────────┐
   │ Human Mindmap │ (Beliefs + History)
   └───────────────┘
```

---

# 🧠 Core Philosophy

This system is NOT a chatbot.

It is a:

> **Belief Evolution Engine**

Where:

* LLM = knowledge + reasoning
* Human = evaluator
* System = tracks and evolves beliefs over time

---

# ⚙️ Agent_Unit_PIE (Core Engine)

## Features

* 🔁 Multi-step tool reasoning loop
* 🛠️ Tool execution (filesystem + shell)
* 🧠 Persistent memory via markdown
* 🧾 Structured knowledge extraction
* ⚙️ Safe file editing (`write_to_file`)
* 📂 Workspace sandboxing

---

## Agent Loop

```
User Input
   ↓
LLM decides tool
   ↓
Tool executes
   ↓
Result returned
   ↓
Loop until final answer
```

---

## Available Tools

* `read_file`
* `list_files`
* `write_to_file`
* `execute_command`

---

## Design Principles

* Tool-first reasoning
* Deterministic actions
* Read before write
* Structured memory
* Minimal hallucination

---

# 🧠 ArguGod Engine

ArguGod transforms the agent into:

> **Interactive reasoning + debate + belief tracking system**

---

# 📚 Knowledge Base

## 1. Argument Graph (graph.json)

Each topic contains:

```
topics/{topic}/graph.json
```

Structure:

```json
{
  "nodes": [arguments],
  "edges": [relations: supports | refutes | related]
}
```

---

## 2. Vector Database (Semantic Layer)

* Uses **ChromaDB**
* Stores embeddings of arguments
* Enables semantic retrieval (vector RAG)

---

## 3. Mindmaps

### Interaction Log

Tracks all user interactions:

```
mindmaps/local_user/interaction_log.json
```

---

### Belief State (Phase 3)

Tracks user beliefs:

```
mindmaps/local_user/belief_state.json
```

---

# 🎮 ArguGod Modes (Slash Commands)

---

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

---

## (Planned Modes)

* `/argu debate` → deeper multi-step debate
* `/argu reflect` → summarize beliefs + contradictions
* `/argu expand` → grow knowledge base

---

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

---

## ✅ Phase 1 — Interaction Engine

* Slash command routing
* Argument navigation
* 4-option MCQ system
* Persistent interaction log
* Resume + no repetition

---

## ✅ Phase 2 — Debate + Retrieval

* Graph-based argument indexing
* Counterargument generation
* Semantic retrieval (vector RAG)
* Context-aware options
* Debate-style interaction

---

## ✅ Phase 2 Advanced — Vector Intelligence

* ChromaDB integration
* Sentence embeddings
* Semantic similarity search
* Relevant argument retrieval

---

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

# 📂 Project Structure (Simplified)

```
agent.py                  # Core agent loop
system_instruction.md     # Tool usage rules

argu_god/
│
├── engine/
│   ├── cli.py
│   ├── loop.py
│   ├── storage.py
│   ├── question_builder.py
│   ├── retriever.py
│   ├── vector_store.py
│   ├── analyzer.py
│
├── topics/
│   └── {topic}/
│       ├── graph.json
│       └── wiki/
│
├── mindmaps/
│   └── local_user/
│       ├── interaction_log.json
│       └── belief_state.json
```

---

# 🎯 Key Constraints

* Only **4 options per question**
* Always include **custom response option**
* Break complex reasoning into multiple steps
* Never overwrite user history
* Maintain separation:

  * LLM knowledge
  * Human beliefs

---

# 🧠 System Evolution

The system evolves from:

```
Static Knowledge → Interactive Debate → Belief Tracking → Adaptive Intelligence
```

---

# 🚀 Vision

This project aims to become:

* 🧠 AI reasoning engine
* ⚖️ Debate simulator
* 📚 Knowledge explorer
* 🧬 Belief evolution tracker

---

# 🔮 Future Roadmap

* Bias detection
* Persuasion tracking
* Multi-agent debate simulation
* Real-time graph visualization
* Cross-topic reasoning graphs
* Self-improving knowledge base

---

# ⚠️ Limitations

* No parallel execution
* Basic contradiction logic
* Limited reasoning depth (Phase 3)
* Requires clean graph data

---

# 🧠 Final Insight

This system is not about answering questions.

It is about:

> **Improving how humans think.**

---

# 🤝 Contributing

This is an experimental system combining:

* AI agents
* knowledge graphs
* human cognition

Contributions and ideas are welcome.

---

# 📜 License

MIT (or define as needed)

---
