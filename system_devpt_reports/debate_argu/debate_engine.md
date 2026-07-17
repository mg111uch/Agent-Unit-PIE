# ArguGod Debate Engine

## Files

| Path | Purpose |
|------|---------|
| `modules/argu_god/engine/loop.py` | Argument graph loading + next-argument selection (`load_graph`, `get_next_argument`) |
| `modules/argu_god/engine/storage.py` | State + belief persistence (`interaction_log.json`, `belief_state.json`) |
| `modules/argu_god/engine/kernel_bridge.py` | Kernel signal bridge + session persistence |
| `modules/argu_god/engine/retriever.py` | Counter-argument retrieval (vector/semantic) |
| `modules/argu_god/engine/vector_store.py` | ChromaDB integration for argument embeddings |
| `modules/argu_god/engine/analyzer.py` | Contradiction detection |
| `modules/argu_god/engine/question_builder.py` | Structured question builder (`build_structured_question`) |
| `agent_core/tools/debate_ops.py` | Composite `debate_step` tool — bridges agent loop with debate engine |
| `modules/argu_god/topics/<topic>/graph.json` | Argument graphs (pre-defined, no LLM needed for questions) |
| `modules/argu_god/mindmaps/local_user/` | Beliefs, state, sessions |

---

## `/argu explore <topic>` — Debate Mode (via Agent Loop)

- `theism_atheism` (default topic)
- Add new topics in `modules/argu_god/topics/<topic>/graph.json`
- Explore topics through structured debate with belief tracking
- LLM acts as conversational moderator, calling `debate_step` tool

### Flow

```
/argu explore → ws_handler routes through agent loop
  → LLM receives debate-moderator instruction
  → LLM calls debate_step(topic) — ONE tool call per iteration
  → debate_step prepares question → engine.py yields "question" event
  → ws_handler relays to frontend → user answers
  → resolve_all_questions unblocks Event → debate_step processes response
  → returns {choice, stance, contradictions, next_argument, done}
  → LLM adds conversational framing, calls debate_step again
```

### Behavior

1. User sends `/argu explore <topic>` from browser frontend
2. `ws_handler.py` routes through agent loop with debate-moderator instruction
3. LLM calls `debate_step(topic)` for each argument iteration
4. User selects from **3 predefined options** (4th custom-text option added by frontend):
   ```
   1. Agree: I accept this argument
   2. Counter: I disagree
   3. Explore / unsure
   ```
5. Tool records response, updates beliefs, detects contradictions
6. Returns structured result to LLM, which adds conversational framing
7. LLM calls `debate_step` again until `done: true`

### Interaction Flow

```
LLM calls debate_step(topic="theism_atheism")
  → picks next argument from graph.json
  → creates _pending question → frontend shows argument + 3 options
  → user selects → tool processes response
  → returns {choice, stance, contradictions, next_argument, done}
LLM: "You disagreed with the Ontological Argument. "
     "Let me show you a counterpoint..."
  → calls debate_step again → repeat
  → when done=true → LLM wraps up with summary
```

### Two-Phase Tool Execution (engine.py)

`debate_step` runs in two phases within the same tool call (transparent to the LLM):

1. **Prepare phase** (`prepare_only=True`): picks next argument from graph.json, creates `_pending[session_id]` entry with question + `threading.Event`, returns the question dict (non-blocking)
2. **Engine yields** `{"type": "question"}` event → ws_handler sends to frontend
3. **Wait phase** (`prepare_only=False`): blocks on Event until `resolve_all_questions` is called from ws_handler, processes response (belief tracking, contradictions), returns result

Reuses `question_ops._pending` dict + `resolve_all_questions`/`cancel_questions` — no new question transport infrastructure needed. Questions come from pre-defined `graph.json` — zero LLM calls for question generation.

---

## External Context File Paths

Files/directories that the debate module (`modules/argu_god/`) reads or writes **outside its own directory tree**:

### Hardcoded Absolute Paths

| File | Line | Path |
|------|------|------|
| `modules/argu_god/llm_compiler.py` | 5 | `/home/manigupt/Hello/python/ai_agent/utils/gemini_question.md` |
| `modules/argu_god/llm_compiler.py` | 7 | `/home/manigupt/Hello/python/ai_agent/utils/gemini_answer.md` |
| `modules/argu_god/llm_compiler.py` | 18 | `/home/manigupt/Hello/python/ai_agent/agent_tools` |

### Imports Outside `modules/argu_god/`

| File | Line | Import | Mechanism |
|------|------|--------|-----------|
| `engine/kernel_bridge.py` | 11-14 | `from kernel.signals.signal_engine`, `kernel.memory.working_memory`, `kernel.hypothesis.hypothesis_engine`, `kernel.events.event_engine` | `sys.path` insert of codebase root (lines 7-9) |
| `engine/retriever.py` | 1 | `from argu_god.engine.vector_store import search_similar` | Depends on `modules/` on `sys.path` (added by `debate_ops.py` or `kernel_bridge.py`) |
| `agent_core/tools/debate_ops.py` | 15-27 | `from modules.argu_god.engine.{loop,storage,analyzer,kernel_bridge}` | Bridge imports |
| `agent_core/tools/debate_ops.py` | 27 | `from agent_core.tools.question_ops import _pending` | Shared pending-questions dict |
| `agent_core/tools/debate_ops.py` | 92 | `from modules.argu_god.engine.retriever import get_best_counter` | Lazy import inside function body |

### ChromaDB Persist Directory (Relative to CWD)

| File | Line | Path |
|------|------|------|
| `engine/vector_store.py` | 12 | `./chroma_db` |

### sys.path Modifications

| File | Path Added | Purpose |
|------|-----------|---------|
| `engine/kernel_bridge.py` (line 8-9) | Codebase root (`codebase/`) | Enables `from kernel.*` imports |
| `agent_core/tools/debate_ops.py` (line 10-13) | `codebase/modules/` | Enables `from modules.argu_god.*` imports |

### Internal Paths (inside `modules/argu_god/`, derived from `__file__`)

| File | Path | Purpose |
|------|------|---------|
| `engine/loop.py` (line 4-7) | `topics/{topic}/graph.json` | Reads argument graph |
| `engine/storage.py` (line 5-10) | `mindmaps/local_user/interaction_log.json` | Debate state |
| `engine/storage.py` (line 28-33) | `mindmaps/local_user/belief_state.json` | Belief state |
| `engine/kernel_bridge.py` (line 20-21) | `mindmaps/local_user/sessions/` | Session persistence |

---

## Run via Web Server

```bash
conda run -n myenv python server.py
# Frontend: /agent page, send "/argu explore theism_atheism"
```

---

## Status

| Capability | Status | Notes |
|------------|--------|-------|
| Argument navigation | ✅ | Via `debate_step` tool |
| 4-option question system | ✅ | 3 options + custom text (frontend adds 4th) |
| Belief tracking | ✅ | Per-argument stance + confidence |
| Contradiction detection | ✅ | On every response |
| Kernel signal emission | ✅ | Belief shifts, confidence changes, contradictions |
| Session persistence | ✅ | Via `kernel_bridge.save_debate_session` |
| Hypothesis engine | ✅ | Belief hypotheses + validation |
| Vector counter-arguments | ✅ | ChromaDB (retriever) |

---

## Under the Hood

### Topic Loading
- Loads argument graph from `topics/<topic>/graph.json`
- Each node = one argument with stance (pro/con/neutral)
- Each edge = logical relationship between arguments

### Argument Selection
- System prioritizes arguments user disagrees/neutral with
- Falls back to untested arguments
- Avoids repeating previously seen arguments

### User Response
User responds with one of **3 options** (4th custom-text added by frontend):

| Option | Meaning | Confidence |
|--------|---------|-------------|
| Agree | You accept this argument | 0.7 |
| Counter | You disagree | 0.7 |
| Explore | You're uncertain/curious | 0.5 |
| Custom | Typed response | 0.6 |

### Belief Tracking
- Stores your stance per argument
- Tracks confidence level
- Records history of changes

### Contradiction Detection
If you agree with arguments that contradict each other (via graph edges with `relation: "refutes"`):
```
⚠️ Potential contradiction detected:
- You agreed with both: Argument A AND Argument B
```

### Signal Emission
Every interaction emits signals via `kernel_bridge`:
- `belief_shift` — When stance changes
- `confidence_change` — When confidence updates
- `contradiction_detected` — When contradictions found

### Session Persistence
- Auto-saves on topic completion
- Sessions stored in `mindmaps/local_user/sessions/`
- Resume supported via `seen_arguments` in state

---

## Kernel Integration

```
User Response
    ↓
debate_step tool calls kernel_bridge internally:
  emit_belief_signal()       → belief_shift
  emit_confidence_signal()   → confidence_change
  emit_contradiction_signal()→ contradiction_detected
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

### Working Memory
After debate session:
- Belief shifts (per argument)
- Confidence changes
- Contradictions detected
- Session metadata

Retrieve with:
```python
kernel_retrieve(query="argument belief", limit=5)
```

---

## Interaction Loop (via debate_step tool)

```
LLM calls debate_step(topic)
  ↓
debate_step internally:
  Load topic graph
  ↓
  Select next argument (belief-aware)
  ↓
  Try to fetch semantic counter (vector DB)
  ↓
  Build structured question with 3 options
  ↓
  Create _pending[session_id] with threading.Event
  ↓  (engine.py yields "question" event to frontend)
  Wait for user response (block on Event)
  ↓
  Map choice → stance + confidence
  ↓
  Store response + update belief state
  ↓
  Detect contradictions
  ↓
  Find next argument
  ↓
  Return structured result to LLM
LLM adds conversational framing, calls debate_step again
```

---

## Belief Model

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

## Adaptive Intelligence

System prioritizes:
- Arguments user disagrees with
- Uncertain areas
- Conflicting beliefs
