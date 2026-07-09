# AI Agent Development Guidelines 

## TASK

I have build a agent `/home/manigupt/Hello/Agentic_Unit_PIE/codebase/agent.py`. I want to improve its coding finctionalities by making it a proper agent like claudecode codex or opencode. I dont want to build a terminal based ui, nor a desktop app nor a vscode extension. I am planning to make it browser based. Can it work. What issues i would face. Should i use plain html js or use a framework with ts. Can all finctionalities of a standard coding agent be covered on a browser. 

Start by knowing module details by reading `python/Agentic_Unit_PIE/system_devpt_reports/orchestrator.md`.

Do not give code or make any changes, just a concise plan or answer.

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/Agentic_Unit_PIE`
- **Source_code:** (Working directory) `/home/manigupt/Hello/Agentic_Unit_PIE/codebase`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase && conda run -n myenv python agent.py`

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