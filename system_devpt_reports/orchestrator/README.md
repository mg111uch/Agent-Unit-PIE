# Agent Orchestrator Reference

Single reference for project usage.

---

## Getting Started

### Run Agent
```bash
cd Agentic_Unit_PIE/codebase
conda run -n myenv python server.py
```

#### Environment Variables
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `AGENT_WORKSPACE_ROOT` — override workspace root (default: process CWD)
- `JWT_SECRET` — JWT signing secret (default: auto-generated random hex)
- `CORS_ORIGINS` — comma-separated allowed origins (default: `http://localhost:3000,http://localhost:8001`)
- `AGENT_PORT` — server port (default: 8001)

#### Config File (`config.json`)
- `allowed_commands` — list of allowed shell commands for `execute_command`
- `git_tools_enabled` — enable/disable git tools (default: true)
- `enable_checkpoints` — enable/disable checkpoint system (default: true)
- `max_checkpoints` — max checkpoint files to keep (default: 50)
- `agents_md_enabled` — enable/disable AGENTS.md bootstrap (default: true)

### Exit
```bash
exit
```

---

## Commands

## `/argu explore <topic>` - Debate Mode

Explore topics through structured debate with belief tracking.

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

### Run via Python directly
```python
from argu_god.engine.loop import run_explore_loop
run_explore_loop("theism_atheism")
```

### Run via Web Server
```bash
conda run -n myenv python -m argu_god.main
# Open http://localhost:8000
```

### Topics
- `theism_atheism` (default)
- Add new topics in `modules/argu_god/topics/<topic>/graph.json`

---

**Example:**
```
>> /argu explore theism_atheism
```

**Response options:**
| Option | Meaning |
|--------|---------|
| 1 | Agree |
| 2 | Counter |
| 3 | Explore/Uncertain |
| 4 | Write own response |

System tracks beliefs, detects contradictions, stores in kernel.

---

### /auto - Auto-Research
Goal-autonomous research using the shared agent loop.

```
/auto "research question"
```

**Examples:**
```
>> /auto Why is population declining?
>> /auto Compare healer vs no-healer scenarios
```

**Behavior:**
- Uses `run_agent_turn()` from the shared loop (same parsing, failure breaker, streaming)
- No hard kernel dependency — proceeds with file/shell tools if kernel is unavailable
- Findings stored to kernel memory if available
- Max iterations configurable (default: 5)

---

## Tools

All tools support **native function calling** (JSON Schema via `tools/schemas.py`) with text-JSON fallback. Tools return structured `ToolResult` objects internally (ok/error_type/message/suggestion) serialized to strings for the model.

### File Operations
| Tool | Purpose |
|------|---------|
| `read_file` | Read file (returns line-numbered output; lists nearby files on error) |
| `read_file_range` | Read portion of a file with offset (1-based) and optional limit |
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

### Kernel Tools
| Tool | Purpose |
|------|---------|
| `kernel_retrieve` | Query memory |
| `kernel_emit_signal` | Emit observation |
| `kernel_store_context` | Store in memory |
| `kernel_get_memory` | Retrieve memory |
| `kernel_create_event` | Create event |

### Simulation Tools
| Tool | Purpose |
|------|---------|
| `simulation_run` | Run simulation |
| `simulation_compare` | Compare runs |
| `simulation_list` | List runs |
| `simulation_get_signals` | Get signals |

---

## Simulation Usage

### Via Agent
```
Run a simulation with 50 years and 100 initial population
```

### Via Python
```python
from modules.simulators.simulation_connector import SimulationConnector
conn = SimulationConnector()
result = conn.run_and_extract({'years': 20, 'initial_pop': 50}, 'run_001')
print(conn.compare_runs(['run_001', 'run_002']))
```

### Parameters
| Parameter | Default |
|-----------|----------|
| `years` | 50 |
| `initial_pop` | 50 |
| `initial_healers` | 1 |
| `grid_width` | 10 |

---

## ToolRegistry (Pluggable Tools)

### ToolRegistry Class
Central registry for tool functions, schemas, and metadata, defined in `agent_core/tools/registry.py`.

```python
from agent_core.tools import registry
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT

# Get tools filtered by category (no file_ops for embedders)
kernel_sim = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])

# Get schemas for specific provider
schemas = registry.get_schemas(provider_name="gemini")  # function_declarations format
schemas = registry.get_schemas()                         # OpenAI "type: function" format

# Export as MCP tools
mcp_tools = registry.to_mcp_tools(categories=[CAT_KERNEL, CAT_SIM])

# Add middleware (wraps every tool)
registry.add_middleware(lambda name, fn: audit_wrap(name, fn, ...))
```

### Tool Registration Categories
| Category | Tools | Config key |
|----------|-------|------------|
| `file` | read_file, list_files, write_to_file, edit_file, execute_command, glob_search, grep_search, get_workspace_info | `file` |
| `kernel` | kernel_retrieve, kernel_emit_signal, kernel_store_context, kernel_get_memory, kernel_create_event | `kernel` |
| `sim` | simulation_run, simulation_compare, simulation_list, simulation_get_signals | `sim` |
| `meta` | todo_write, todo_read, run_tests, undo_last_edit, checkpoint_info | `meta` |
| `git` | git_status, git_diff, git_commit, git_log | `git` |

### Config-Based Tool Pack Filtering
Set `AGENT_TOOL_PACKS=file,kernel,sim` env var or `"tool_packs": ["kernel","sim"]` in `config.json` to control which tools are active. Default: all five packs.

### MCP Server (agent_core/mcp_server.py)
Exposes kernel+sim tools via stdio MCP transport, usable by any MCP host (Claude Code, Cursor, etc.):

```bash
python -m agent_core.mcp_server
```

Claude Code integration:
```json
{
  "pie-kernel-sim": {
    "command": "python",
    "args": ["-m", "agent_core.mcp_server"]
  }
}
```

### Backward Compatibility
`TOOLS` and `TOOL_META` globals preserved in `agent_core.tools` for existing import sites. They are snapshots of the registry at import time. For dynamic filtering, use `registry.get_tools(categories=[...])`.

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
  ├── tools/           ──► registry.py + file_ops, kernel_ops, sim_ops, schemas, plan_ops, ...
  └── llm/             ──► orchestrator (timeouts/retries) + providers
       ├── gemini_provider.py
       ├── openrouter_provider.py
       └── mock_provider.py
```

### System Prompt
The system prompt (`system_instruction.md`) is loaded dynamically at server startup:
- `{TOOL_LIST}` — replaced with a markdown table of all registered tools + descriptions
- `{TOOL_INPUT_FORMATS}` — replaced with a markdown table of tool input formats
- `{AGENTS_MD}` — replaced with AGENTS.md content from workspace root (if `agents_md_enabled: true`)
- Kernel and simulation tools are automatically included in the tables
- Prompt contract enforces JSON-only responses (action+input or final, mutually exclusive)

### Native Function Calling
All providers support optional `tools=[]` parameter with JSON Schema definitions:
- Tool schemas defined once in `agent_core/tools/schemas.py`
- Gemini uses `function_declarations` format
- OpenRouter/OpenAI uses `type: "function"` format
- Responses with `tool_calls` are parsed by `response_parse.parse_provider_response()`
- Text-JSON and XML tool call formats serve as fallback

### Structured Tool Results
Tools now return structured `ToolResult` objects:
```python
@dataclass
class ToolResult:
    ok: bool
    data: str = ""
    error_type: str = ""
    message: str = ""
    suggestion: str = ""
```
Errors are typed: `not_found`, `not_unique`, `permission`, `path_escape`, `too_large`, `timeout`, `internal`.

### Real Token Streaming
All providers support `generate_stream()` for real-time token streaming:
- **Gemini:** uses `generate_content_stream()` yielding text chunks as they arrive
- **OpenRouter:** uses `stream=True` on the OpenAI-compatible API
- **Mock:** simulates streaming for development
- The agent loop uses streaming for the final answer path, falling back to fake chunking
- Orchestrator wrapper `generate_stream()` provides unified streaming with non-streaming fallback

### Stop/Cancel Generation
- Client sends `{"type": "cancel"}` via WebSocket to stop the current generation
- Server sets a `threading.Event` checked between agent loop steps
- Frontend shows a "Stop generation" button when `isBusy`

### LLM Timeouts & Retries
- `LLMOrchestrator.generate()` retries up to 3 times with exponential backoff (2^attempt seconds)
- Timeout per provider call is 60s
- Retry count exposed in `/api/status` and response metadata

### Server Status API
`GET /api/status` (no auth) returns:
```json
{
  "status": "ok",
  "provider": "openrouter",
  "model": "anthropic/claude-sonnet-20241022",
  "kernel": true,
  "tools": ["read_file", "edit_file", ...],
  "tool_packs": ["file", "kernel", "sim", "meta", "git"],
  "workspace": "/path/to/workspace",
  "total_requests": 42,
  "total_failures": 1,
  "total_tokens": 15000,
  "total_cost": 0.15,
  "total_retries": 2,
  "sessions": 3
}
```

### Multi-Tool Parallel Turns
When a provider returns multiple `tool_calls` in one response, the agent loop executes all of them (serialized) and feeds results back in a single follow-up. This reduces round trips for multi-file operations.

### Message Store & Context Compaction
Sessions and messages persist to SQLite (`agent_sessions.db`, WAL mode, thread-safe):
- Every user message and tool result is stored per session
- When a session exceeds 100 messages, older messages are trimmed (keeps last 50)
- Sessions survive server restarts
- API: `MessageStore` in `agent_core/message_store.py`

### Explicit Message Arrays (Phase 1 gap closed)
The agent loop (`iter_agent_events`) now accepts optional `msg_store` and `session_id`.
When provided, it builds explicit message arrays from the store + in-memory tool results,
and passes them to all providers via a new `messages` parameter, **replacing** the old
growing-string `current_input` + provider-side `conversation_id` approach for that path.

**Per-provider handling of `messages`:**
| Provider | Mechanism |
|----------|-----------|
| Gemini | `models.generate_content()` with `contents` + `system_instruction` in config |
| OpenRouter | `_convert_messages_to_openai()` → OpenAI chat completions `messages` |
| Mock | Accepted but ignored (backward compat) |

---

## Checkpoints / Undo
- Before `edit_file` or `write_to_file` (overwrite mode), a checkpoint is saved to `.agent_checkpoints/` directory
- `save_checkpoint()` copies the file before modification (when `enable_checkpoints: true` in config.json)
- `undo_last_edit` restores the most recent checkpoint for a given file
- `checkpoint_info` lists available checkpoints
- Configurable max checkpoints via `max_checkpoints` in config.json

## Path Resolution (workspace.py)

All file tools (`read_file`, `list_files`, `write_to_file`, `edit_file`) and the server's
`/api/files/*` endpoints resolve paths through `agent_core.workspace.resolve()`. This ensures
the agent and frontend always agree on the root. The root defaults to process CWD and is
overridable via the `AGENT_WORKSPACE_ROOT` environment variable.

Leading slashes in model-supplied paths are treated as workspace-relative (not OS-root), matching
the convention most coding agents expect. A `PathEscapeError` is raised if `..` traversal or
symlinks attempt to escape the workspace.

---

## Auth & CORS

- JWT-based auth on WebSocket (`/ws/agent?token=...`) and all REST endpoints except `/api/status`
- `JWT_SECRET` env var (auto-generated random hex if not set)
- CORS restricted to `CORS_ORIGINS` env var (default: `http://localhost:3000,http://localhost:8001`)
- `allow_credentials=False` (auth via token query param, not cookies)

## Per-User Workspace

Each authenticated user gets an isolated workspace rooted at `{WORKSPACE_BASE}/{user_id}/`.
- `WORKSPACE_BASE` defaults to `{project_root}/workspaces/`, overridable via `AGENT_WORKSPACE_BASE` env var
- `workspace.set_user_workspace(user_id)` creates the directory and sets a thread-local root
- `resolve()` and `to_relative()` use the thread-local root when set, falling back to global `WORKSPACE_ROOT`
- REST endpoints (`/api/files/*`) set user workspace from JWT `id` claim
- WebSocket handler sets user workspace on connect, clears on disconnect

## Sandbox Shell

- Config flag `sandbox_enabled` in `config.json` (default: `false`)
- When enabled, `execute_command` wraps commands via Docker: `docker run --rm --network none -v {workspace}:/workspace:ro python:3.11-slim sh -c "{cmd}"`
- Falls back with a clear error message if Docker is unavailable
- Preserves existing subprocess path when disabled

## Secrets Redaction

- Regex patterns in `config.json` `secrets_patterns` (OpenAI keys, GitHub tokens, Slack tokens, AWS keys, private keys)
- `secrets_redactor.redact(text)` applies all patterns, replacing matches with `[REDACTED]`
- Applied on `message_store.get_messages()` read path (tool results and model outputs redacted before feeding back to LLM)
- Applied on every tool result via the audit wrapper in `handle_chat`

## Rate Limiting

- Token-bucket per user, two categories: `llm_calls_per_minute` (default: 10) and `tool_writes_per_minute` (default: 30)
- Configurable via `config.json` `rate_limits` block
- LLM rate checked before processing `chat` and `slash` WS messages
- Write rate (write_to_file, edit_file, execute_command, etc.) checked inside the tool wrapper
- Returns `{"type": "error", "message": "Rate limited: ..."}` on denial

## Audit Log

- SQLite (`agent_audit.db`, WAL mode) with table: `user_id, tool, input_hash, status, created_at`
- Every tool invocation logged via wrapped TOOLS dict in `handle_chat`
- `/api/audit?limit=100&offset=0` endpoint (auth-protected) returns paginated entries
- Inputs are hashed (SHA-256, 16-char prefix) rather than stored raw

---

## Integrations

| Component | Status | Docs |
|-----------|--------|------|
| Kernel | ✅ | `kernel.md` |
| Simulation | ✅ | `simulation_engine.md` |
| ArguGod | ✅ | `debate_engine.md` |
| Digital Twins | Planned | - |

---

## Self-Evolution

Full concept in README.md.

Current: User-reactive → Target: Goal-autonomous
1. Research Loop ✓ implemented (shared agent loop)
2. Hypothesis Generator
3. Validator
4. Compressor
5. Self-Evolve Loop
