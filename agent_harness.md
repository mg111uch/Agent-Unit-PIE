# AI Agent Development Guidelines 

## TASK

I am getting output given in `Agentic_Unit_PIE/Issues_n_ideas.md` while making a llm call to gemini_provider. There are no final answer as output in the frontend. Also tool names are not displayed properly, every tool name is shown `multi`. There are no errors shown in backend terminal while making tool calls to gemini api. I think there is issue in response parsing only.

Start by knowing module details by reading `Agentic_Unit_PIE/system_devpt_reports/orchestrator/README.md`.

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