# AI Agent Development Guidelines 

## TASK

Suppose I have this project codebase structure:

```
project_dir/
├── subdir1/                         
│   ├── subsubdir1/
│   │   ├── file2.py         
│   │   └── file3.py          
│   └── file4.py  
├── subdir2/                         
│   ├── subsubdir2/
│   │   ├── file5.py         
│   │   └── file6.py          
│   └── file7.py
└── file1.py  
```

I want to render node graph of this project, but as there are so many files in node, rendering whole graph simultaneously and relocating nodes is not possible. What else i could do is render graph of subdirectories one by one, rearrange node as i want and save it. Finally rendering whole codebase becomes easy as it just load saved state of already arranged subdirectories nodes. How could this be achieved with respect to current graph served using `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/backend/serve.py`. Also can we group files nodes in boxes as per the subdirectories are organised in the codebase.

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