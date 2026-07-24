# AI Agent Development Guidelines 

## TASK

During git commit one citations using `Agentic_Unit_PIE/scripts/verify_citations.py` failed with error: FAIL  [grep ] system_devpt_reports/codebase_atlas/status.md:12  modules/codebase_atlas/graph/backend/serve.py:save_positions()

System development reports are given in `Agentic_Unit_PIE/system_devpt_reports`. 

Do not give code or make any changes. Just give a plan or an answer. 

## Kernel Probing Rules (Mandatory)

**Never `Read` a file under `kernel/` — use `pie_file_api` first, always.**

### Preferred tools by scenario

| Scenario | Tool |
|---|---|
| Need full source of a known function/class | `pie_get_symbol(names=["ClassName", "function_name"], file_path=...)` |
| Searching by name when unsure of exact spelling | `pie_search_symbols(query="...")` |
| See what calls / is called by a symbol | `pie_get_callers_callees(name="symbol")` |
| Find what breaks when editing a symbol | `pie_find_impact(name="symbol")` |
| Quick metadata (signature, risk, LOC) for many symbols | `pie_get_symbols_meta(names=[...])` |
| Compact context for an external LLM | `minimal_context_dump(problem_description="...", symbol_names=[...])` — chains blast radius + symbol source + peripheral API signatures into one capped file. **Default choice** over full-file dumps (copyContent.py, code_dump.txt). |
| Single-file paths for kernel files | `glob(pattern="**/kernel/**/*.py", path="<codebase>")` |
| **Orientation — what's in a file?** | `pie_file_api(path=...)` — hierarchical API surface (classes → methods, signatures, docstring first lines). Prefer over `Read` for understanding file structure. |
| **Flat inventory — all symbols in a file** | `pie_symbols_by_file(path=...)` — every symbol with type, line range, risk level. No query needed. Prefer over `glob` + `grep` discovery. |
| **Call path across modules** | `pie_call_chain(start_fn="...", end_module="...")` — shortest BFS path. Prefer over reading 3+ files to trace data flow. |
| **API diff between two files** | `pie_compare_apis(path_a=..., path_b=...)` — shows only_in_a, only_in_b, signature mismatches. Prefer over reading both files to find overlap. |

### Token-saving workflow for code exploration

```
1. CALIBRATE: get_index_info → get real avg function token count, risk distribution
2. ORIENT:     file_api / symbols_by_file for file structure (no bodies)
3. META:       get_symbols_meta(names=[...]) → signatures + token_count, cheap
4. FETCH:      get_symbol(names=[worth_it_1, worth_it_2]) → full source, batched
5. TRACE:      get_callers_callees / find_impact only if coupling matters
```

Use `get_symbols_meta` before `get_symbol` — avoid fetching full source for low-value symbols. Batch `get_symbol` conservatively (2-3 names max per call unless you calibrated otherwise via `get_index_info`).

### Anti-patterns to avoid
- ❌ `search_symbols` with `top_k > 10` — large result sets waste tokens on irrelevant hits
- ❌ `get_symbol` without checking `get_symbols_meta` first — you may fetch 500+ tokens for a symbol you didn't need
- ❌ Deep recursive `get_callers_callees` beyond depth 2 — call graphs rarely yield new info past that
- ❌ `Read` for kernel files without trying atlas tools first — the whole pipeline exists to avoid this

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
- **Agent frontend** `/home/manigupt/Hello/Agentic_Unit_PIE/codebase/frontend`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase && conda run -n myenv python server.py`

## Core principles

- Small scope always
- Strict modularity — Single responsibility, clear interfaces, minimal coupling.
- Ask the user before installing modules and libraries.
- Ask the user before running tests and verifying implementation.
- Smoke tests are allowed. Keep them small.
- Optimize for handling large codebases while maintaining output quality.
- Generate code which is less verbose to save tokens without compromising on functionality.
- Max 400–500 lines per file (including tests & comments).
- One public class/struct/interface per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.
- Keep all files in `/system_development_report` under 1000 lines.

## Dev Report Integrity Rule

Every status claim in `system_devpt_reports/` must include a file path + function/class reference that exists in the current codebase. "✅ Working" without a verifiable anchor gets deleted on sight. Before closing any session, grep each report to confirm every cited function still exists — if it was refactored or deleted, update the report or remove the entry.

### Operating rules

1. **Verify before trusting** — grep for actual call sites before relying on any "✅ Working" claim.
2. **Kernel owns cognition; modules orchestrate** — argu_god (and any future module) calls into kernel; it does not reimplement.
3. **Don't build empty kernel files ahead of a real consumer** — Tier 5 stubs stay empty until a second module genuinely needs them.
4. **One persistence path** — SQLite only now; don't let a future module invent a second.
5. **Every removal needs a reason on record** — already enforced by the project_history topic's `contradicts` edges.

## Tooling Workflow Rules

1. **Use `batch_edit` for repetitive edits across a single file** — Instead of many sequential `edit_file` calls for the same file (e.g., adding the same parameter to every registration), use one `batch_edit` call with all replacements. The tool applies edits sequentially and supports `replace_all` for bulk renames.

2. **Verify directory paths with `list_files` before reading** — When uncertain about a file's location or the directory structure, call `list_files` on the suspected parent directory first. Guessing paths (e.g. `kernel/tools/` when the actual prefix is `agent_core/tools/`) wastes a round trip on a file-not-found error.

3. **Prefer `pie_batch_file_api` when ≥2 files** — batch reduces token overhead vs. serial `pie_file_api` calls.

## system_devpt_reports/ File Convention

- `README.md` = how to use/run the module (user-facing docs)
- `status.md` = current verified capability with citations (agent-facing, verified before every session)
- Prefer `status.md` over `roadmap.md` for determining "what works."
- `roadmap.md` = speculative/planned work, never cited as working

## Report Freshness Rule

1. Every system_devpt_reports/*.md status file (not roadmap files) must carry a `_Last verified: <date>_` line under its title.
2. Before using any status report to decide what to build next, check its Last-verified date against the most recent related code change. If the report predates a change to files it describes, treat it as unverified.
3. Before ending any session that touched code: update the Capability/Gaps section of the relevant status file, append one line to Recent Changes, and bump Last-verified.
4. Status files never contain roadmap/speculative content. If a status file and a roadmap file disagree, the status file wins.
5. Citations (`file.py:function()`) in status files must be checked against the codebase before a session closes.

Status reports are subject to the same verify-before-trusting rule as code — see rule 1 in Operating Rules.

## Report maintenance protocol

### Session start (read path)
- Call `pie_report_freshness`.
- If any status is stale or missing stamp → re-validate before trusting.
- Prefer `status.md` over `roadmap.md` for "what works."

### Session end (write path) — if code changed
- Update only modules you touched.
- For each new/changed public behavior: add/adjust one capability line with citation.
- For removed behavior: delete capability line; if intentional removal, record reason in `project_history` (`contradicts` / why).
- Append one Recent Changes line; trim to 10.
- Bump `_Last verified`.
- Optionally: `python scripts/validate_capabilities.py` (must exit 0 for touched modules).

### Schema enforcement
- Status files without `_Last verified` are treated as empty.
- Capability lines without `file:function()` are deleted on sight (existing Dev Report Integrity Rule).
- Roadmap content found in status → move to roadmap, do not leave dual.

### Empty-file rule
- Empty `status.md` is a defect. Either fill minimal schema within the session that touches the module, or remove the module report directory if the module is abandoned.

### Single writer for automated claims
- Prefer regenerate-from-hypotheses over hand-editing long tables once generator exists. Until then, hand-edit only the thin template.

One-command validation: `python scripts/seed_hypotheses.py && python scripts/validate_capabilities.py`
