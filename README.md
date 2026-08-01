# 🧠 Agent Unit_PIE 

- Name resembles __init__.py

### Universal Unit Pattern Intelligence Engine (PIE) 

- **Human-in-Loop Argument Intelligence System**
- **A filesystem-backed LLM-powered Pattern Intelligence System**
- **A Self-Evolving Intelligence Operating System**

---

##  Under active development. Not ready yet

---

## ⚙️ Setup to Get Started

### Install dependencies
```bash
pip install google-genai python-dotenv
```

### Run Agent
```bash
cd /path/to/Agentic_Unit_PIE
conda activate myenv
AGENT_SKIP_AUTH=true python codebase/server.py
```

#### Environment Variables
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `AGENT_WORKSPACE_ROOT` — override workspace root (default: process CWD)
- `JWT_SECRET` — JWT signing secret (default: auto-generated random hex)
- `CORS_ORIGINS` — comma-separated allowed origins (default: `http://localhost:3000,http://localhost:8001`)
- `AGENT_PORT` — server port (default: 8001)
- `CODEBASE_ATLAS_DIR` — path to atlas output dir with `graphdata.json` (default: `<workspace>/atlas_output/`)

#### Config File (`config.json`)
- `allowed_commands` — list of allowed shell commands for `execute_command`
- `git_tools_enabled` — enable/disable git tools (default: true)
- `enable_checkpoints` — enable/disable checkpoint system (default: true)
- `max_checkpoints` — max checkpoint files to keep (default: 50)
- `agents_md_enabled` — enable/disable AGENTS.md bootstrap (default: true)

---

## 🔮 Core Vision

Agent_Unit_PIE is about **Building Persistent Machine Cognition** that builds **A Recursive World Modeling Infrastructure** which continuously:

```text
observe reality
understanding systems
compress knowledge
finds hidden patterns
extract meaning
modeling reality
simulate future possibilities
generates strategies
optimizes systems
recursively evolve understanding
improves itself
improving civilizations
augmenting human intelligence
```

while maintaining:

* temporal awareness
* causal understanding
* hierarchical memory
* multi-domain reasoning
* adaptive compression
* persistent cognition

across all scales of systems and across every type of unit:

* humans
* codebases
* software projects
* organizations
* companies
* cities
* states
* countries
* markets
* ecosystems
* civilizations
* AI societies
* knowledge systems

The project aims to build persistent evolving world models and digital twins for all kinds of systems.The system transforms raw observations into evolving structured knowledgebases using a signal-centric architecture that scales beyond LLM context limits. The final goal of Agent_Unit_PIE is to create system that continuously:

* ingests information
* organizes knowledge
* extracts signals
* discovers patterns
* models reality
* simulates futures
* generates strategies
* improves itself recursively

---

### OpenCode tool list (Native + MCP-Metatools)

**File / codebase tools**
- `read` / `write` / `edit` — read, write, edit files
- `glob` — find files by pattern
- `grep` — content search with regex
- `pie_file_skeleton` — AST structural map of a file
- `pie_read_section` — read a file section around a regex match
- `pie_file_diff` — show uncommitted changes diff
- `pie_check_path_exists` — check file/dir existence

**Cross-file edit / validation**
- `pie_check_before_edit` — dry-run verify edit targets match
- `pie_cross_file_edit` — apply edits across multiple files in one call
- `pie_undo_last_edit` — restore last checkpoint
- `pie_checkpoint_info` — list available checkpoints

**Code intelligence**
- `pie_who_imports` — module import graph / blast radius
- `pie_get_workspace_info` — workspace root + top-level entries

**Execution / agents**
- `bash` — run terminal commands
- `task` — spawn subagents (explore, general)
- `skill` — load a skill
- `todowrite` — track tasks
- `question` — ask the user questions

**Web**
- `webfetch` — fetch a URL
- `websearch` — real-time web search