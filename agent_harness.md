# AI Agent Development Guidelines 

## TASK

Check `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/web/core/storage.js` whether the custom node positions are stored in browser local storage. Node positions are also stored in json file using post method on `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/backend/serve.py`. Why do we need duplicate storage of node positions.Could we removel browser local storage altogether so that node positions are only stored in json files.

Start by knowing module details and current development status by reading `python/Agentic_Unit_PIE/system_devpt_reports/codebase_atlas/current_status.md`.

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