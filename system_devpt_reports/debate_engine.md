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

---

# 📖 How to Use ArguGod

## Starting Debate Mode

To start exploring a topic through debate:

```python
# In the agent, run:
from argu_god.engine.loop import run_explore_loop

# Available topics
# - "theism_atheism" (default example)
# - Any topic in modules/argu_god/topics/

# Start exploring
run_explore_loop("theism_atheism")
```

Or via the FastAPI server:

```bash
cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase
conda run -n myenv python -m argu_god.main
# Open http://localhost:8000 in browser
```

---

## What Happens Under the Hood

### 1. Topic Loading
- Loads argument graph from `topics/<topic>/graph.json`
- Each node = one argument with stance (pro/con/neutral)
- Each edge = logical relationship between arguments

### 2. Argument Selection
- System prioritizes arguments user disagrees/neutral with
- Falls back to untested arguments
- Avoids repeating previously seen arguments

### 3. User Response
User responds with one of **4 options**:

| Option | Meaning | Confidence |
|--------|---------|-------------|
| 1 (Agree) | You accept this argument | 0.7 |
| 2 (Counter) | You disagree | 0.7 |
| 3 (Explore) | You're uncertain/curious | 0.5 |
| 4 (Write own) | Custom response | 0.6 |

### 4. Belief Tracking
- Stores your stance per argument
- Tracks confidence level
- Records history of changes

### 5. Contradiction Detection
If you agree with arguments that contradict each other:
```
⚠️ Potential contradiction detected:
- You agreed with both: Argument A AND Argument B
```

### 6. Signal Emission to Kernel
Every interaction emits signals to the kernel:
- `belief_shift` - When stance changes
- `confidence_change` - When confidence updates
- `contradiction_detected` - When contradictions found
- `observation` - Topic start/end

### 7. Session Persistence
- Auto-saves on exit or topic completion
- Prompts to resume if returning to same topic
- Sessions stored in `mindmaps/local_user/sessions/`

---

## Expected Interaction Flow

```
Exploring topic: theism_atheism
Found previous session on theism_atheism. Resume? (y/n): n

Arguments for: Does God exist?

[Argument 1 - Pro]
The existence of moral law: If God does not exist, 
objective moral values do not exist. But objective 
moral values do exist. Therefore, God exists.

1. Agree (argument)
2. Counter (relevant opposing argument)
3. Explore / unsure
4. Write own response
Select option (1-4 or 'exit'): 1

You seem to agree. Let's test this with a counterpoint next.

⚠️ Potential contradiction detected:
- You agreed with both: Argument 1 AND Argument 5

Saved. Moving to next...
```

---

## Response Options Explained

### Option 1: Agree
- System records your stance as "agree"
- Records confidence 0.7
- Tests next argument with opposing view
- Used when you find argument convincing

### Option 2: Counter  
- System records your stance as "disagree"
- Records confidence 0.7
- Tests next argument (potentially same side)
- Used when you reject the argument

### Option 3: Explore/Unsure
- System records your stance as "neutral"
- Records confidence 0.5
- Shows more arguments on this topic
- Used when you need more information

### Option 4: Write Own Response
- System records custom response
- Records confidence 0.6
- Stored for later analysis
- Used for nuanced positions

---

## Slash Commands (Current)

| Command | Status | Description |
|---------|--------|-------------|
| `/argu explore <topic>` | ✅ Working | Interactive guided exploration |

Slash Commands (Planned):
| `/argu debate` | 🔜 | Deeper multi-step debate |
| `/argu reflect` | 🔜 | Summarize beliefs + contradictions |
| `/argu expand` | 🔜 | Grow knowledge base |

---

## Kernel Integration (What Gets Tracked)

### Signals Emitted
```
User Response
    ↓
kernel_bridge.emit_belief_signal()     → belief_shift
kernel_bridge.emit_confidence_signal()→ confidence_change
kernel_bridge.emit_contradiction_signal() → contradiction_detected
    ↓
signal_engine persists to episodic memory
    ↓
belief_signal_handler processes:
  - stores in working memory
  - detects patterns
  - emits pattern_detected
    ↓
Accessible via kernel_retrieve tool
```

### Working Memory Contents
After debate session:
- Belief shifts (per argument)
- Confidence changes
- Contradictions detected
- Session metadata

Retrieve with kernel tools:
```python
kernel_retrieve(query="argument belief", limit=5)
```

---

## Session Resume

When you return to a previously explored topic:

```
Exploring topic: theism_atheism
Found previous session on theism_atheism. Resume? (y/n): y
Resuming with 12 arguments already seen.
```

Sessions are auto-saved:
- On `exit` command
- When all arguments exhausted
- Available at `mindmaps/local_user/sessions/`

---

## Files & Locations

| Path | Purpose |
|------|---------|
| `modules/argu_god/engine/loop.py` | Main interaction loop |
| `modules/argu_god/engine/storage.py` | State + belief persistence |
| `modules/argu_god/engine/kernel_bridge.py` | Kernel signal bridge |
| `modules/argu_god/topics/<topic>/graph.json` | Argument graphs |
| `modules/argu_god/mindmaps/local_user/` | Beliefs, state, sessions |

---

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

# 🧠 Belief Hypothesis Flow

When user responds to arguments, beliefs are tracked as hypotheses:

```
1. User responds (1-4)
   ↓
2. create_belief_hypothesis(argument, stance, confidence, topic)
   ↓
3. Belief stored in belief_state.json
   ↓
4. Signal emitted: belief_shift → kernel signal_engine
   ↓
5. If contradiction detected:
   a. get_hypothesis_for_argument(both arguments)
   b. add_belief_evidence(hyp, counter_arg, supports=False)
   c. validate_belief_hypothesis(hyp)
   ↓
6. Hypothesis status updated:
   - support_count/(support+contradict) >= 0.7 → "supported"
   - support_count/(support+contradict) <= 0.3 → "rejected"
   - else → "uncertain"
```

### Hypothesis Functions

```python
# Create hypothesis from belief
create_belief_hypothesis(argument_name, stance, confidence, topic)

# Add evidence when contradictions found
add_belief_evidence(hypothesis_id, evidence_id, supports=True/False)

# Validate - returns status
validate_belief_hypothesis(hypothesis_id)
# Returns: {validation_score, support_count, contradiction_count, status}

# Get summary for topic
get_belief_summary(topic)
```

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

---

# 🧠 System Evolution

The system evolves from:

```
Static Knowledge → Interactive Debate → Belief Tracking → Adaptive Intelligence
```

---

# 🔗 KERNEL INTEGRATION (Completed)

## Phase 1: Signal Emission (Completed)

ArguGod now emits signals to kernel on:

- **belief_shift** - When user changes stance on an argument
- **confidence_change** - When confidence updates
- **contradiction_detected** - When contradictions detected
- **observation** - Topic exploration start/end

### Files Changed:
- `modules/argu_god/engine/kernel_bridge.py` - Signal emission bridge
- `modules/argu_god/engine/loop.py` - Integrated signal calls

## Phase 2: Pattern Detection (Completed)

Kernel signal handlers now:

- Store belief changes in working memory
- Detect contradiction patterns
- Emit pattern_detected signals for retrieval

### Files Changed:
- `kernel/signals/belief_signal_handler.py` - Signal handlers
- `agent_tools.py` - Handler registration on startup

## Phase 3: Session Persistence (Completed)

Added debate session save/load for session resume:

- `save_debate_session()` - Saves state + beliefs to disk + working memory
- `load_debate_session()` - Loads previous session
- `list_debate_sessions()` - Lists all saved sessions
- `get_current_session_info()` - Gets most recent session info

Loop now:
- Prompts to resume if previous session exists for topic
- Auto-saves on exit
- Auto-saves when topic completed

### Files Changed:
- `modules/argu_god/engine/kernel_bridge.py` - Session functions
- `modules/argu_god/engine/loop.py` - Resume prompt + auto-save

## Phase 4: Hypothesis Engine Integration (Completed)

Connected belief system to kernel hypothesis engine:

- `create_belief_hypothesis()` - Creates hypothesis from belief
- `add_belief_evidence()` - Adds supporting/contradicting evidence
- `validate_belief_hypothesis()` - Validates hypothesis status
- `get_hypothesis_for_argument()` - Gets existing or creates new
- `get_belief_summary()` - Gets all beliefs for topic

Loop now:
- Creates hypothesis on each belief response
- Adds contradiction evidence when contradictions detected
- Validates hypotheses and updates status

### Files Changed:
- `modules/argu_god/engine/kernel_bridge.py` - Added hypothesis functions
- `modules/argu_god/engine/loop.py` - Hypothesis integration

## Phase 5: Event Timeline Tracking (Completed)

Connected debate events to kernel event engine for timeline tracking:

- `emit_debate_event()` - Generic debate event emitter
- `emit_session_start_event()` - Session start/resume
- `emit_argument_viewed_event()` - Argument shown to user
- `emit_user_response_event()` - User responds to argument
- `emit_belief_changed_event()` - Belief stance changes
- `emit_contradiction_event()` - Contradiction detected
- `emit_session_end_event()` - Session ends

Loop now tracks full timeline:
- Session start/resume events
- Argument viewed events
- User response events
- Belief change events
- Contradiction events
- Session end events

### Files Changed:
- `modules/argu_god/engine/kernel_bridge.py` - Added event functions
- `modules/argu_god/engine/loop.py` - Event integration

## Integration Flow

```
User responds in debate
    ↓
ArguGod updates belief state
    ↓
kernel_bridge emits signals:
  - belief_shift
  - confidence_change
  - contradiction_detected
    ↓
signal_engine persists → episodic memory
    ↓
belief_signal_handler:
  - stores in working memory
  - detects patterns
  - emits pattern_detected
    ↓
Kernel: patterns available for retrieval
```

---

## Next Development Phases

### Phase 6: Enhanced Debate Features

| Feature | Description |
|---------|-------------|
| Debate Analytics | Show session stats (arguments seen, time, belief changes) |
| Progress Indicator | "5/23 arguments explored" |
| Export Beliefs | Export belief_state.json / belief graph |
| Topic Browser | List and select from available topics |

### Phase 7: Multi-Person Debate

| Feature | Description |
|---------|-------------|
| Multiple Perspectives | Store beliefs per user/persona |
| Side Tracking | Track which side user favors |
| Argument Quality | Score arguments by evidence strength |
| Debate Summary | Generate summary report |

### Phase 8: Advanced Reasoning

| Feature | Description |
|---------|-------------|
| Cross-Topic Linking | Connect beliefs across topics |
| Recursive Counterarguments | Explore counter-counterarguments |
| Evidence Search | Auto-find supporting evidence |
| belief_graph Visualization | Render belief network |

### Phase 9: Self-Evolution

| Feature | Description |
|---------|-------------|
| Auto-Topic Generation | Generate new topics from knowledge |
| Hypothesis Chaining | Link related hypotheses |
| Pattern → New Arguments | Generate arguments from patterns |
| System Self-Check | Detect internal contradictions |

---

## Quick Start for Next Session

```python
# 1. Run tests to verify integration
cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase
conda run -n myenv python -m pytest tests/agent_test.py

# 2. Start debate session
from argu_god.engine.loop import run_explore_loop
run_explore_loop("theism_atheism")

# 3. Or start web server
cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase
conda run -n myenv python -m argu_god.main
# Open http://localhost:8000
```

---