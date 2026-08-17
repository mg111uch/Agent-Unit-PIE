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
| Tool Search | Hybrid dynamic tool exposure: per-turn payload shrunk to an always-on base set + request-ranked top-k; `find_tool`/`get_tool_schema` let the model discover and call any enabled tool on demand — gated by `tool_search.*` in config |
| Tool Mode | Restrict active tools by preset via `tool_mode`: `all` (no filtering), `read_only`, `shell_only` — enforced on schemas and execution |
| MCP Integration | Exposes tools over MCP: always-on set = CAT_META + CAT_SEARCH (`mcp_always_expose = "meta"`, default) or CAT_SEARCH only (`"search"`), CAT_FILE never, other tool packs only when enabled in config |
| MCP Playbook Resources | Active-pack tool playbooks exposed as MCP resources (`pie://playbooks/<pack>`) — client fetches once per session; no per-turn sending |
| Code RAG | SQLite-based symbol search + call graph from codebase atlas output |
| Hot-Reload | Auto-detect tool module file changes and reload without restart; explicit `kernel_reload` and `hot_reload` tools |
| Tool Call Stats | Per-tool call count, avg duration, error rate, token estimate — tracked in `kernel.db`; native loop and MCP both record durations per call |
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
| Deterministic Tool factory Fast-path | Unambiguous single-intent prompts (find/read/list/check-exists/create-dir) run one allowlisted tool call directly with 0 LLM calls |

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

### Tool Search (dynamic tool exposure)

When `tool_search.enabled` is on, the loop sends the model only an **always-on
base set** (configurable via `tool_search.base_tools`; `find_tool` /
`get_tool_schema` are always included) plus a **lexically-ranked top-k**
(`tool_search.top_k`) of enabled tools matched against the user request —
dropping the full catalog from ~10.8k tokens to roughly the base set (~2.8k).
Tool schemas from `code_rag` (~3.8k), `kernel` (~1.4k), `sim`/`debate`/`git`/
`observer` (~2.7k) are only sent when actually retrieved.

- `find_tool(query)` — searches the **enabled-only** catalog (respects
  `tool_packs` + `tool_mode`) by capability keywords; returns name, category,
  one-line description, and compact `name:type(req/opt)` params.
- `get_tool_schema(name)` — returns the full JSON schema for a named tool.
- The model then calls the discovered tool **directly by name**: execution runs
  against the full registry, so no schema re-injection is needed. After a
  `get_tool_schema` step, the discovered tool's schema is appended to the
  catalog for the next chained step (native-FC friendly).
- Registered under `CAT_SEARCH` (new category). Always exposed over MCP in
  either `mcp_always_expose` mode (`meta` = CAT_META + CAT_SEARCH, `search` =
  CAT_SEARCH only); in the loop they are force-included by name
  (`SEARCH_TOOL_NAMES`) independent of pack config.

### File Operations
| Tool | Purpose |
|------|---------|
| `Read` | Read file (returns line-numbered output; lists nearby files on error) ; **batch_read mode** via `paths=[...]` — reads multiple files in one call, each with optional own `offset`/`limit`/`line_numbers`; **auto-cache hook** — if file unchanged since last read, return `(cached: 544 lines)` instead of full content - Also lists files when dir path is given|
| `Write` | Write file (create/overwrite/append modes — no patch mode) |
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
| `find_tool` | Lexical search over the enabled tool catalog by capability keywords; returns name, category, one-liner, compact params (`name:type`, req/opt) — used to discover non-base tools |
| `get_tool_schema` | Full JSON schema (params, types, descriptions, required) for one/many tools by exact name — used after `find_tool` when the precise argument contract is needed |

### Chain Tools (composite `chain` category registered under `CAT_META`)
| Tool | Purpose |
|------|---------|
| `probe_module` | file_skeleton → who_imports → find_impact (optional) — one-call module orientation |
| `orient_symbols` | get_index_info → file_api → get_symbols_meta → get_symbol — cheap-to-full symbol fetch |
| `doc_audit` | report_freshness → report_schema_check → report_inventory — doc health in one call |
| `safe_edit` | check_before_edit → edit_file → file_diff — validate, apply, and verify a single-file edit batch |

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

## Tool workings

### Q1 — In my native agent loop if cat_meta pack is active, then does each llm tool turn sends schema of tool_group of file pack plus full schema of all the cat_meta tools.
No, not the way you think. Current defaults (`tool_group_routing=true`, tool_search disabled):
- `tool_categories = resolve_active_tool_packs()` (engine.py:519) → `get_schemas()` first pulls full schemas of all active packs (file + meta).
- Then `_filter_names(...)` intersects that against the routed group (`_READ`/`_LIST`/`_BASE`/…, tool_groups.py:16-26). Those groups contain **only file tools** (`Read`, `grep_search`, `edit_file`, `Write`, …) — **zero meta tools**.
- So the meta schemas get **filtered out** — the per-turn payload is just the routed file group. Meta tools aren't sent at all (they stay callable via the registry, but the model gets no schema/description for them).
Meta schemas only appear per-turn when `tool_group_routing=false` (then full file + full meta).

### Q2 — How does mcp work by sending schema once to the client but my native agent loop has to get tool schema in each tool turn.
MCP "sends schema once" is a half-truth. The MCP server pushes `tools/list` (name + description + inputSchema) *once to the client*, which caches it. But the client still re-injects those schemas into the LLM request every turn — that's the client's job, not the server's. The server just stops repeating the transfer; context cost per LLM call remains.
The native loop is the inverse: the loop owns the per-turn payload (`build_catalog` → provider `tools=` each step), so it can *shrink* it per request (routing / tool_search / chained-step pruning). That per-turn rebuild is a deliberate lever for context control, not a limitation — and the schemas are static per session anyway, so rebuilding is cheap (no I/O).

### Q3 — How does an MCP client get the tool playbooks of active packs?
The server exposes each active-pack playbook as an MCP **resource** (`pie://playbooks/<pack>`, e.g. `pie://playbooks/code_rag`), derived from `prompt_fragments` gating (`FRAGMENT_ORDER`). The client calls `resources/list` once and reads the ones it wants via `resources/read` (resource-aware clients auto-load them into context at session start). MCP has no server→client content-push, so there is **no per-user-message or per-tool-turn sending** — the client pulls once and re-injects as it sees fit. The server advertises `resources` capability with `listChanged`; `hot_reload` emits `notifications/resources/list_changed`. `find_tool`/`get_tool_schema` descriptions point at the resource URIs so the model can discover them.

----------
