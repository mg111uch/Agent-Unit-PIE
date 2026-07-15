# AI Agent Development Guidelines 

## TASK

There is much detail given in `Agentic_Unit_PIE/system_devpt_reports/orchestrator/README.md` which the end user dont need to know about. This doc is for humans to get usage details and overview of how project work. But many features documented gives unnecessary details which humans dont need to concern with  and agents can easily get it by reading code files directly. Should we keep details as it is or should we clean up a bit.   

Start by knowing module details by reading `Agentic_Unit_PIE/system_devpt_reports/orchestrator/README.md`. Keep updating it.

Do not give code or make any changes, just a concise plan or answer.

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/Agentic_Unit_PIE`
- **Source_code:** (Working directory) `/home/manigupt/Hello/Agentic_Unit_PIE/codebase`
- **Agent frontend** `/home/manigupt/Hello/reddit-clone/frontend/app/agent/page.tsx`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase && conda run -n myenv python server.py`

## Core principles

- Small scope always
- Strict modularity — Single responsibility, clear interfaces, minimal coupling.
- Ask the user before installing modules and libraries.
- Ask the user before running tests and verifying implementation.
- Smoke tests are allowed. Keep them small.
- Optimize for handling large codebases while maintaining output quality.

## File & Module Size Rules

- Max 400–500 lines per file (including tests & comments).
- One public class/struct/interface per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.
- Keep all files in `/system_development_report` under 1000 lines.

## Session Findings

Add useful project-specific findings here for later sessions. Be precise — one-liners preferred.

### 2026-07-13 — Phase 4: server.py / agent_loop.py split into packages
- `codebase/__init__.py` causes circular import on `pytest` — workaround: `mv __init__.py __init__.py.bak` before running tests, restore after
- Splitting a module with mutable globals into a package: import via `import pkg as _srv` and reference `_srv.global_name` for reads/writes; `from pkg import name` creates local bindings that won't see mutations by other submodules

### 2026-07-15 — Code RAG: SQLite-based symbol search from atlas output
- `agent_core/tools/code_rag.py` — `CodeRAG` class ingests atlas `graphdata.json` + `ast`-parsed function/class code into SQLite with FTS5. Zero external deps (stdlib only).
- 4 agent tools registered under `CAT_META`: `get_symbol`, `search_symbols`, `get_callers_callees`, `find_impact`
- Tool functions must be plain (no `@tool_call`) in ops module to avoid circular import; decorator applied in `__init__.py` registration.