# AI Agent Development Guidelines 

## TASK

Check why in module `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas` , the serve.py file is not moving the connected edges of the nodes as the nodes are being dragged to relocate by the user.

Start by knowing module details by reading `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/README.md`.

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
- Keep all files in `/system_development_report` under 500 lines.