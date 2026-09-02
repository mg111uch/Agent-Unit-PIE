# PIE Adapter Guide — Integrate Kernel & Simulation into Any Agent

PIE's differentiator is **kernel memory + simulation + debate** — not basic file I/O.
This guide shows how to consume those capabilities from other coding agents
without importing PIE's file tools.

---

## 1. Quick Start: MCP (Recommended)

The fastest integration is via **Model Context Protocol (MCP)**, supported by
Claude Code, Cursor, and many other agent platforms.

### 1.1 Start the MCP server

```bash
# From the PIE codebase directory
cd Agentic_Unit_PIE/codebase
python -m agent_core.mcp_server
```

This exposes 9 tools over stdio:
- `kernel_retrieve`, `kernel_emit_signal`, `kernel_store_context`,
  `kernel_get_memory`, `kernel_create_event`
- `simulation_run`, `simulation_compare`, `simulation_list`, `simulation_get_signals`

### 1.2 Claude Code

```json
// ~/.claude/servers.json or project .claude.json
{
  "mcpServers": {
    "pie-kernel-sim": {
      "command": "python",
      "args": ["-m", "agent_core.mcp_server"],
      "env": {
        "WORKSPACE_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

Claude will see the 9 tools listed above. It keeps its own `Read`, `Edit`, `Write`,
`Bash` tools — it never imports PIE file tools.

### 1.3 Cursor

In Cursor settings → MCP Servers → Add:

```
Name: pie-kernel-sim
Type: stdio
Command: python -m agent_core.mcp_server
```

### 1.4 Any MCP host

```bash
python -m agent_core.mcp_server
# or from another directory:
python /path/to/Agentic_Unit_PIE/codebase/agent_core/mcp_server.py
```

---

## 2. In-Process Python Integration

If your agent is written in Python, register PIE tools directly as callables.

### 2.1 Install

```bash
pip install pie-sdk  # (future — package not yet published)
```

For now, clone the repo and add to `PYTHONPATH`:

```python
import sys
sys.path.insert(0, "/path/to/Agentic_Unit_PIE/codebase")
```

### 2.2 Use the ToolRegistry

```python
from agent_core.tools import registry
from agent_core.tools.registry import CAT_KERNEL, CAT_SIM

# Get only kernel + sim tools (no file ops)
kernel_sim_tools = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])

# Each tool is a callable accepting a single dict/string argument
result = kernel_sim_tools["kernel_retrieve"]({"query": "past decisions", "limit": 10})
print(result.data)
```

### 2.3 Get schemas for native function calling

```python
# OpenAI-style function schemas
schemas = registry.get_schemas()  # default: {"type": "function", "function": {...}}

# Gemini-style
gemini_schemas = registry.get_schemas("gemini")  # [{"function_declarations": [...]}]
```

### 2.4 Add middleware (logging, redaction, rate-limits)

```python
def log_middleware(name: str, fn):
    def wrapped(*args, **kwargs):
        print(f"[PIE] Calling {name}")
        return fn(*args, **kwargs)
    return wrapped

registry.add_middleware(log_middleware)
# Now all tools returned by registry.get_tools() are wrapped.
```

---

## 3. HTTP Tool Gateway

Expose PIE tools as HTTP endpoints for agents that support HTTP tools.

```bash
# Start the FastAPI server
python server.py

# Then call tools
curl http://localhost:8001/api/mcp/tools/kernel_retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "architecture decisions"}'
```

> Note: The HTTP gateway is not yet implemented. Use MCP or in-process for now.

---

## 4. Supplying Host Tools + Disabling PIE File Ops

When using PIE's full server (not MCP), set `AGENT_TOOL_PACKS` to exclude file tools:

```bash
# Only kernel + simulation tools (no file, git, or meta tools)
AGENT_TOOL_PACKS=kernel,sim python server.py
```

Or in `config.json`:

```json
{
  "tool_packs": ["kernel", "sim"]
}
```

The system prompt will automatically exclude file tool descriptions and add
embed-mode guidance telling the model that filesystem is provided by the host.

---

## 5. Prompt Composition (for Host Agents)

If you want to include PIE tool guidance in your own system prompt, compose
from fragments:

```python
from agent_core.prompts import load_system_prompt
from agent_core.tools import registry
from agent_core.tools.registry import CAT_KERNEL, CAT_SIM

# Build prompt for embed mode (no file tools)
tools = registry.get_tools(categories=[CAT_KERNEL, CAT_SIM])
prompt = load_system_prompt(tools_dict=tools, active_packs=["kernel", "sim"])
```

The returned prompt contains:
- Base persona + workspace rules
- Dynamic tool table (only kernel + sim entries)
- Kernel playbook section
- Simulation playbook section
- Embed mode guidance ("Filesystem provided by host")
- Response contract

No file ops sections, no file tool examples, no file-specific workflow rules.

---

## 6. Capability Packages (Planned)

| Package | Content | Status |
|---------|---------|--------|
| `pie.runtime` | AgentSession, event bus, step policies | Planned |
| `pie.kernel` | kernel_ops + memory hooks | ✅ Ready |
| `pie.simulation` | sim_ops | ✅ Ready |
| `pie.argu` | Debate entrypoints | Available as slash cmd |
| `pie.mcp` | MCP server export | ✅ Ready |
| `pie.file` | Optional file_ops + workspace | ✅ Available |

---

## 7. Architecture Summary

```
Your Agent (Claude Code, Cursor, custom)
    │
    ├── MCP ──► pie-kernel-sim (kernel + sim tools only)
    │
    └── In-process ──► ToolRegistry.get_tools(categories=["kernel","sim"])
                         │
                         ├── kernel_retrieve
                         ├── kernel_store_context
                         ├── simulation_run
                         └── ...
```

PIE owns the differentiating tools. You own the filesystem, shell, and editor.
No tool conflict, no prompt bloat.
