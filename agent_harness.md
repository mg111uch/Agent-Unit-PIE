# AI Agent Development Guidelines 

## TASK

In module `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas` , check why in `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/backend/serve.py` interactive graph is served but it only displays loading graph using `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/web/graph_viewer.html` in browser while mermaid graph `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/web/mermaid_view.html` is rendering correctly using same graph data from backend as interactive graph.

Start by knowing module details and current development status by reading `python/Agentic_Unit_PIE/system_devpt_reports/codebase_atlas.md`.

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
- Keep all files in `/system_development_report` under 1000 lines.