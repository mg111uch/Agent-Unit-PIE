# ArguGod Debate Engine

## Files

| Path | Purpose |
|------|---------|
| `modules/argu_god/engine/loop.py` | Main interaction loop |
| `modules/argu_god/engine/storage.py` | State + belief persistence |
| `modules/argu_god/engine/kernel_bridge.py` | Kernel signal bridge |
| `modules/argu_god/topics/<topic>/graph.json` | Argument graphs |
| `modules/argu_god/mindmaps/local_user/` | Beliefs, state, sessions |

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

## Status

- ✅ Signal emission to kernel
- ✅ Pattern detection  
- ✅ Session persistence
- ✅ Hypothesis engine
- ✅ Event timeline

See `orchestrator.md` for user commands.
See `kernel.md` for integration details.

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
