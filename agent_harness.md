# AI Agent Development Guidelines 

## TASK

For population simulation, old non behaviour based hard coded simulation agents is given in `python/Agentic_Unit_PIE/codebase/modules/simulators/popula_dyn/old_str`. Suggest how this could be modified to behaviour based unit_agents given in `python/Agentic_Unit_PIE/codebase/modules/simulators/popula_dyn/core`.

Start by reading `README.md` and `code_atlas.md` in project root to understand the project first.

Do not give code or make any changes, just a concise plan or answer.

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/python/Agentic_Unit_PIE`
- **Source_code:** (Working directory) `/home/manigupt/Hello/python/Agentic_Unit_PIE/codebase`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/python/Agentic_Unit_PIE/codebase && conda run -n myenv python agent.py`

## Core principles

- **Small scope always** 
- **Strict modularity** — Single responsibility, clear interfaces, minimal coupling.
- **Test-first mindset** — Tests are the safety net for AI-generated code.
- **Human-in-the-loop** — Agent proposes → you review → apply → test → commit.
- Optimize for handling large codebases while maintaining output quality.

## File & Module Size Rules

- Max **400–500 lines** per file (including tests & comments).
- **One public class/struct/interface** per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.