## Project Paths
- **WORKSPACE_ROOT:**  `/home/manigupt/Hello/Agentic_Unit_PIE`
- **Codebase atlas:** `/home/manigupt/Hello/Agentic_Unit_PIE/atlas_output`
- **CODEBASE_ROOT:** `/home/manigupt/Hello/Agentic_Unit_PIE/codebase` (project source code, inside workspace root)
- **Agent frontend** `/home/manigupt/Hello/Agentic_Unit_PIE/codebase/frontend`

## Code Execution & Validation Environment
- **Command to run project:** `cd /home/manigupt/Hello/Agentic_Unit_PIE && conda run -n myenv AGENT_SKIP_AUTH=true python codebase/server.py`

## Regenerate the stale `code_rag.db` codeatlas:
```bash
cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && python run_cmds.py /home/manigupt/Hello/Agentic_Unit_PIE/project_tools.md "Make Codebase_atlas"
```

## Core principles
- All project packages are installed in conda envt. Always use it `conda run -n myenv`
- Small scope always.
- Do not use any git commands.
- Strict modularity — Single responsibility, clear interfaces, minimal coupling.
- Ask the user before installing modules and libraries.
- No frontend tests, no playwright tests.
- Smoke tests are allowed. Keep them small.
- Optimize for handling large codebases while maintaining output quality.
- Generate code which is less verbose to save tokens without compromising on functionality.
- Max 400–500 lines per file (including tests & comments).
- Split large files when they exceed 500 LOC.
- **One persistence path** — SQLite only now; don't let a future module invent a second.



