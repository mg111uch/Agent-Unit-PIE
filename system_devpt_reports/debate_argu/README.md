# ArguGod Debate Engine (Level 1)

> Code: `$PIE_ROOT/codebase/modules/argu_god/` + bridge `$PIE_ROOT/codebase/agent_core/tools/debate_ops.py` · Topic data is owned by `engine/topic_store.py` (SQLite canonical, exported by the kernel — see `kernel/README.md`).
> **Level-2 files (same dir, still live):** `roadmap.md` (unimplemented only), `status.md` (next task + recent changes).
> This doc **corrects** three contradictions found between the old debate README and the kernel manual (DBT-01/02/03); items marked ❓ still need a coding-agent answer. Facts below were re-checked against code on 2026-10-25 — the old README's file list (Jul 17) was stale.

## 1. Role

ArguGod is the **epistemic validation engine** and human-belief tracker: contradiction detection, counter-argument generation, hypothesis testing, evidence comparison, uncertainty analysis, belief tracking, perspective exploration, simulation of alternative viewpoints. System evolution: `Static knowledge → Interactive debate → Belief tracking → Adaptive intelligence → Recursive epistemic intelligence`.

**Constraints:** **3 predefined options per question + always a custom-text option added by the frontend** (= 4 total); break complex reasoning into steps; **never overwrite user history**; keep **LLM knowledge separate from human beliefs**. Currently single-user (`local_user`).

## 2. Code map

| Path | Purpose |
|---|---|
| `modules/argu_god/engine/loop.py` | argument graph loading + next-argument selection (`load_graph`, `get_next_argument`) |
| `modules/argu_god/engine/debate.py` | the loop itself — `debate_step` (prepare/wait phases), `debate_expand`, `export_topic`, `import_topic`, `_populate_semantic_memory` |
| `modules/argu_god/engine/debate_helpers.py` | extracted knowledge-check / novelty-check / write-back helpers |
| `modules/argu_god/engine/storage.py` | state + belief persistence (`interaction_log.json`, `belief_state.json`) |
| `modules/argu_god/engine/topic_store.py` | **single writer/reader of topic data** (SQLite canonical; `export_graph` writes the derived `graph.json` view) |
| `modules/argu_god/engine/expand.py` | `expand_topic` — add nodes/edges through `topic_store` (strict duplicate-error contract) |
| `modules/argu_god/engine/dedup.py` | duplicate detection for proposed nodes |
| `modules/argu_god/engine/retriever.py` | counter-argument retrieval (vector/semantic) |
| `modules/argu_god/engine/vector_store.py` | ChromaDB (`all-MiniLM-L6-v2`) argument embeddings |
| `modules/argu_god/engine/question_builder.py` | `build_structured_question` |
| `modules/argu_god/llm_compiler.py` | topic compiler — **working again**: `compile_topic_llm`, `generate_llm_question` via `agent_core.providers_setup.build_orchestrator` (the hardcoded absolute paths are gone — DBT-04 resolved) |
| `agent_core/tools/debate_ops.py` | thin bridge exposing `debate_step` as a tool |
| `agent_core/tools/expand_ops.py` | thin bridge exposing `expand_topic` as a tool (graph expansion, not a CLI) |
| `sub-agents/debate_agent.py` | `emit_belief_signal` / `emit_confidence_signal` / `emit_contradiction_signal` — the kernel bridge, relocated here (the old `engine/kernel_bridge.py` was deleted) |
| — | `engine/analyzer.py` was **deleted** (dead code); contradiction detection now runs through the kernel's generalized detector (`kernel/patterns/contradiction_detector.py`, `detect_contradictions_for_beliefs`) plus the edge check inside `debate_step` |
| `prompt_fragments/debate_playbook.md` | the `CAT_DEBATE` playbook injected with the debate tools |
| `data/topics/<topic>/` | canonical topic store (`theism_atheism`, `popu_sim`, `sim_stock`, `project_history`, `controlworks_*`) |
| `data/mindmaps/local_user/` | beliefs, state, sessions (`belief_state.json`, `interaction_log.json`, `sessions/`); mindmap layer is largely a schema stub |

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

Two-phase execution is transparent to the LLM: `prepare_only=True` picks the argument and returns the question; `complete_only=True` (or a plain call) blocks on the Event and processes the answer. Reuses `question_ops._pending` + `resolve_all_questions`/`cancel_questions` (no new question transport). Works from one topic store: `debate_step` errors with `Topic not found` when the topic has no graph.

| Option | Meaning | Confidence |
|---|---|---|
| Agree | accept argument | 0.7 |
| Counter | disagree | 0.7 |
| Explore | unsure/curious | 0.5 |
| Custom | typed response (frontend-added) | 0.6 |

**Zero LLM calls to generate questions** while the graph lasts; when it is exhausted the caller may pass `llm_generated` (LLM-proposed next argument + evidence) and the compiler's `generate_llm_question` can produce one. Free-text answers are accepted and go through knowledge check → novelty check → write-back with provenance.

**Argument selection:** prioritize arguments the user disagrees/is neutral on → untested → never repeat; fetch a semantic counter from the vector DB if available. **Belief model per argument:** `{stance: agree|disagree|neutral|custom, confidence 0–1, history[], last_updated}`. **Session persistence:** auto-save on topic completion to `data/mindmaps/local_user/sessions/`; resume via `seen_arguments` in state.

**Contradiction detection:** agreement with two arguments linked by a contradicting edge, e.g.
```
⚠️ Potential contradiction detected:
- You agreed with both: Argument A AND Argument B
```
The legacy `refutes` relation is aliased to the kernel vocabulary `{contradicts, requires, supports, supersedes}` on write and on load (DBT-03 fixed in code; a dedicated test is still missing).

## 4. Kernel integration

Every response emits `belief_shift`, `confidence_change`, `contradiction_detected` via `sub-agents/debate_agent.py` → `signal_engine` persists to episodic memory → `belief_signal_handler` stores in working memory, detects patterns, emits `pattern_detected` → retrievable with `kernel_retrieve(query="argument belief", limit=5)`. Working memory after a session holds belief shifts per argument, confidence changes, contradictions, session metadata.

## 5. Status

| Capability | Status |
|---|---|
| Argument navigation (`debate_step`) | ✅ |
| 3 predefined options + frontend custom | ✅ |
| Belief tracking (stance + confidence) | ✅ |
| Contradiction detection | ✅ (`refutes` aliased to `contradicts`) |
| Kernel signal emission, session persistence, hypothesis engine | ✅ (bridge now `sub-agents/debate_agent.py`) |
| Vector counter-arguments (ChromaDB) | ✅ (path issue DBT-05 open) |
| Topic expansion (`expand_topic` + `expand_ops`) | ✅ |
| LLM topic compiler (`llm_compiler.py`) | ✅ rewritten; hardcoded paths removed |
| Multi-user beliefs, mindmap layer | ⬜ stubs |

## 6. External paths & hazards (verify — docs conflict)

| Hazard | Detail | ID |
|---|---|---|
| Topic editing | **Never hand-edit `graph.json`** — it is a derived view rewritten by `write_export`. Add topics with `scripts/topic_ops.py add-node` / `batch`, or `expand_topic` | DBT-01 |
| Data-path drift between docs | live paths are `data/topics/…` and `data/mindmaps/local_user/…`; the old README's `modules/argu_god/{topics,mindmaps}` no longer exist | DBT-02 |
| Relation vocabulary | kernel vocabulary `{contradicts, requires, supports, supersedes}`; `refutes` is aliased on write/load, legacy relations survive only in backfilled data | DBT-03 |
| CWD-relative vector store | `engine/vector_store.py` persists to `./chroma_db` — different launch dirs create different indexes | DBT-05 |
| `sys.path` mutation | `debate_ops` / `expand_ops` insert `codebase/modules/`; `sub-agents/debate_agent.py` adds the codebase root for `kernel.*` imports | DBT-06 |
| Cross-module imports | `sub-agents/debate_agent.py` imports `kernel.{signals.signal_engine, memory.working_memory, hypothesis.hypothesis_engine, events.event_engine}`; `retriever` imports `argu_god.engine.vector_store`; bridges import `modules.argu_god.engine.*` and `agent_core.tools.question_ops._pending` | — |

[LOOPHOLE DBT-01 · S1] ~~Old README says create `graph.json` by hand~~ — **resolved**: `topic_store` is the single writer, `graph.json` is a derived view. Documented above. [/LOOPHOLE]
[LOOPHOLE DBT-02 · S2] If `debate_step`/`export_topic` and `topic_ops set-stance` ever read different stores, edge-time contradiction detection silently never fires. Live paths now agree; keep them asserted. [/LOOPHOLE]
[SUGGESTION DBT-03res · P1] Add a regression test pinning `refutes → contradicts` aliasing (implemented, untested). [/SUGGESTION]
[SUGGESTION DBT-05 · P1] Persist ChromaDB to an absolute, configured path. [/SUGGESTION]
[SUGGESTION DBT-06 · P3] Install the codebase as an editable package; remove `sys.path` edits. [/SUGGESTION]
[SUGGESTION DBT-07 · P3] Make confidence constants configurable/calibrated; prepare per-user belief stores for a future human twin. [/SUGGESTION]
[SUGGESTION DBT-08 · P2] Decide whether ArguGod's graph/gate backs the opportunity "challenge" round (`economy/challenge.py`). [/SUGGESTION]
[VERIFY DBT-02] Print the live paths of `belief_state.json`, `interaction_log.json` and the topic store. [/VERIFY]

## 7. Run

```bash
conda run -n myenv python server.py
# Frontend: /agent page → send "/argu explore theism_atheism"
```

## 8. Roadmap hand-off (detail lives in `roadmap.md` / `status.md`)

`roadmap.md` remains the single plan of record for this module; the table below is the direction-session summary. Shipped items were moved out of it rather than copied forward.

| Item | Status | Note |
|---|---|---|
| Topic expansion tool | ✅ shipped | `expand_topic` + `expand_ops` (the old `/argu add-topic` CLI is not what got built) |
| LLM-generated question batching when `graph.json` is exhausted | 🟡 partial | `generate_llm_question` + `llm_generated` param exist; batching/quality unproven |
| Circular dependency fix: `question_ops._pending` | ⬜ open | blocks a `debate_step` integration test (`status.md` blocker) |
| Multi-person debate with user/perspective tracking | ⬜ later | plus debate analytics (session stats, belief changes), argument quality scoring by evidence strength |
| Export belief graph as JSON | 🟡 partial | `export_topic` exports the topic graph; belief-graph export still open |
| Recursive counterarguments (counter-counterarguments) | ⛔ rejected | complexity too high for current scope |

**Doc reconciliation:** `status.md` (2026-08-16) is newer than both READMEs and is the source of the file-relocation/compiler facts kept above; its "Known Gaps" still list `/argu add-topic` and the broken `llm_compiler` — both stale (DOC-03).
