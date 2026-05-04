# DebateGraph – Theism vs. Atheism Argument Web

**An open-source, community-driven, interactive web platform for mapping and debating the existence of God.**

DebateGraph is a multidimensional knowledge graph that visualizes arguments **for** and **against** the existence of God (or related metaphysical questions).  
Users can explore a force-directed web of nodes & edges, contribute new arguments/evidences, and engage in AI-assisted debate mode.

The project draws from philosophy, science (cosmology, biology, neuroscience), history, psychology, sociology, theology, and more — aiming for rigorous, balanced, evidence-based exploration.

Live demo: (coming soon)  
Production site: (planned)

## ✨ Core Features

- **Interactive multidimensional graph**  
  Force-directed visualization of arguments (nodes) and relationships (supports / attacks / evidences / related) using Cytoscape.js or similar  
  Color-coded sides: green (pro-theism), red (anti-theism / atheism), gray (neutral/claims)  
  Jump between nodes, expand neighbors, zoom/pan, search & filter

- **Community contributions**  
  Authenticated users can add/edit nodes (arguments, premises, evidences)  
  Suggest & create typed edges ("supports", "refutes", "evidences", etc.)  
  Upvote/downvote, simple moderation queue, version history basics

- **AI-powered Debate Mode**  
  Enter your own argument → LLM analyzes side & strength  
  Automatically finds / generates counters or supports from the existing graph  
  Simulates turn-based debate (user ↔ LLM)  
  One-click suggestion to add your point (or LLM's response) as new node(s)

- **Research-first foundation**  
  Nodes include short premise, detailed description, real-world examples, sources/links  
  seeded with classical & modern arguments (Anselm, Aquinas, Craig, Dawkins, Oppy, Swinburne, problem of evil, fine-tuning, evolutionary debunking, etc.)


### 🚧 In Progress / Planned
- [ ] Community contribution forms & moderation
- [ ] Debate mode prototype with LLM
- [ ] Authentication system
- [ ] Public live deployment

## 🚀 Quick Start (Development)

### Clone & run (example – adjust for your stack)

```bash
git clone https://github.com/YOUR-USERNAME/debategraph.git
cd debategraph

# Frontend
cd frontend
npm install
npm run dev

# Backend (FastAPI example)
cd ../backend
pip install -r requirements.txt
uvicorn main:app --reload

# Seed initial data (Python script)
python scripts/seed_arguments.py
```

### Environment 
- Always use `conda run -n myenv python [file]` for all executions.

## 🎮 Current Implementation (January 2026)

### Quick Start (Current Version)

```bash
cd python/ArguGod

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
conda run -n myenv python -m uvicorn main:app --reload

# Access the web interface
# Open http://localhost:8000 in your browser
```


# 🚀 Project Improvement Ideas (High Value)

Now the fun part — your project actually has strong potential.

---

## 🧠 1. Make it a “Thinking Engine” (BIG upgrade)

Right now:

> static compile → graph

Upgrade to:

👉 **interactive reasoning graph**

User clicks node → triggers:

* expand argument
* generate counterarguments
* refine evidence

---

## ⚡ 2. Real-time LLM Graph Growth

Instead of:

```text
Click compile → full graph
```

Do:

👉 streaming updates via WebSocket:

* new nodes appear live
* edges animate in

---

## 🧩 3. Argument Strength Scoring

You already have:

```json
confidence
```

Use it:

* node size = confidence
* edge thickness = strength

---

## 🧠 4. Debate Mode (killer feature)

Let user choose:

* Pro
* Con

Then:

* LLM generates attack/defense
* graph evolves dynamically

👉 Turns into **AI debate simulator**

---

## 🧬 5. Knowledge Evolution Tracking

You already started mindmap — expand it:

* track:

  * bias
  * contradictions
  * weak areas

👉 “You tend to favor X arguments”

---

## 🌐 6. Multi-topic Graph Merge

Combine topics:

```text
theism + morality + consciousness
```

👉 create **cross-domain reasoning graph**

---

## 🎯 7. Better Graph Layout (important)

Current:

```js
circle layout
```

Upgrade to:

* force-directed graph (d3-force)
* hierarchical (argument tree)

---

## 🔍 8. Click → Show Full Argument Panel

Instead of alert:

👉 show:

* premise
* evidence
* sources
* counterarguments

---

## 🧠 9. Auto-critique system

After graph build:

👉 run second LLM pass:

* detect weak arguments
* missing links
* logical fallacies

---

## ⚙️ 10. Replace File-based LLM system

Current:

```text
write file → subprocess → read file
```

Upgrade to:

* direct API call
* streaming response

👉 massive reliability gain

---

## 💡 11. Add “Graph Diff” (very powerful)

Compare:

```text
before vs after compile
```

👉 show:

* new arguments
* removed ones
* confidence change

---

## 🧠 12. Turn into Product Idea

This can become:

* AI research tool
* debate trainer
* philosophy engine
* knowledge explorer

---

# 🧠 Final Insight

Right now your system is:

```text
LLM → static graph
```

To make it powerful:

```text
LLM ↔ Graph ↔ User ↔ Feedback loop
```

👉 That’s where it becomes **unique**

---
