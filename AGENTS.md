# AI Agent Development Guidelines 

## TASK

Read `Agentic_Unit_PIE/system_devpt_reports/kernel_core/improvement.md` for kernal improvement plan. Check if `Free-text redesign` has been implemented and give plan for pending.

Start by knowing system details by reading `Agentic_Unit_PIE/system_devpt_reports/kernel_core/kernel.md`. 

Do not give code or make any changes, just a concise plan or answer.

## Kernel Probing Rules (Mandatory)

Use code_rag MCP tools (`pie_*` tools) to probe kernel files — never `Read` them directly. Only exceptions where `Read` is allowed:
- Empty/stub files (0 LOC, no indexed symbols) — `Read` is fine since there's nothing in code atlas.
- Argu_god module files (not indexed in code atlas) — use `Read`.
- Files under `system_devpt_reports/` — use `Read`.

### Preferred tools by scenario

| Scenario | Tool |
|---|---|
| Need full source of a known function/class | `pie_get_symbol(names=["ClassName", "function_name"], file_path=...)` |
| Searching by name when unsure of exact spelling | `pie_search_symbols(query="...")` |
| See what calls / is called by a symbol | `pie_get_callers_callees(name="symbol")` |
| Find what breaks when editing a symbol | `pie_find_impact(name="symbol")` |
| Quick metadata (signature, risk, LOC) for many symbols | `pie_get_symbols_meta(names=[...])` |
| Single-file paths for kernel files | `glob(pattern="**/kernel/**/*.py", path="<codebase>")` |
| **Orientation — what's in a file?** | `pie_file_api(path=...)` — hierarchical API surface (classes → methods, signatures, docstring first lines). Prefer over `Read` for understanding file structure. |
| **Flat inventory — all symbols in a file** | `pie_symbols_by_file(path=...)` — every symbol with type, line range, risk level. No query needed. Prefer over `glob` + `grep` discovery. |
| **Call path across modules** | `pie_call_chain(start_fn="...", end_module="...")` — shortest BFS path. Prefer over reading 3+ files to trace data flow. |
| **API diff between two files** | `pie_compare_apis(path_a=..., path_b=...)` — shows only_in_a, only_in_b, signature mismatches. Prefer over reading both files to find overlap. |

Batch lookups with `pie_get_symbol` — prefer passing multiple names in one call over reading whole files line by line.

**Avoid `Read` for kernel files** — use `pie_file_api` / `pie_symbols_by_file` for orientation, then `pie_get_symbol` for specific functions. Raw `Read` is only for stub files, argu_god modules, and files under `system_devpt_reports/`.

### Handling atlas misses

When `pie_symbols_by_file` or `pie_file_api` return empty results (atlas miss), the correct escalation is:

1. Try `pie_search_symbols(query="<likely_name>")` with a fuzzy/partial query
2. If that also fails, try `pie_file_api(path=...)` (may have partial indexing even if symbols table missed)
3. **Only then** fall back to `Read` — and note the miss as a bug to fix via reindexing

Do NOT skip directly to `Read` just because the atlas returned empty.

### Keeping the atlas in sync after edits

After editing/creating/deleting any kernel files, the `code_rag.db` atlas becomes stale. Regenerate it:

```bash
# From codebase root:
conda run -n myenv python -m codebase_atlas.main \
  --project-dir /home/manigupt/Hello/Agentic_Unit_PIE/codebase \
  --output-dir /home/manigupt/Hello/Agentic_Unit_PIE/atlas_output
```

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

## Dev Report Integrity Rule

Every status claim in `system_devpt_reports/` must include a file path + function/class reference that exists in the current codebase. "✅ Working" without a verifiable anchor gets deleted on sight. Before closing any session, grep each report to confirm every cited function still exists — if it was refactored or deleted, update the report or remove the entry.

### Operating rules

1. **Verify before trusting** — grep for actual call sites before relying on any "✅ Working" claim.
2. **Kernel owns cognition; modules orchestrate** — argu_god (and any future module) calls into kernel; it does not reimplement.
3. **Don't build empty kernel files ahead of a real consumer** — Tier 5 stubs stay empty until a second module genuinely needs them.
4. **One persistence path** — SQLite only now; don't let a future module invent a second.
5. **Every removal needs a reason on record** — already enforced by the project_history topic's `contradicts` edges.

## File & Module Size Rules

- Max 400–500 lines per file (including tests & comments).
- One public class/struct/interface per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.
- Keep all files in `/system_development_report` under 1000 lines.

