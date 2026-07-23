# Agent Orchestrator Reference

## Features Overview

| Capability | Description |
|------------|-------------|
| Auto-Research | Goal-autonomous research using shared agent loop (`/auto`) |
| Debate Mode | Structured topic exploration with belief tracking (`/argu`) |
| Kernel Memory | Persistent memory — retrieve, store, emit signals, create events |
| Simulation | Run, compare, and analyze agent-based simulations |
| File Operations | Read, write, edit, search, glob, execute commands, run tests |
| Git Tools | Status, diff, commit, log |
| Planning | Task todo lists, checkpoints, undo |
| Provider Switching | Swap LLM provider/model at runtime via API |
| Tool Pack Filtering | Enable/disable tool categories via env or config.json |
| MCP Integration | Expose kernel + simulation + code_rag tools to any MCP host (Claude Code, Cursor, opencode) |
| Code RAG | SQLite-based symbol search + call graph from codebase atlas output |
| Hot-Reload | Auto-detect file changes to tool modules and reload without restart |
| Simulation Timeout | Cap simulation run time via `timeout` parameter |

## Tools

All tools support **native function calling** (JSON Schema via `tools/schemas.py`) with text-JSON fallback. Tools return structured `ToolResult` objects internally (ok/error_type/message/suggestion) serialized to strings for the model.

### File Operations
| Tool | Purpose |
|------|---------|
| `read_file` | Read file (returns line-numbered output; lists nearby files on error) |
| `batch_read` | Read multiple non-kernel files in one call (warns on kernel files) — faster than sequential `read_file` calls |
| `read_section` | Read file content around a regex pattern match |
| `minimal_context_dump` | Chains blast radius → symbol source → peripheral API sigs into one capped file |
| `extract_symbols_to_file` | Fetch bodies of named symbols from atlas, write to destination with headers |
| `list_files` | List directory (recursive, depth-capped, skips noise dirs) |
| `write_to_file` | Write file (create/overwrite/append modes — no patch mode) |
| `edit_file` | Targeted replacement (unique old_string → new_string; rejects 0/>1 matches; shows diff) |
| `get_workspace_info` | Ground-truth: root path + top-level entries |
| `execute_command` | Run shell (configurable allowlist via config.json: ls, cat, pwd, echo, python, python3, pytest, pip, pip3, node, npm, npx, git) |
| `glob_search` | Find files by glob pattern (`**/*.py`, `src/**/*.ts`) |
| `grep_search` | Search file contents by regex (uses ripgrep if available) |
| `run_tests` | Discover and run tests using pytest or unittest |

### Git Tools (behind `git_tools_enabled` config flag)
| Tool | Purpose |
|------|---------|
| `git_status` | Show current git status |
| `git_diff` | Show git diff (optional path/staged filter) |
| `git_commit` | Commit staged changes with a message |
| `git_log` | Show recent commit history |

### Planning & Meta Tools
| Tool | Purpose |
|------|---------|
| `todo_write` | Create/update a task plan (actions: create, update, mark_done, clear) |
| `todo_read` | Read the current task plan |
| `undo_last_edit` | Restore the most recent checkpoint for a file |
| `checkpoint_info` | List available checkpoints |
| `ask_user_question` | Ask the user for input/clarification with up to 3 options per question (a custom text option is always added). Multiple questions can be asked at once — the user sees them one by one with a progress bar. Tool blocks until all answers are submitted. |

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

### Kernel Tools
| Tool | Purpose |
|------|---------|
| `kernel_retrieve` | Query memory |
| `kernel_emit_signal` | Emit observation |
| `kernel_store_context` | Store in memory |
| `kernel_get_memory` | Retrieve memory |
| `kernel_create_event` | Create event |
| `kernel_reload` | Reload tool modules from disk without restart |

### Simulation Tools
| Tool | Purpose |
|------|---------|
| `simulation_run` | Run simulation (opt. `timeout` param in secs) |
| `simulation_compare` | Compare runs |
| `simulation_list` | List runs |
| `simulation_get_signals` | Get signals |

---

## ToolRegistry (Pluggable Tools)

### ToolRegistry Class
Central registry for tool functions, schemas, and metadata, defined in `agent_core/tools/registry.py`.

```python
from agent_core.tools import registry
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT, CAT_CODE_RAG

# Get tools filtered by category (no file_ops for embedders)
kernel_sim = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])

# Get schemas for specific provider
schemas = registry.get_schemas(provider_name="gemini")  # function_declarations format
schemas = registry.get_schemas()                         # OpenAI "type: function" format

# Export as MCP tools
mcp_tools = registry.to_mcp_tools(categories=[CAT_KERNEL, CAT_SIM, CAT_CODE_RAG])

# Add middleware (wraps every tool)
registry.add_middleware(lambda name, fn: audit_wrap(name, fn, ...))
```

### Tool Registration Categories
| Category | Tools | Config key |
|----------|-------|------------|
| `file` | read_file, list_files, write_to_file, edit_file, execute_command, glob_search, grep_search, get_workspace_info | `file` |
| `kernel` | kernel_retrieve, kernel_emit_signal, kernel_store_context, kernel_get_memory, kernel_create_event, kernel_reload | `kernel` |
| `sim` | simulation_run, simulation_compare, simulation_list, simulation_get_signals | `sim` |
| `meta` | todo_write, todo_read, run_tests, undo_last_edit, checkpoint_info, ask_user_question, debate_step | `meta` |
| `code_rag` | get_symbol, get_symbols_meta, search_symbols, get_callers_callees, find_impact, get_index_info, file_api, call_chain, compare_apis, symbols_by_file | `code_rag` |
| `git` | git_status, git_diff, git_commit, git_log | `git` |

### Config-Based Tool Pack Filtering
Set `AGENT_TOOL_PACKS=file,kernel,sim` env var or `"tool_packs": ["kernel","sim"]` in `config.json` to control which tools are active. Default: all five packs.

For MCP integration (expose kernel+sim+code_rag to Claude Code, Cursor, opencode, etc.), see `ADAPTERS.md`.

### Hot-Reload Support
The MCP server (`agent_core/mcp_server.py`) auto-reloads tool modules when their source files change on disk:
- Tracks `st_mtime_ns` of `sim_ops.py`, `kernel_ops.py`, `code_rag.py`, `tools/__init__.py`
- Detects changes on the next tool call and re-imports + re-registers all tools
- No server restart needed — edits apply on next `pie_*` call
- Also available as explicit tool: `kernel_reload` (`pie_kernel_reload` via MCP)

---

## LLM Orchestration

### Provider Switching
`POST /api/switch-provider` (auth-protected) changes the active provider and model at runtime:
```json
// Request
{ "provider": "gemini", "model": "gemini-2.0-flash" }
// Response
{ "active": { "provider": "gemini", "model": "gemini-2.0-flash" } }
```
The frontend uses this for the provider switcher UI. The change is global until the next switch or server restart. `GET /api/providers` (auth-protected) lists available providers with their models.

### Architecture

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
  ├── context, prompts, commands, auto_research
  ├── tools/           ──► registry.py + file_ops, kernel_ops, sim_ops, schemas, plan_ops, code_rag, ...
  └── llm/             ──► orchestrator (timeouts/retries) + providers
       ├── gemini_provider.py
       ├── openrouter_provider.py
       └── mock_provider.py
```

### System Prompt
The system prompt (`system_instruction.md`) is loaded dynamically at server startup, replacing `{TOOL_LIST}`, `{TOOL_INPUT_FORMATS}`, and `{AGENTS_MD}` placeholders. Kernel and simulation tools are automatically included. The prompt contract enforces JSON-only responses (action+input or final, mutually exclusive).

### Native Function Calling
All providers support optional `tools=[]` parameter with JSON Schema definitions. Gemini uses `function_declarations` format, OpenRouter/OpenAI uses `type: "function"` format. Text-JSON and XML tool call formats serve as fallback.

### Streaming
All providers support `generate_stream()` for real-time token streaming. The agent loop uses streaming for the final answer path, falling back to fake chunking. Stop/cancel is supported via `threading.Event` checked between agent loop steps.

### Timeouts & Retries
`LLMOrchestrator.generate()` retries up to 3 times with exponential backoff (2^attempt seconds). Timeout per provider call is 60s. Retry count exposed in `/api/status` and response metadata.

### Multi-Tool Parallel Turns
When a provider returns multiple `tool_calls` in one response, the agent loop executes all of them (serialized) and feeds results back in a single follow-up, reducing round trips.

### Message Store & Context Compaction
Sessions and messages persist to SQLite (`agent_sessions.db`, WAL mode, thread-safe). When a session exceeds 100 messages, older messages are trimmed (keeps last 50). Sessions survive server restarts.

---

## Checkpoints / Undo
- Before `edit_file` or `write_to_file` (overwrite mode), a checkpoint is saved to `.agent_checkpoints/` directory
- `save_checkpoint()` copies the file before modification (when `enable_checkpoints: true` in config.json)
- `undo_last_edit` restores the most recent checkpoint for a given file
- `checkpoint_info` lists available checkpoints
- Configurable max checkpoints via `max_checkpoints` in config.json

## Path Resolution (workspace.py)

All file tools resolve paths through `agent_core.workspace.resolve()`. The root defaults to process CWD, overridable via `AGENT_WORKSPACE_ROOT`. Leading slashes in model-supplied paths are treated as workspace-relative. A `PathEscapeError` is raised if `..` traversal or symlinks attempt to escape the workspace.

---

## Auth & CORS

- JWT-based auth on WebSocket (`/ws/agent?token=...`) and all REST endpoints except `/api/status`
- `JWT_SECRET` env var (auto-generated random hex if not set)
- CORS restricted to `CORS_ORIGINS` env var (default: `http://localhost:3000,http://localhost:8001`)

## Per-User Workspace

Each authenticated user gets an isolated workspace rooted at `{WORKSPACE_BASE}/{user_id}/`. `WORKSPACE_BASE` defaults to `{project_root}/workspaces/`, overridable via `AGENT_WORKSPACE_BASE` env var.

## Sandbox Shell

Optional Docker sandboxing for `execute_command`: when `sandbox_enabled: true`, commands run in a read-only Docker container with no network access. Falls back with a clear error if Docker is unavailable.

## Secrets Redaction

Regex patterns in `config.json` `secrets_patterns` redact API keys and tokens from tool results and stored messages to prevent credential leakage.

## Rate Limiting

Token-bucket per user: `llm_calls_per_minute` (default: 10) and `tool_writes_per_minute` (default: 30), configurable via `config.json` `rate_limits`.

## Audit Log

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
