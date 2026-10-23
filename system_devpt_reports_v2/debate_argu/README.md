# ArguGod Debate Engine (Level 1)

> Code: `$PIE_ROOT/codebase/modules/argu_god/` + bridge `agent_core/tools/debate_ops.py` · Topic data is stored by the kernel (`engine/topic_store.py`) — see `kernel/README.md`. Master doc: `README.md`.
> This doc **corrects** three contradictions found between the old debate README and the kernel manual (DBT-01/02/03); items marked ❓ must be confirmed by the coding agent.

## 1. Role

ArguGod is the **epistemic validation engine** and human-belief tracker: contradiction detection, counter-argument generation, hypothesis testing, evidence comparison, uncertainty analysis, belief tracking, perspective exploration, simulation of alternative viewpoints. System evolution: `Static knowledge → Interactive debate → Belief tracking → Adaptive intelligence → Recursive epistemic intelligence`.

**Constraints:** only **4 options per question** (3 predefined + always a custom-text option added by the frontend); break complex reasoning into steps; **never overwrite user history**; keep **LLM knowledge separate from human beliefs**. Currently single-user (`local_user`).

## 2. Code map

| Path | Purpose |
|---|---|
| `engine/loop.py` | argument graph loading + next-argument selection (`load_graph`, `get_next_argument`) |
| `engine/storage.py` | state + belief persistence (`interaction_log.json`, `belief_state.json`) |
| `engine/kernel_bridge.py` | kernel signal bridge + session persistence |
| `engine/retriever.py` | counter-argument retrieval (vector/semantic) |
| `engine/vector_store.py` | ChromaDB (`all-MiniLM-L6-v2`) argument embeddings |
| `engine/analyzer.py` | contradiction detection |
| `engine/question_builder.py` | `build_structured_question` |
| `engine/topic_store.py` | **single writer/reader of topic data** (SQLite canonical via kernel) |
| `agent_core/tools/debate_ops.py` | composite `debate_step` tool bridging the agent loop and the engine |
| `llm_compiler.py` | topic compiler — **broken** (subprocess pipeline commented out; hardcoded absolute paths) |
| `mindmaps/local_user/` | beliefs, state, sessions (mindmap layer is largely a schema stub) |

## 3. Interaction (`/argu explore <topic>`, default topic `theism_atheism`)

```
/argu explore → ws_handler routes through the agent loop with a debate-moderator instruction
 → LLM calls debate_step(topic) — ONE tool call per iteration
 → prepare phase: pick next argument, create _pending[session_id] with threading.Event, return question (non-blocking)
 → engine yields {"type":"question"} → ws_handler relays to frontend → user answers
 → resolve_all_questions unblocks the Event → wait phase: map choice→stance+confidence, update beliefs, detect contradictions
 → returns {choice, stance, contradictions, next_argument, done}
 → LLM adds conversational framing and calls debate_step again until done:true → wraps up with a summary
```
Reuses `question_ops._pending` + `resolve_all_questions`/`cancel_questions` (no new question transport). **Zero LLM calls to generate questions** (pre-defined graph).

| Option | Meaning | Confidence |
|---|---|---|
| Agree | accept argument | 0.7 |
| Counter | disagree | 0.7 |
| Explore | unsure/curious | 0.5 |
| Custom | typed response | 0.6 |

**Argument selection:** prioritize arguments the user disagrees/is neutral on → untested → never repeat; fetch a semantic counter from the vector DB if available. **Belief model per argument:** `{stance: agree|disagree|neutral|custom, confidence 0–1, history[], last_updated}`. **Session persistence:** auto-save on topic completion; resume via `seen_arguments`.

## 4. Kernel integration

Every response emits `belief_shift`, `confidence_change`, `contradiction_detected` via `kernel_bridge` → `signal_engine` persists to episodic memory → `belief_signal_handler` stores in working memory, detects patterns, emits `pattern_detected` → retrievable via `kernel_retrieve(query="argument belief", limit=5)`. Contradiction = user *agrees* with two arguments linked by a contradicting edge.

## 5. Status

| Capability | Status |
|---|---|
| Argument navigation (`debate_step`) | ✅ |
| 3 options + custom | ✅ |
| Belief tracking (stance + confidence) | ✅ |
| Contradiction detection | ✅ (see DBT-02/03) |
| Kernel signal emission, session persistence, hypothesis engine | ✅ |
| Vector counter-arguments (ChromaDB) | ✅ (path issue DBT-05) |
| LLM topic compiler (`llm_compiler.py`) | ⬜ broken |
| Multi-user beliefs, mindmap layer | ⬜ stubs |

## 6. External paths & hazards (verify — docs conflict)

| Hazard | Detail | ID |
|---|---|---|
| Hardcoded absolute paths | `llm_compiler.py` → `/home/manigupt/Hello/python/ai_agent/utils/gemini_{question,answer}.md` and `/…/agent_tools` | DBT-04 |
| CWD-relative vector store | `engine/vector_store.py` persists to `./chroma_db` | DBT-05 |
| `sys.path` mutation | `kernel_bridge` inserts codebase root; `debate_ops` inserts `codebase/modules/` | DBT-06 |
| Cross-module imports | `kernel_bridge` imports `kernel.{signals.signal_engine, memory.working_memory, hypothesis.hypothesis_engine, events.event_engine}`; `retriever` imports `argu_god.engine.vector_store`; `debate_ops` imports `modules.argu_god.engine.*` and `agent_core.tools.question_ops._pending` | — |
| Data paths differ between docs | old debate README: `modules/argu_god/{topics,mindmaps}/…` · kernel manual: `data/topics/…`, `data/mindmaps/local_user/belief_state.json` | DBT-02 |

[LOOPHOLE DBT-01 · S1] The old debate README says to add topics by creating `graph.json`; the kernel manual says `graph.json` is a derived view overwritten on the next mutation. **Add topics with `scripts/topic_ops.py add-node` / `batch`, never by hand.** [/LOOPHOLE]
[LOOPHOLE DBT-02 · S2] If the debate loop and `topic_ops set-stance` read/write different `belief_state.json` files, edge-time contradiction detection silently never fires. [/LOOPHOLE]
[LOOPHOLE DBT-03 · S2] Analyzer expects edge relation `refutes`; kernel vocabulary is `{contradicts, requires, supports, supersedes}` (legacy relations only in backfilled data). Alias or migrate and test. [/LOOPHOLE]
[SUGGESTION DBT-04 · P2] Replace the broken compiler with "LLM proposes nodes/edges → `topic_ops batch` → contradiction gate". [/SUGGESTION]
[SUGGESTION DBT-05 · P1] Persist ChromaDB to an absolute, configured path. [/SUGGESTION]
[SUGGESTION DBT-06 · P3] Install the codebase as an editable package; remove `sys.path` edits. [/SUGGESTION]
[SUGGESTION DBT-07 · P3] Make confidence constants configurable/calibrated; prepare per-user belief stores for a future human twin. [/SUGGESTION]
[SUGGESTION DBT-08 · P2] Decide whether ArguGod's graph/gate backs the opportunity "challenge" round (`economy/challenge.py`). [/SUGGESTION]
[VERIFY DBT-02] Print the live paths of `belief_state.json`, `interaction_log.json` and the topic store. [/VERIFY]

## 7. Run

`conda run -n myenv python server.py` → frontend `/agent` page → send `/argu explore theism_atheism`.
