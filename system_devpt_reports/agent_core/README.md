# Agent Orchestrator Reference

## Architecture

```
server.py
    │
    ▼
agent_core/
  ├── agent_loop       ──► tools + schemas + multi-tool calls + failure breaker
  │                    ──► builds explicit message arrays from msg_store (when available)
  ├── message_store    ──► SQLite session/message persistence + compaction
  ├── workspace        ──► single path resolver (used by all file tools + server APIs)
  ├── providers_setup  ──► agent_core.llm.*
  ├── planning/        ──► local_planner.py (LocalPlanner — routing + local model orchestration)
  ├── context, prompts, commands, auto_research
  ├── tools/           ──► registry.py + file_ops, kernel_ops, sim_ops, schemas, plan_ops, code_rag, ...
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
| Pluggable Tools | File Ops, Meta, Code RAG, Kernel, Debate, Simulation, Git, Observer|
| Auto-Research | Goal-autonomous research using shared agent loop (`/auto`) |
| Debate Mode | Structured topic exploration with belief tracking (`/argu`) |
| Provider Switching | Swap LLM provider/model at runtime via API |
| Local Model Routing | Route simple file/meta tool calls to a local FunctionGemma model via Ollama; fall back to cloud for complex reasoning — configurable via `local_model` in config.json |
| Tool Pack Filtering | Enable/disable tool categories via env or config.json |
| MCP Integration | Expose kernel + simulation + code_rag tools to any MCP host (Claude Code, Cursor, opencode) |
| Code RAG | SQLite-based symbol search + call graph from codebase atlas output |
| Hot-Reload | Auto-detect file changes to tool modules and reload without restart |
| Tool Call Stats | Per-tool call count, avg duration, error rate, token estimate — tracked in `kernel.db` |
| File Access Stats | Per-file read/write/edit count — tracks churn and most-accessed files |
| User Reading Budget | Daily budget for LLM output lines shown to user; auto-alerts when &lt;20% remaining |
| Hot-Reload MCP Tool | `hot_reload` re-registers tools + sends `notifications/tools/list_changed` to client — no restart needed for next session |
| Tool Failure Logging | Failed tool calls auto-saved to `generic_memory` with error, args, and timestamp |

## Tools

All tools support **native function calling** (JSON Schema via `tools/schemas.py`) with text-JSON fallback. Tools return structured `ToolResult` objects internally (ok/error_type/message/suggestion) serialized to strings for the model.

### Approximate size of the tool schemas sent each turn

Measured programmatically (JSON-serialized with 2-space indent):

| Format | Estimated tokens |
|---|---|
| **OpenAI-style** (all 58 tools) | **~10,828** |
| **Gemini-style** (all 58 tools) | **~10,838** |

**Per-tool breakdown (range):** Smallest = `todo_read` (193 chars), Largest = `expand_topic` (1,720 chars). Most tools are 300–900 chars.

**Per-category breakdown (OpenAI format):**

| Category | Tools | Chars | Est. tokens |
|---|---|---|---|
| `code_rag` (20 tools) | 20 | 15,132 | ~3,783 |
| `file` (10 tools) | 10 | 7,745 | ~1,936 |
| `meta` (8 tools) | 8 | 5,653 | ~1,413 |
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

### Meta Tools
| Tool | Purpose |
|------|---------|
| `check_path_exists` | Path to check, relative to workspace root |
| `get_workspace_info` | Ground-truth: root path + top-level entries |
| `file_diff` | Verify edits by seeing 5 changed lines instead of re-reading the full file |
| `read_section` | Read file content around a regex pattern match |
| `undo_last_edit` | Restore the most recent checkpoint for a file |
| `checkpoint_info` | List available checkpoints |
| `run_tests` | Discover and run tests using pytest or unittest |
| `subagent_task` | Spawns a full agent loop with its own context, Returns the sub-agent's final answer |

### Code RAG Tools (from codebase atlas, separate `code_rag` category)
| Tool | Purpose |
|------|---------|
| `get_symbol` | Look up a function/class by name with full source code, signature, and docstring |
| `get_symbols_meta` | Batch metadata lookup (name, signature, token_count, risk_level, lines) without full source — browse cheaply then call `get_symbol` for the ones worth fetching |
| `search_symbols` | FTS5 full-text search across symbol names, docstrings, and code |
| `get_callers_callees` | Recursive graph traversal — who calls this symbol and what it calls |
| `find_impact` | List everything that depends on a symbol (all transitive callers) |
| `get_index_info` | Real-time atlas stats (symbols, edges, token ranges, risk distribution) — call once at session start to calibrate budget |
| `file_api` | Public API surface of a file: classes → method signatures (with docstring first line), module-level functions, no bodies. Hierarchical, class-organized. |
| `call_chain` | Shortest call chain from a function to any symbol in another module via BFS over `call_edges` |
| `compare_apis` | API-level diff between two files (only_in_a, only_in_b, signature_mismatches) |
| `symbols_by_file` | Complete flat symbol inventory of a file by path alone — no query needed |
| `atlas_status` | Check if atlas is indexed, ingestion timestamp, file/symbol/call-edge counts |
| `project_root` | Return absolute project root and codebase root paths |
| `batch_file_api` | Query atlas for API surfaces of multiple kernel files in one call — avoids sequential `file_api` round trips |
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

---

### Config-Based Tool Pack Filtering
Set `AGENT_TOOL_PACKS=file,kernel,sim` env var or `"tool_packs": ["kernel","sim"]` in `config.json` to control which tools are active. Default: all five packs.

For MCP integration (expose kernel+sim+code_rag to Claude Code, Cursor, opencode, etc.), see `ADAPTERS.md`.

### Hot-Reload Support
The MCP server (`agent_core/mcp_server.py`) auto-reloads tool modules when their source files change on disk:
- Tracks `st_mtime_ns` of `sim_ops.py`, `kernel_ops.py`, `code_rag.py`, `tools/__init__.py`
- Detects changes on the next tool call and re-imports + re-registers all tools
- No server restart needed — edits apply on next `pie_*` call
- Available as explicit tool: `kernel_reload` (`pie_kernel_reload` via MCP)
- **`hot_reload` built-in tool**: re-registers all tools AND sends `notifications/tools/list_changed` MCP notification so the client re-fetches the tool list. New tools appear without restarting the MCP connection.

### Provider Switching
`POST /api/switch-provider` (auth-protected) changes the active provider and model at runtime:
```json
// Request
{ "provider": "gemini", "model": "gemini-2.0-flash" }
// Response
{ "active": { "provider": "gemini", "model": "gemini-2.0-flash" } }
```
The frontend uses this for the provider switcher UI. The change is global until the next switch or server restart. `GET /api/providers` (auth-protected) lists available providers with their models.

### System Prompt
The system prompt is assembled at server startup from fragments in `prompt_fragments/` by `agent_core/prompts.py`. Fragments are conditionally included based on active tool packs (`CAT_FILE`, `CAT_KERNEL`, `CAT_SIM`, `CAT_CODE_RAG`). The assembly order is: `00_base_persona.md`, `10_tool_list.md`, `20_file_ops_workflow.md` (file pack), `25_code_rag.md` (code_rag pack), `30_kernel_playbook.md` (kernel pack), `40_sim_playbook.md` (sim pack), `51_file_io_details.md` (file pack), `60_response_contract.md`, and `70_embed_mode.md` (excluded when file pack is active). The `{AGENTS_MD}` placeholder is replaced with AGENTS.md content when enabled. The `60_response_contract.md` fragment enforces native function calling with a 3–4 tool call budget and forced termination.

### Native Function Calling
All providers support optional `tools=[]` parameter with JSON Schema definitions. Gemini uses `function_declarations` format, OpenRouter/OpenAI uses `type: "function"` format. Text-JSON and XML tool call formats serve as fallback.

### Streaming
All providers support `generate_stream()` for real-time token streaming. The agent loop uses streaming for the final answer path, falling back to fake chunking. Stop/cancel is supported via `threading.Event` checked between agent loop steps.

## Local Model Routing (Experimental)

When `local_model.enabled` is `true` in `config.json`, a small local model (e.g. FunctionGemma via Ollama) handles simple file/meta tool calls before falling back to the cloud LLM.

**How it works per step:**
1. `LocalPlanner.should_route_local()` checks: is the query simple (short, keywords like `check`/`list`/`find`)? Are recent tool calls all in file/meta categories? Fewer than `max_local_steps` consecutive local steps?
2. If yes → `OllamaProvider` is called with only `file`+`meta` tool schemas (18 tools instead of all 40+)
3. If FunctionGemma returns valid tool calls → execute locally, inject results, continue
4. If it produces a final answer → done
5. If it fails (parse error, invalid tool, connection error) → `record_fallback()`, next step routes to cloud LLM

**Config** (`config.json`):
```json
"local_model": {
    "enabled": false,
    "provider": "ollama",
    "model": "gemma-2-2b-it",
    "endpoint": "http://localhost:11434",
    "local_categories": ["file", "meta"],
    "fallback_to_cloud": true,
    "max_local_steps": 3,
    "timeout_seconds": 30
}
```

**Files:** `agent_core/planning/local_planner.py`, `agent_core/providers/ollama_provider.py`

**When disabled** (`enabled: false`), zero code path change — behaves exactly as before with no added latency.

### Timeouts & Retries
`LLMOrchestrator.generate()` retries up to 3 times with exponential backoff (2^attempt seconds). Timeout per provider call is 60s. Retry count exposed in `/api/status` and response metadata.

### Multi-Tool Parallel Turns
When a provider returns multiple `tool_calls` in one response, the agent loop executes all of them (serialized) and feeds results back in a single follow-up, reducing round trips.

### Message Store & Context Compaction
Sessions and messages persist to SQLite (`agent_sessions.db`, WAL mode, thread-safe). When a session exceeds 100 messages, older messages are trimmed (keeps last 50). Sessions survive server restarts.

---

### Checkpoints / Undo
- Before `edit_file` or `write_to_file` (overwrite mode), a checkpoint is saved to `.agent_checkpoints/` directory
- `save_checkpoint()` copies the file before modification (when `enable_checkpoints: true` in config.json)
- `undo_last_edit` restores the most recent checkpoint for a given file
- `checkpoint_info` lists available checkpoints
- Configurable max checkpoints via `max_checkpoints` in config.json

### Path Resolution (workspace.py)
All file tools resolve paths through `agent_core.workspace.resolve()`. The root defaults to process CWD, overridable via `AGENT_WORKSPACE_ROOT`. Leading slashes in model-supplied paths are treated as workspace-relative. A `PathEscapeError` is raised if `..` traversal or symlinks attempt to escape the workspace.

### Auth & CORS
- JWT-based auth on WebSocket (`/ws/agent?token=...`) and all REST endpoints except `/api/status`
- `JWT_SECRET` env var (auto-generated random hex if not set)
- CORS restricted to `CORS_ORIGINS` env var (default: `http://localhost:3000,http://localhost:8001`)

### Per-User Workspace
Each authenticated user gets an isolated workspace rooted at `{WORKSPACE_BASE}/{user_id}/`. `WORKSPACE_BASE` defaults to `{project_root}/workspaces/`, overridable via `AGENT_WORKSPACE_BASE` env var.

### Sandbox Shell
Optional Docker sandboxing for `execute_command`: when `sandbox_enabled: true`, commands run in a read-only Docker container with no network access. Falls back with a clear error if Docker is unavailable.

### Secrets Redaction
Regex patterns in `config.json` `secrets_patterns` redact API keys and tokens from tool results and stored messages to prevent credential leakage.

### Rate Limiting
Token-bucket per user: `llm_calls_per_minute` (default: 10) and `tool_writes_per_minute` (default: 30), configurable via `config.json` `rate_limits`.

### Audit Log
Every tool invocation is logged to SQLite (`agent_audit.db`) with user_id, tool name, input hash, and timestamp. Queryable via `/api/audit` endpoint.

### Code RAG: 
- Named lookups: agent should call `get_symbol(names=[...])` first; `search_symbols` only on `missing_names` / unknown names
- Removed `prefetched_symbols` + `batch_get_symbol_hint` from `search_symbols` (bulk-prefetching unrelated FTS hits)
- `get_symbol_tool` returns `missing_names` + hint when some names fail
- Tool functions must be plain (no `@tool_call`) in ops module to avoid circular import; decorator applied in `__init__.py` registration.
- `file_api` / `symbols_by_file`: accept relative or absolute paths; resolved via `_resolve_path()` which prepends `CODEBASE_ROOT` for relative paths.
- `call_chain` uses BFS over `call_edges` table (undirected traversal). Returns shortest path or clear error.
- `compare_apis` delegates to `file_api` internally for both files, then diffs by `(parent_name, symbol_name)` key.
- `pie_file_api`, `pie_call_chain`, `pie_compare_apis`, `pie_symbols_by_file`
All 4 added to `code_rag.py` (`CodeRAG` class methods + tool functions), registered in `schemas.py` + `__init__.py` under `CAT_CODE_RAG`. Path resolution via `_resolve_path()` prepending `CODEBASE_ROOT`.

### Hot-Reload Notes:
- `_register_all()` in `__init__.py` imports functions inside the function body — supports `importlib.reload` + re-registration on hot-reload
- `mcp_server.py:_reload_if_changed()` compares `st_mtime_ns` before every tool call — only reloads when file timestamps changed
- `mcp_server.py:_do_reload()` calls `importlib.reload` on each hot module, then re-runs `_register_all()`
- Explicit `kernel_reload` tool (`kernel_ops.py`) does the same via tool call
- `.pyc` cache (`__pycache__/`) is automatically invalidated by `importlib.reload` — no manual cleanup needed

### Observability (kernel.db)
Three dedicated tables in `data/kernel.db` track telemetry:

**`tool_stats`** — per-tool call log:
- `tool_name`, `call_count`, `last_called_at`, `total_duration_ms`, `error_count`, `output_chars`, `token_estimate`
- Auto-recorded in `mcp_server.py:call_mcp_tool()` finally block
- Derived: `avg_duration_ms`, `error_rate`, `avg_chars`, `avg_tokens`
- Exposed via `tool_stats` tool; flags tools with >30% error rate

**`file_access`** — per-file operation log:
- `file_path`, `operation` (read/write/edit), `access_count`, `last_accessed_at`
- Recorded in `file_ops.py:read_file()`, `write_to_file()`, `edit_file()`
- Exposed via `file_stats` tool; flags files with >5 total ops as churn candidates

**`daily_read_budget`** — daily user reading cap:
- `date`, `lines_used`, `budget` (default 500)
- `user_reading_budget` tool: records LLM output lines, returns usage/remaining
- Alerts at <20% remaining; resets daily

**`generic_memory`** — tool failure auto-logging:
- Failed tool calls saved with `memory_type="tool_failure"` in `call_mcp_tool()` except block
- Payload: `{"tool": name, "error": text, "ts": timestamp, "args": truncated_args}`
