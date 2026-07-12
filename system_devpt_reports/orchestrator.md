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
Goal-autonomous research without manual iteration.

```
/auto "research question"
```

**Examples:**
```
>> /auto Why is population declining?
>> /auto Compare healer vs no-healer scenarios
```

**Output:** Findings stored to kernel memory.

---

## Tools

### File Operations
| Tool | Purpose |
|------|---------|
| `read_file` | Read file (returns line-numbered output; lists nearby files on error) |
| `list_files` | List directory (recursive, depth-capped, skips noise dirs) |
| `write_to_file` | Write file (create/overwrite/append/patch modes) |
| `edit_file` | Targeted replacement (unique old_string → new_string; rejects 0/>1 matches) |
| `get_workspace_info` | Ground-truth: root path + top-level entries |
| `execute_command` | Run shell |

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

## LLM Orchestration

### Architecture

```
agent.py / server.py
        │
        ▼
   agent_core/
     ├── agent_loop     ──► tools + parse + steps + failure breaker
     ├── workspace      ──► single path resolver (used by all file tools + server APIs)
     ├── providers_setup ──► agent_core.llm.*
     ├── context, prompts, commands, auto_research
     └── llm/ (orchestrator + providers)
```

### Path Resolution (workspace.py)

All file tools (`read_file`, `list_files`, `write_to_file`, `edit_file`) and the server's
`/api/files/*` endpoints resolve paths through `agent_core.workspace.resolve()`. This ensures
the agent and frontend always agree on the root. The root defaults to process CWD and is
overridable via the `AGENT_WORKSPACE_ROOT` environment variable.

Leading slashes in model-supplied paths are treated as workspace-relative (not OS-root), matching
the convention most coding agents expect. A `PathEscapeError` is raised if `..` traversal or
symlinks attempt to escape the workspace.

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
1. Research Loop ✓ implemented
2. Hypothesis Generator
3. Validator
4. Compressor
5. Self-Evolve Loop