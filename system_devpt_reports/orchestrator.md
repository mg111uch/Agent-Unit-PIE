# Agent Orchestrator Reference

Single reference for project usage.

---

## Getting Started

### Run Agent
```bash
cd codebase
conda run -n myenv python agent.py --provider gemini --model gemini-3.1-flash-lite
conda run -n myenv python agent.py --provider openrouter --model openai/gpt-oss-20b:free
```

#### OpenRouter provider Models
- google/gemma-4-26b-a4b-it:free
- google/gemma-4-31b-it:free
- openai/gpt-oss-120b:free
- openai/gpt-oss-20b:free
- nvidia/nemotron-3-ultra-550b-a55b:free
- nvidia/nemotron-3-super-120b-a12b:free
- nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
- nvidia/nemotron-3-nano-30b-a3b:free

#### Google provider Models
- gemini-3.5-flash
- gemini-3.1-pro-preview
- gemini-3.1-flash-lite
- gemini-3.1-flash-lite-image
- gemma-4-31b-it
- gemma-4-26b-a4b-it

#### Environment Variables
- `GEMINI_API_KEY` — required for `--provider gemini`
- `OPENROUTER_API_KEY` — required for `--provider openrouter`

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
| `read_file` | Read file |
| `list_files` | List directory |
| `write_to_file` | Write file |
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
agent.py
  │
  ├── orchestrator.generate(provider, model, conversation_id, ...)
  │     │
  │     ├── gemini_provider.generate()
  │     │     └── genai.Client.interactions.create(previous_interaction_id=conversation_id)
  │     │         ↳ stateful — conversation_id carries turn history server-side
  │     │
  │     └── openrouter_provider.generate()
  │           └── openai.OpenAI(base_url="https://openrouter.ai/api/v1")
  │               .chat.completions.create(messages=[...])
  │               ↳ stateless — conversation_id ignored
  │
  └── result["response"] ──► agent loop
```

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