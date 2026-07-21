## Kernel development progress report 

## ArguGod Integration (Completed)

### Phase 1: Signal Emission from ArguGod

| Item | File + Function | Status |
|------|-----------------|--------|
| Bridge functions | `sub-agents/debate_agent.py` → `emit_belief_signal`, `emit_confidence_signal`, `emit_contradiction_signal` | ✅ Working |
| belief_shift signals | `sub-agents/debate_agent.py:emit_belief_signal()` → `signal_extractor.extract_and_emit(signal_type_hint="belief_shift")` | ✅ Working |
| confidence_change signals | `sub-agents/debate_agent.py:emit_confidence_signal()` → `signal_extractor.extract_and_emit(signal_type_hint="confidence_change")` | ✅ Working |
| contradiction_detected signals | `sub-agents/debate_agent.py:emit_contradiction_signal()` → `signal_extractor.extract_and_emit(signal_type_hint="contradiction_detected")` | ✅ Working |
| observation signals (topic start) | `kernel/extractors/signal_extractor.py:_extract_observation()` (registered line 210) | ✅ Working |

### Phase 2: Pattern Detection from Belief Signals

| Item | File + Function | Status |
|------|-----------------|--------|
| Signal handlers file | `kernel/signals/belief_signal_handler.py` | ✅ Created |
| belief_shift handler | `belief_signal_handler.py:handle_belief_shift_signal()` — stores in working memory with `BELIEF_SHIFT_TTL` | ✅ Working |
| contradiction handler | `belief_signal_handler.py:handle_contradiction_signal()` — stores in working memory + emits `pattern_detected` | ✅ Working |
| confidence_change handler | `belief_signal_handler.py:handle_confidence_change_signal()` — stores in working memory with `CONFIDENCE_CHANGE_TTL` | ✅ Working |
| pattern_detected emission | `belief_signal_handler.py:handle_contradiction_signal()` lines 79-98 → `signal_engine.create_signal(type="pattern_detected")` | ✅ Working |
| Working memory storage | `working_memory.add_memory()` called in all three handlers above | ✅ Working |

### Integration Flow

```
User responds in debate
    ↓
ArguGod updates belief state (modules/argu_god/engine/debate.py:debate_step)
    ↓
debate_agent (sub-agents/debate_agent.py) emits signals:
  - belief_shift       → signal_extractor.extract_and_emit(signal_type_hint="belief_shift")
  - confidence_change  → signal_extractor.extract_and_emit(signal_type_hint="confidence_change")
  - contradiction_detected → signal_extractor.extract_and_emit(signal_type_hint="contradiction_detected")
    ↓
signal_engine persists → episodic memory
    ↓
belief_signal_handler (kernel/signals/belief_signal_handler.py):
  - stores in working_memory.add_memory()
  - detects patterns → emit pattern_detected signal
    ↓
Kernel: patterns available for retrieval via pattern_engine
```

---

## Development paths

### Full Kernel Cognition

| Item | Description |
|------|-------------|
| Simulation → Pattern Pipeline | Trigger patterns from sim signals |
| Digital Twin + Simulation | Run scenarios from twin data |
| Policy Injection | Test policies via simulation |
| Recursive Hypothesis Testing | Generate sims from hypotheses |

### Kernel Hot-Reload

| Item | Description |
|------|-------------|
| `kernel_reload` tool | Reloads sim_ops, kernel_ops, code_rag, and tools/__init__.py from disk without restart |
| Auto-reload (MCP) | MCP server detects `st_mtime_ns` changes and re-imports modules on next tool call |
| Use case | Edit simulation/kernel code → next `pie_*` call picks up changes — no server restart |

### Enhanced Debate Features

| Item | Description |
|------|-------------|
| Multi-Person Debate | Multiple users/perspectives |
| Debate Analytics | Show session stats (arguments seen, time, belief changes) |
| Multiple Perspectives | Store beliefs per user/persona |
| Side Tracking | Track which side user favors |
| Argument Quality | Score arguments by evidence strength |
| Debate Summary | Generate summary report |
| Progress Indicator | "5/23 arguments explored" |
| Export Belief Graph | Export as JSON |
| Argument Quality Scoring | Score by evidence |
| Topic Browser | List and select from available topics |
| Cross-Topic Linking | Connect beliefs across topics |
| Recursive Counterarguments | Explore counter-counterarguments |
| Evidence Search | Auto-find supporting evidence |
| belief_graph Visualization | Render belief network |

### Self-Evolution

| Item | Description |
|------|-------------|
| Auto-Pattern Discovery | Discover new patterns |
| Hypothesis Auto-Generation | Auto-generate from signals |
| Auto-Topic Generation | Generate new topics from knowledge |
| Self-Contradiction Detection | Check consistency |
| Knowledge Compression | Auto-summarization |
| System Self-Check | Detect internal contradictions |

---

## Files Added/Modified

| File | Change |
|------|--------|
| `agent_core/tools/kernel_ops.py` | Added `kernel_reload()` — hot-reload tool modules without restart |
| `agent_core/tools/__init__.py` | `_register_all()` imports fresh inside function body for reload support; code_rag tools moved to `CAT_CODE_RAG`; `kernel_reload` registered |
| `agent_core/tools/schemas.py` | Added `kernel_reload` and `timeout` param schemas |
| `agent_core/tools/mcp_server.py` | Added hot-reload (`_reload_if_changed`/`_do_reload`); exposes `CAT_CODE_RAG` tools |
| `modules/argu_god/engine/kernel_bridge.py` | **Deleted** — relocated to `sub-agents/debate_agent.py` |
| `modules/argu_god/engine/analyzer.py` | **Deleted** — dead code, no callers |
| `sub-agents/debate_agent.py` | Created — bridge functions from former `kernel_bridge.py` |
| `kernel/config/kernel_config.py` | Created — centralized config constants |
| `kernel/signals/belief_signal_handler.py` | Modified — imports config constants instead of hardcoding |
| `kernel/hypothesis/hypothesis_engine.py` | Modified — imports config constants instead of hardcoding |
| `kernel/retrieval/semantic_retriever.py` | Modified — graceful `sentence_transformers` import check in `ChromaBackend` |
| `modules/argu_god/engine/debate.py` | Modified — imports from `debate_agent`; indexing consolidated into `_populate_semantic_memory` |
| `kernel/memory/memory_engine.py` | Refactored — SQLite sole backend; removed JSON write path, `write_json`/`read_json` imports, `use_sqlite` param, `memory_roots` dict |
| `kernel/persistence/db.py` | Added `generic_memory` table + CRUD methods (save/load/list/delete/exists) |
| `kernel/utils/paths.py` | Removed `MEMORY_DIR`, `WORKING_MEMORY_DIR`, `EPISODIC_MEMORY_DIR`, `SEMANTIC_MEMORY_DIR`, `PATTERN_MEMORY_DIR`, `HYPOTHESIS_MEMORY_DIR`, `get_memory_path()` |

---
## Implementation Status (2026-07-21)

### ✅ Completed

| Step | Description | Key Changes |
|------|-------------|-------------|
| 1 | `storage/` vs `kernel/memory/` resolved | `memory_engine.py` now delegates JSON I/O to `storage/unit_storage.py`'s shared `write_json`/`read_json` functions. One canonical JSON writer. |
| 2 | SQLite persistence layer | Created `kernel/persistence/db.py` with full schema (logs, semantic_nodes, semantic_edges, patterns, hypotheses, working_memory). Replaced `RotatingFileHandler` in `kernel/utils/logger.py` with `SqliteLogHandler`. `memory_engine.save_object()` optionally persists to SQLite. |
| 3 | `contradiction_detector.py` | Built `kernel/patterns/contradiction_detector.py` — generalized from argu_god's `analyzer.py`, uses `semantic_memory` edges with `relation_type == "contradicts"` instead of debate `graph.json` refutes. Two APIs: `detect_contradictions(believed_node_ids)` and `detect_contradictions_for_beliefs(beliefs_dict)`. |
| 4 | `signal_extractor.py` | Built at canonical `kernel/extractors/signal_extractor.py` (only copy — no duplicate in `kernel/signals/`). Registered extractors for `belief_shift`, `confidence_change`, `contradiction_detected`, `observation`. Implements `extract()` and `extract_and_emit()`. |
| 5 | Add embedding path to `semantic_retriever.py` | ✅ Done. Added `EmbeddingBackend` protocol + `ChromaBackend` class. `set_embedding_backend()` / `search_by_embedding()` on `SemanticRetriever`. Falls back to keyword if no backend set. No new parallel file — embedding is a backend option within the existing retriever. |
| 6 | Rewire argu_god | ✅ Done. `sub-agents/debate_agent.py` (former `kernel_bridge.py`) delegates to `signal_extractor.extract_and_emit()`. `debate.py` populates `semantic_memory` from graph.json via `_populate_semantic_memory()`, then calls kernel's `detect_contradictions_for_beliefs()`. |
| 7 | Tier 4 hygiene | Extracted `HypothesisSchema` into `kernel/schemas/hypothesis_schema.py`; `hypothesis_engine.py` now imports it (consistent with pattern_schema/signal_schema/event_schema). Added `requires`, `required_by`, `depends_on` relation types to `kernel/ontology/relation_types.py`. |
| 8 | Leave Tier 5 empty | No second consumer exists yet — no change needed. |
| 9 | SQLite made sole persistence backend | `memory_engine.py` — JSON file writes removed, `write_json`/`read_json` imports removed, `use_sqlite` parameter removed. `db.py` — added `generic_memory` table for episodic signals/events + future types. `paths.py` — memory directory constants and `get_memory_path()` removed. |

### Notes

- `relation_schema.py` already has the full `RelationSchema` model covering `supports`/`contradicts` — only `requires`/`depends_on` types were missing (now added).
- SQLite is now the sole persistence backend. `memory_engine.save_object()` writes to both `generic_memory` (full JSON blob for round-trip fidelity) and structured tables (for querying). No JSON files are written.

---

## Kernel Improvements (Completed — 2026-07-21)

All 5 items from the previous session's pending list have been implemented:

### 1. `analyzer.py` — removed
File `modules/argu_god/engine/analyzer.py` deleted (28 LOC, no remaining callers).

### 2. `vector_store.index_graph()` consolidated into `_populate_semantic_memory()`
`_populate_semantic_memory()` in `debate.py` now calls `vector_store.index_graph(graph)` internally after creating semantic nodes. Removed the separate `_index_graph` import and try/except block from `debate_step()`.

### 3. `sentence_transformers` import — graceful fallback
`ChromaBackend._get_model()` in `kernel/retrieval/semantic_retriever.py` now wraps the import in `try/except ImportError` with a clear log message: `"sentence_transformers not installed — embedding search disabled. Install with: pip install sentence-transformers"`.

### 4. Magic numbers centralized
Created `kernel/config/kernel_config.py` with all extracted constants:
- `BELIEF_SHIFT_TTL`, `CONTRADICTION_TTL`, `CONFIDENCE_CHANGE_TTL`
- `PATTERN_IMPORTANCE`, `PATTERN_CONFIDENCE`
- `HYPOTHESIS_CONFIDENCE_BUMP`, `HYPOTHESIS_CONFIDENCE_PENALTY`

`belief_signal_handler.py` and `hypothesis_engine.py` import from this module instead of hardcoding.

### 5. `kernel_bridge.py` relocated to `sub-agents/debate_agent.py`
The 3 bridge functions (`emit_belief_signal`, `emit_confidence_signal`, `emit_contradiction_signal`) moved to `sub-agents/debate_agent.py`. `debate.py` imports from the new location (adds `sub-agents` dir to `sys.path`). Old `kernel_bridge.py` deleted.

### 6. MCP Code RAG tools — `pie_file_api`, `pie_call_chain`, `pie_compare_apis`, `pie_symbols_by_file`
All 4 added to `code_rag.py` (`CodeRAG` class methods + tool functions), registered in `schemas.py` + `__init__.py` under `CAT_CODE_RAG`. Path resolution via `_resolve_path()` prepending `CODEBASE_ROOT`.

### 7. SQLite made sole persistence backend
`memory_engine.py` refactored to use SQLite as the only storage backend:
- `save_object()` unconditionally persists to `generic_memory` table (full JSON blob) plus structured tables (semantic_nodes, patterns, etc. for querying)
- `load_object()` reads from `generic_memory`, preserving full dict round-trip
- `list_objects()`, `delete_object()`, `object_exists()`, `search_by_prefix()` all query SQLite
- Removed `write_json`/`read_json` imports from `storage.unit_storage`
- Removed `use_sqlite` parameter, `memory_roots` dict, and all file path methods
- Added `generic_memory` table to `kernel/persistence/db.py` with `save_generic_memory`, `load_generic_memory`, `list_generic_memory_ids`, `delete_generic_memory`, `generic_memory_exists`
- Cleaned up `kernel/utils/paths.py` — removed `MEMORY_DIR`, all 5 memory subdirectory constants, `get_memory_path()`

