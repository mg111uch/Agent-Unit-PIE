# AI Agent Development Guidelines 

## TASK

Currently agent only use gemini api for llm, i also want to integrate openrouter api so that user can select when to use use which provider. Also how `python/Agentic_Unit_PIE/codebase/llm/llm_orchestrator.py` can be ontegrated to main agent loop. Also current agent writes every terminal output to tui_output.txt file, instead i want it to write last terminal output with error only when user enters a command in agent ternimal. How can this be achieved.

Start by knowing module details by reading `python/Agentic_Unit_PIE/system_devpt_reports/orchestrator.md`.

Do not give code or make any changes, just a concise plan or answer.

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/python/Agentic_Unit_PIE`
- **Source_code:** (Working directory) `/home/manigupt/Hello/python/Agentic_Unit_PIE/codebase`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase && conda run -n myenv python agent.py`

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