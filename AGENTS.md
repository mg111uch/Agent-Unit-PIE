# AI Agent Development Guidelines 

## TASK

I have a code RAG tool system where an LLM agent can call `get_symbol(names=["func1", "func2"])` to batch-lookup function definitions. The schema exposes only `names` (required array of strings) + optional `file_path`. Despite this:

Schema shows `names` as the only parameter (required array).
Prompt fragment has explicit rule: "After search_symbols returns multiple results, call get_symbol once with names: ['func1', 'func2', ...] instead of individual calls."
Executor merges parallel get_symbol calls server-side.

The LLM still calls get_symbol sequentially — one name at a time — even when search_symbols returned multiple results. It uses names: ["func1"] (single-element array) and repeats N times.

The executor merge only catches parallel calls sent in the same turn. But the LLM generates them sequentially (one per turn) — so the merge never fires. The prompt fragment instruction seems insufficient.

Why does the LLM still not batch? Diagnose the root cause and propose a solution that actually works. Consider:
1. Is the prompt fragment being loaded correctly? Check prompts.py assembly logic.
2. Do native function-calling schemas have issues with array-type required params on Gemini/OpenRouter?
3. Does the system prompt's tool description approach or the response contract inadvertently encourage single calls?
4. Would a different approach (e.g., interceptor that accumulates pending get_symbol calls for a short window, then flushes as batch) be more robust?
5. Should we give up on LLM-side batching and instead always batch on the server side — i.e., make get_symbol_tool accept both name and names, and in executor.py, hold all get_symbol calls across a turn, merge names, execute once, and fan out the merged result to all call_ids?

Provide the best concrete fix with implementation details.

LLM chat is given in `Agentic_Unit_PIE/Issues_n_ideas.md`.

Start by knowing module details by reading `Agentic_Unit_PIE/system_devpt_reports/orchestrator/README.md`. Keep updating it.

Do not give code or make any changes, just a concise plan or answer.

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/Agentic_Unit_PIE`
- **Codebase atlas:** `/home/manigupt/Hello/Agentic_Unit_PIE/atlas_output`
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

### 2026-07-16 — Code RAG: get_symbol-first (no search prefetch)
- Named lookups: agent should call `get_symbol(names=[...])` first; `search_symbols` only on `missing_names` / unknown names
- Removed `prefetched_symbols` + `batch_get_symbol_hint` from `search_symbols` (bulk-prefetching unrelated FTS hits)
- `get_symbol_tool` returns `missing_names` + hint when some names fail
- Workflow in `prompt_fragments/25_code_rag.md`; plan in project-root `get_symbol_batching_plan.md`

### 2026-07-16 — Code RAG: batch get_symbol + auto-budget for tool results
- `executor.py` result truncation raised 500→10000 chars to stop mid-function cuts
- `code_rag.py`: `get_symbols(names, file_path)` + `BUDGET_CHARS=10000` auto-batching in `get_symbol_tool`

### 2026-07-15 — Code RAG: SQLite-based symbol search from atlas output
- `agent_core/tools/code_rag.py` — `CodeRAG` class ingests atlas `graphdata.json` + `ast`-parsed function/class code into SQLite with FTS5. Zero external deps (stdlib only).
- 4 agent tools registered under `CAT_META`: `get_symbol`, `search_symbols`, `get_callers_callees`, `find_impact`
- Tool functions must be plain (no `@tool_call`) in ops module to avoid circular import; decorator applied in `__init__.py` registration.