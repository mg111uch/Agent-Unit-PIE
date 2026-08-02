# Agent Orchestrator Reference

## Architecture

```
server.py
    │
    ▼
agent_core/
  ├── loop               ──► engine/executor/stepper + multi-tool calls + failure breaker
  │                      ──► builds explicit message arrays from msg_store (when available)
  ├── message_store      ──► SQLite session/message persistence + compaction
  ├── workspace          ──► single path resolver (used by all file tools + server APIs)
  ├── providers_setup    ──► agent_core.llm.*
  ├── planning/          ──► local_planner.py (LocalPlanner — routing + local model orchestration)
  ├── context, prompts, commands, auto_research
  ├── tools/             ──► registry.py + file_ops, meta_ops, kernel_ops, sim_ops, ast_ops, code_rag, ...
  ├── llm_orchestrator ──► timeouts/retries
  └── providers/
       ├── gemini_provider.py
       ├── openrouter_provider.py
       ├── ollama_provider.py
       └── mock_provider.py
```

## Features Overview

| Capability | Description |
|------------|-------------|
| Pluggable Tools | File Ops, Meta, Code RAG, Kernel, Debate, Simulation, Git, Observer, Chain (composite multi-tool calls) |
| Auto-Research | Goal-autonomous research using shared agent loop (`/auto`) |
| Debate Mode | Structured topic exploration with belief tracking (`/argu`) |
| Provider Switching | Swap LLM provider/model at runtime via API (`/api/switch-provider`); `GET /api/providers` lists available providers |
| Local Model Routing | Route simple file/meta tool calls to a local model via Ollama; fall back to cloud for complex reasoning — configurable via `local_model` in config.json |
| Tool Pack Filtering | Enable/disable tool categories via `AGENT_TOOL_PACKS` env or `tool_packs` in config.json; default `file` only |
| Tool Mode | Restrict active tools by preset via `tool_mode`: `all` (no filtering), `read_only`, `shell_only` — enforced on schemas and execution |
| MCP Integration | Exposes tools over MCP: CAT_META always, CAT_FILE never, other tool packs only when enabled in config |
| Code RAG | SQLite-based symbol search + call graph from codebase atlas output |
| Hot-Reload | Auto-detect tool module file changes and reload without restart; explicit `kernel_reload` and `hot_reload` tools |
| Tool Call Stats | Per-tool call count, avg duration, error rate, token estimate — tracked in `kernel.db` |
| File Access Stats | Per-file read/write/edit count — tracks churn and most-accessed files |
| User Reading Budget | Daily budget for LLM output lines shown to user; auto-alerts when &lt;20% remaining |
| Hot-Reload MCP Tool | `hot_reload` re-registers tools + sends `notifications/tools/list_changed` to client — no restart needed |
| Tool Failure Logging | Failed tool calls auto-saved to `generic_memory` with error, args, and timestamp |
| Timeouts & Retries | Retries failed LLM calls up to 3x with exponential backoff; 60s per-call timeout |
| Multi-Tool Parallel Turns | Executes all tool calls from one model response in a single follow-up, reducing round trips |
| Message Store & Compaction | SQLite session/message persistence (WAL, thread-safe); sessions past 100 messages trimmed to last 50; survives restarts |
| Checkpoints / Undo | Auto-saves a checkpoint before edit/write; `undo_last_edit` restores latest; `checkpoint_info` lists; max via config |
| Path Resolution | Single workspace path resolver; blocks `..` traversal and symlink escapes |
| Auth & CORS | JWT auth on WebSocket + REST (except `/api/status`); CORS restricted via env |
| Per-User Workspace | Isolated workspace per authenticated user |
| Sandbox Shell | Optional Docker sandboxing for `execute_command` (read-only, no network) |
| Secrets Redaction | Redacts API keys/tokens from tool results and stored messages |
| Rate Limiting | Per-user token bucket: `llm_calls_per_minute` (10), `tool_writes_per_minute` (30) |
| Audit Log | Every tool invocation logged to SQLite; queryable via `/api/audit` |
| System Prompt | Capability-aware prompt assembled from `prompt_fragments/` based on active tool packs |
| Native Function Calling | JSON Schema function calling for all providers; text-JSON/XML fallback |
| Streaming | Real-time token streaming with stop/cancel support |

> Verified capability inventory with code citations: `status.md`.

## Tools

All tools support **native function calling** (JSON Schema derived from function signatures via `tools/registry.py`) with text-JSON fallback. Tools return structured `ToolResult` objects internally (ok/error_type/message/suggestion) serialized to strings for the model.

### Approximate size of the tool schemas sent each turn

Measured programmatically (JSON-serialized with 2-space indent):

| Format | Estimated tokens |
|---|---|
| **OpenAI-style** (all 59 tools) | **~10,828** |
| **Gemini-style** (all 59 tools) | **~10,838** |

**Per-tool breakdown (range):** Smallest = `get_workspace_info` (~100 chars), Largest = `expand_topic` (1,720 chars). Most tools are 300–900 chars.

**Per-category breakdown (OpenAI format):**

| Category | Tools | Chars | Est. tokens |
|---|---|---|---|
| `code_rag` (20 tools) | 20 | 15,132 | ~3,783 |
| `file` (9 tools) | 9 | 7,745 | ~1,936 |
| `meta` (10 tools) | 10 | 5,653 | ~1,413 |
| `kernel` (6 tools) | 6 | 5,664 | ~1,416 |
| `debate` (2 tools) | 2 | 3,263 | ~815 |
| `sim` (4 tools) | 4 | 2,127 | ~531 |
| `git` (4 tools) | 4 | 1,998 | ~499 |
| `observer` (4 tools) | 4 | 1,747 | ~436 |

### File Operations
| Tool | Purpose |
|------|---------|
| `read_file` | Read file (returns line-numbered output; lists nearby files on error) ; **batch_read mode** via `paths=[...]` — reads multiple files in one call, each with optional own `offset`/`limit`/`line_numbers`; **auto-cache hook** — if file unchanged since last read, return `(cached: 544 lines)` instead of full content|
| `list_files` | List directory (recursive, depth-capped, skips noise dirs) |
| `write_to_file` | Write file (create/overwrite/append modes — no patch mode) |
| `edit_file` | Targeted replacement (unique old_string → new_string; rejects 0/>1 matches; shows diff) ; **batch_edit mode** via `edits=[...]` - apply sequentially with per-file checkpoint + cache invalidation; `replace_all` for bulk renames|
| `execute_command` | Run shell (configurable allowlist via config.json) |
| `glob_search` | Find files by glob pattern (`**/*.py`, `src/**/*.ts`) |
| `grep_search` | Search file contents by regex (uses ripgrep if available) |
| `todo` | Manage task plan (actions: read, create, update, mark_done, clear) |
| `ask_user_question` | Ask the user for input/clarification with up to 3 options per question (a custom text option is always added). Multiple questions can be asked at once — the user sees them one by one with a progress bar. Tool blocks until all answers are submitted. |
| `subagent_task` | Spawns a full agent loop with its own context, Returns the sub-agent's final answer — gated by `subagent_task_enabled` config flag (default false) |

### Meta Tools
| Tool | Purpose |
|------|---------|
| `check_path_exists` | Path to check, relative to workspace root |
| `get_workspace_info` | Ground-truth: root path + top-level entries |
| `file_diff` | Verify edits by seeing 5 changed lines instead of re-reading the full file; tracks all changes regardless of git |
| `read_section` | Read file content around a regex pattern match |
| `undo_last_edit` | Restore the most recent checkpoint for a file; file_diff — shows what changed without reverting. |
| `checkpoint_info` | List available checkpoints |
| `file_skeleton` | AST structure map: eager/lazy imports, globals, classes (with method counts), functions with full signatures + line ranges + docstring hints. Non-Python files get a lightweight regex skeleton. Always fresh (on-disk), no atlas. |
| `who_imports` | module-level import graph: what the file imports (eager/lazy) + which workspace files import it, with relative-import resolution (from .engine import X → agent_core.loop.engine). Uses an mtime-keyed parse cache. |
| `cross_file_edit` | Surgerical edits across files in one call, per-edit status.  |
| `check_before_edit` |  read-only dry-run: validates each {path, old_string} target matches exactly once before applying. |
| `tool_anatomy` | Registry introspection: tool_anatomy(name) traces a tool's category, registration/implementation locations, MCP exposure, schema, and all cross-file references; tool_anatomy() lists the full tool surface grouped by category with a stale-reference scan (docs/mocks referencing unregistered names)  |

### Code RAG Tools (from codebase atlas, separate `code_rag` category)
| Tool | Purpose |
|------|---------|
| `get_symbol` | Look up a function/class by name with full source code, signature, and docstring |
| `get_symbols_meta` | Batch metadata lookup (name, signature, token_count, risk_level, lines) without full source — browse cheaply then call `get_symbol` for the ones worth fetching |
| `search_symbols` | FTS5 full-text search across symbol names, docstrings, and code |
| `get_callers_callees` | Recursive graph traversal — who calls this symbol and what it calls |
| `find_impact` | List everything that depends on a symbol (all transitive callers) |
| `get_index_info` | Real-time atlas stats (symbols, edges, token ranges, risk distribution) — call once at session start to calibrate budget |
| `file_api` | Public API surface of one or more files (pass `paths=[...]` to batch — any files, not just kernel): classes → method signatures (with docstring first line), module-level functions, no bodies. Hierarchical, class-organized. |
| `call_chain` | Shortest call chain from a function to any symbol in another module via BFS over `call_edges` |
| `compare_apis` | API-level diff between two files (only_in_a, only_in_b, signature_mismatches) |
| `symbols_by_file` | Complete flat symbol inventory of a file by path alone — no query needed |
| `atlas_status` | Check if atlas is indexed, ingestion timestamp, file/symbol/call-edge counts |
| `project_root` | Return absolute project root and codebase root paths |
| `report_freshness` | Scan all `system_devpt_reports/*.md` for stale `_Last verified` stamps and broken citations |
| `extract_symbols_to_file` | Fetch bodies of named symbols from atlas, write to destination with headers |
| `minimal_context_dump` | Chains blast radius → symbol source → peripheral API sigs into one capped file |

### Chain Tools (composite `chain` category)
| Tool | Purpose |
|------|---------|
| `probe_module` | file_skeleton → who_imports → find_impact (optional) — one-call module orientation |
| `orient_symbols` | get_index_info → file_api → get_symbols_meta → get_symbol — cheap-to-full symbol fetch |
| `doc_audit` | report_freshness → report_schema_check → report_inventory — doc health in one call |
| `safe_edit` | check_before_edit → edit_file → file_diff — validate, apply, and verify a single-file edit batch |

Runs each step through the `ChainEngine` (`agent_core/tools/chain/chain_engine.py`), binding `$input.X`/`$step.<key>` refs, with per-step budget caps. Gated by `tool_packs.chain` in config.json (default off).

#### Self-evolving workflow graph (mining + evolution)
`agent_core/tools/chain/chain_miner.py` observes tool-call sequences (in-loop via `_feed_chain_miner` in `loop/_helpers.py`, and session-end via `ChainMiner.mine_session`) and mines repeated contiguous sub-sequences into new `ChainSpec`s. Persisted in SQLite (`agent_core/tools/chain/chain_store.py`, tables `chain_specs` + `chain_candidates` in the kernel DB) and approved mined chains are reloaded as live tools on startup (`_register_stored_chains`).

- Read-only chains auto-promote to `approved` (live) immediately.
- Chains with any write step persist as `pending` — promoted live only via `chain_admin approve <name>`.
- Gated by the `workflow_learn` block in config.json: `enabled`, `min_occurrences` (2), `max_sequence_len` (4), `in_loop`, `session_end`, `graph_evolve`, `context_hints`, `stale_after_days` (14), `min_savings_tokens` (0).
- `chain_admin` tool (category `chain`): `list`, `candidates`, `approve name=...`, `activate name=...`, `delete name=...`.
- `workflow_status` tool (observer): `summary` (default), `full` (graph nodes/edges/clusters/notes), `candidates`, `evolve` (rebuild graph from chains + candidates + session telemetry).
- Repeated tools inside a mined chain get unique step names (`tool_2`); periodic repeats (`[a,b,a,b]`) collapse to their base (`[a,b]`).
- **Feedback loop:** `workflow_hints()` injects live chains (only when `tool_packs.chain` is on) + top DO/AVOID notes into the turn context at every step, gated by `workflow_learn.context_hints`. Chains are never hinted when not exposed, so the agent is never told to call a tool it can't see.
- **Lifecycle:** approved mined chains unused for > `stale_after_days` are auto-demoted to `inactive` (unregistered) at session-end; `chain_admin activate` restores them. Handwritten chains are never touched.
- **Savings scoring:** candidates carry `savings_est` (≈ tokens saved per chain, from `tool_stats` avg output tokens). `min_savings_tokens` gates auto-promotion: read-only chains below the bar stay `pending`.

**Workflow graph (Part 3 / P4):** `agent_core/tools/chain/graph_evolver.py` (`GraphEvolver`) maintains the evolving graph in SQLite — tables `graph_nodes`, `graph_edges`, `graph_clusters`, `graph_notes`, `graph_state`, `tool_sequences`. Each chain becomes a cluster node (dagre compound) with its steps as an ordered edge chain; mining candidates become dashed diamond shortcut edges; observed session usage (`tool_sequences`) becomes DO/AVOID notes and per-tool stats. `scripts/render_graph.py` serves a dagre-d3 HTML view of the SQLite graph over HTTP (default port 8123, auto-opens the browser; `--output FILE` writes a static file instead) with cluster subgraphs + a toggleable notes panel; the served page re-renders from SQLite on every refresh. Graph evolution runs from the session-end hook in `loop/engine.py` (gated by `workflow_learn.graph_evolve`).

### Kernel Tools
| Tool | Purpose |
|------|---------|
| `kernel_retrieve` | Query memory |
| `kernel_emit_signal` | Emit observation |
| `kernel_store_context` | Store in memory |
| `kernel_get_memory` | Retrieve memory |
| `kernel_create_event` | Create event |
| `kernel_reload` | Reload tool modules from disk without restart |

### Debate Tools
| Tool | Purpose |
|------|---------|
| `debate_step` | Present next debate argument for a topic and get user response. |
| `expand_topic` | Add new nodes and edges to a topic's argument graph. Validates no duplicate names, persists to graph.json, and re-indexes the vector store. |

### Simulation Tools
| Tool | Purpose |
|------|---------|
| `simulation_run` | Run simulation (opt. `timeout` param in secs) |
| `simulation_compare` | Compare runs |
| `simulation_list` | List runs |
| `simulation_get_signals` | Get signals |

### Git Tools (behind `git_tools_enabled` config flag)
| Tool | Purpose |
|------|---------|
| `git_status` | Show current git status |
| `git_diff` | Show git diff (optional path/staged filter) |
| `git_commit` | Commit staged changes with a message |
| `git_log` | Show recent commit history |

### Observer Tools (telemetry & observability)
| Tool | Purpose |
|------|---------|
| `tool_stats` | Per-tool call count, avg duration, error rate, avg tokens — flags high-error tools |
| `file_stats` | Most accessed files by read/write/edit, grouped by file — flags high-churn candidates |
| `user_reading_budget` | Track daily LLM output lines read by user. Call with `record_lines=N` to log; warns when &lt;20% budget remains |
| `hot_reload` | Built-in (handled by `mcp_server.py`). Re-registers all tools + sends `notifications/tools/list_changed` to MCP client |

----------

# Final Plan: Tool Chains + Self-Evolving Workflow Graph

**Decisions locked in:**
- **Auto-promotion:** read-only chains auto-register; write/edit chains require approval.
- **Persistence:** everything in SQLite (graph + telemetry + patterns + chains).
- **Mining trigger:** both session-end batch AND in-loop lightweight check, each behind config flags (both can be disabled).
- **Phase 1 chains:** `probe_module`, `orient_symbols`, `doc_audit`, `safe_edit`.

---

## Part 1 — Tool Chains (deterministic composite tools)

New package `agent_core/tools/chain/`:
- **`chain_spec.py`** — `ChainSpec` + `Step` dataclasses (declarative: name, category, description, params spec, `steps[]`, budget). Each step: `{tool, args, collect}` where `args` bind `$input.X` / `$step.<prev>.<field>` / literals, and `collect` slices step output into named intermediates + the final JSON.
- **`chain_engine.py`** — `ChainEngine`: resolves each step's tool via `registry.get_tools` (same wrapped fns the loop uses), normalizes args, calls, normalizes results (both `ToolResult` and raw-string incl. `"Error"` prefix, mirroring `executor.py:97`), binds outputs, accumulates under a token budget (reuse `context_dump.py:13` `_add_section` idea), short-circuits on error. Returns one JSON dict.
- **`chains.py`** — data-only list:

| Chain | Cat | Steps | Kills pattern |
|---|---|---|---|
| `probe_module` | meta | `file_skeleton` → `who_imports` → `find_impact` | "read file to understand structure" (sessions 2/3/5) |
| `orient_symbols` | code_rag | `get_index_info` → `file_api(paths)` → `get_symbols_meta` → `get_symbol` | CALIBRATE→ORIENT→META→FETCH, hardcoded |
| `doc_audit` | meta | `report_freshness` → `report_schema_check` → `report_inventory` | session-1 doc audits |
| `safe_edit` | meta | `check_before_edit` → `edit_file` → `file_diff` | batch_edit failure-recovery (implement_fix) |

- **Registration:** new category `CAT_CHAIN = "chain"` in `registry.py`, gated by `tool_packs.chain`, registered through the `_register` spec table so `hot_reload` + `tool_anatomy` track them. `make_chain_tool(spec)` factory follows `_make_rag_tool` shape, wrapped in `tool_call`.

---

## Part 2 — Observation → Mining → Auto-Promotion

**2a. Hook + telemetry**
- Extend `_finish_tool_events` (`_helpers.py:132`) to record `{name, category, ts, args_summary, output_chars}`.
- Wire the dead `session_state.observe_tool_result` to capture ok/fail + result size.
- Persist ordered per-session sequences to SQLite (below).
- **Session-end hook** at loop exit (`engine.py:283`) — none exists today.

**2b. Mining (both triggers, flag-gated)**
- `pattern_miner.py` — `PatternMiner`: slide-window n-gram counting (n=2..4) over tool names; keep only deterministic read-only sequences; score by frequency × savings (`Σ output_chars − one chain call`) × determinism.
- **Session-end batch:** full mine over accumulated `tool_sequences` → writes candidates to `patterns` table.
- **In-loop lightweight:** cheap lookup against a cached pattern table checked during the turn; read-only promotion only; never blocks the hot path.
- Config flags (in `config.json`):
  ```
  "workflow_learn": {
    "enabled": true,
    "session_end_mining": true,
    "in_loop_mining": false,
    "auto_promote_readonly": true,
    "min_frequency": 3, "min_savings_tokens": 2000
  }
  ```
  `enabled:false` deactivates both triggers.

**2c. Promotion (`chain_promoter.py`)**
- Deterministic, no LLM in the decision. Read-only pattern meeting thresholds → templated `ChainSpec` written into a `chains_learned.py` that `_register_all()` picks up (appears as a real tool next reload). Write/edit patterns → status `pending_approval`, surfaced via the `workflow_status` tool for a confirm.

---

## Part 3 — Graph in SQLite + Subgraphs + Evolver

**3a. Storage (all SQLite, new `data/logs/workflow.db`, managed by `workflow_store.py`):**
- `tool_sequences` (session_id, seq JSON, outcome, ts)
- `patterns` (pattern JSON, frequency, determinism, savings, status)
- `chains` (chain_id, spec JSON, source, status, ts)
- `graph_nodes` / `graph_edges` / `graph_clusters` (id, label, shape, color, cluster_id, chain_id, stats JSON)
- `graph_notes` (section, text, tag do/avoid)
- `graph_state` (version, last_evolved_at)

**3b. Renderer (`scripts/render_graph.py` + shared JS template):**
- Reads SQLite → emits the `data={nodes,edges,clusters}` view → renders `Agent_graph.html` and per-workflow HTML via one dagre-d3 template.
- Subgraph merge: dagre compound nodes (`g.setParent(child, clusterId)`) — each workflow (`minimal_context`, `implement_fix`) becomes a **cluster node** inside the main graph.

**3c. `graph_evolver.py` (`GraphEvolver`) + `workflow_status` tool:**
- Runs from the session-end hook with mined patterns: adds shortcut edges (pattern already a graph path, executed redundantly), collapses a promoted pattern into a single `chain` node referencing its tool, appends DO/AVOID notes from outcome stats.
- `workflow_status` tool (observer/meta) exposes the live graph, pattern candidates, and pending-approval chains for the LLM/user.

---

## Phases (small scope, each independently shippable/reversible)
1. **P1:** chain runtime + 4 hand-written chains (biggest immediate token win).
2. **P2:** hook + telemetry + SQLite sequences.
3. **P3:** miner + dual triggers + deterministic promoter (+ approval gate).
4. **P4:** graph refactor to SQLite + shared renderer + subgraph clusters + evolver.

**Key risks & mitigations**
- Chain schema bloat adds ~2k tokens/turn → mitigated by `tool_packs.chain` gating.
- In-loop mining coupling → gated off by default, cached lookups only.
- Auto-registered chains accumulating → status field + `chains` table allows clean deactivation; no unregister path exists today, so evolver marks inactive rather than deleting.
- Side-effect safety → read-only auto, writes gated by approval.

Ready to start with P1 whenever you are — or I can drill into any part of this first.

---

# Implementation Status (updated 2026-08-02)

All 4 parts implemented, tested, and shipped. Deviations from the original plan are
flagged inline; each is a deliberate adaptation to the project's conventions
(one persistence path in SQLite, no file-generated modules, no LLM in the loop).

## P1 — Tool Chains: DONE
- `agent_core/tools/chain/chain_spec.py` — `ChainSpec` + `Step` dataclasses with
  `$input.X` / `$step.<key>.<path>` / literal binding and `collect` slicing.
- `chain_engine.py` — `ChainEngine.run()` resolves steps via the live registry,
  normalizes `ToolResult` + raw-string results (incl. `"Error"` prefix), binds
  outputs, applies per-step char caps + total token budget, short-circuits on
  errors, returns one JSON dict. `make_chain_tool(spec)` returns the wrapped fn.
- `chains.py` — the 4 handwritten chains: `probe_module`, `orient_symbols`,
  `doc_audit`, `safe_edit`.
- Registration — `CAT_CHAIN` in `registry.py`, exposed only when
  `tool_packs.chain` is on in config.json (default off). Hot-reload + anatomy track
  them via the `_register` spec table.

## P2 + P3 — Mining, Telemetry, Promotion: DONE (names adapted)
- Hooks: in-loop `_feed_chain_miner(session_id, tool, args)` in
  `loop/_helpers.py` (both stepper paths); session-end batch in
  `loop/engine.py` `finally:` block.
- **Deviation 2b:** miner is `chain/chain_miner.py` (`ChainMiner`), not
  `pattern_miner.py`. Same slide-window n-gram counting over tool names (n=2..4,
  `max_sequence_len`), periodic-repeat collapse (`[a,b,a,b]` → `[a,b]`), and
  repeated tools get unique step names (`tool_2`).
- **Deviation 2c:** no `chain_promoter.py` or generated `chains_learned.py`.
  Promotion is inline in the miner: read-only → `approved` (live via
  `_register_live`); write steps → `pending`. Persisted in SQLite and reloaded
  live on startup by `_register_stored_chains()` in `tools/__init__.py`.
- **Deviation config keys:** actual flags are `min_occurrences` (2),
  `max_sequence_len` (4), `in_loop`, `session_end`, `graph_evolve`,
  `context_hints`, `stale_after_days` (14), `min_savings_tokens` (0). The plan's
  `session_end_mining`/`in_loop_mining`/`min_frequency` names were simplified.

## P4 — Graph + Renderer + Evolver: DONE
- **Deviation 3a:** storage lives in the existing `kernel.db` via
  `chain_store.py` (not a new `workflow.db`/`workflow_store.py`) to honor the
  one-persistence-path rule. Tables: `tool_sequences`, `graph_nodes`,
  `graph_edges`, `graph_clusters`, `graph_notes`, `graph_state` (+ existing
  `chain_specs`, `chain_candidates`).
- `graph_evolver.py` (`GraphEvolver`) rebuilds the graph deterministically at
  session-end: chain clusters with ordered step nodes/edges, candidates as
  diamond shortcut edges, session usage as DO/AVOID notes + per-tool stats.
  Bumps `graph_state.version` on every evolve.
- `scripts/render_graph.py` serves the graph over HTTP (default port 8123, auto-opens the
  browser; `--output FILE` writes a static file instead). The served page re-renders from
  SQLite on every refresh, via one dagre-d3 template with compound cluster subgraphs
  (`g.setParent`) + a toggleable notes panel.
- `workflow_status` tool (observer) — `summary` | `full` | `candidates` |
  `evolve`.

## Post-plan additions (feedback loop, lifecycle, savings)
- **Feedback loop:** `graph_evolver.workflow_hints()` injects live chains +
  top DO/AVOID notes into turn context every step (gated by
  `workflow_learn.context_hints`). Chains are listed **only** when
  `tool_packs.chain` is enabled, so the agent is never told to call a tool it
  can't see.
- **Lifecycle:** `sweep_stale_chains()` demotes approved mined chains unused for
  > `stale_after_days` to `inactive` (unregistered) at session-end;
  `chain_admin activate` restores them. Handwritten chains are never touched.
  This closes the original "no unregister path" risk — `registry.unregister`
  now exists.
- **Savings scoring:** candidates carry `savings_est` ≈ (Σ step avg output
  tokens − largest step) × occurrences, from `tool_stats`. `min_savings_tokens`
  gates read-only auto-promotion (below bar → `pending`). Displayed by
  `chain_admin candidates` / `workflow_status candidates`.

## Known limits / next candidates
- `tool_packs.chain` is off by default; the whole pipeline is invisible to the
  LLM until it is enabled (the original schema-bloat mitigation). The context
  hints degrade gracefully to the "chains disabled" note.
- Mining was validated with synthetic feeds; validating against the 8 real
  transcripts in `sessions_analysis/` is a natural next step.
- All paths are smoke-tested via `conda run -n myenv python`; no formal test
  suite exists yet.