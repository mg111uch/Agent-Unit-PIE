# Agent Workflow Details

Supplementary rules and anti-patterns that accompany the graph above.

## 🛠 Tool Selection by Scenario

- **Need full source** — `pie_get_symbol(names=["ClassName", "function_name"], file_path=...)`
- **Unsure of spelling** — `pie_search_symbols(query="...")`
- **See callers/callees** — `pie_get_callers_callees(name="symbol")`
- **Find what breaks on edit** — `pie_find_impact(name="symbol")`
- **Quick metadata (cheap)** — `pie_get_symbols_meta(names=[...])`
- **Compact external-LLM context** — `minimal_context_dump(problem_description="...", symbol_names=[...])` — chains blast radius + symbol source + peripheral API signatures. Prefer over full-file dumps.
- **Single-file paths for kernel** — `glob(pattern="**/kernel/**/*.py", path="<codebase>")`
- **Orientation (file structure)** — `pie_file_api(path=...)` — classes, methods, signatures, no bodies. Prefer over `Read`.
- **Flat file inventory** — `pie_symbols_by_file(path=...)` — every symbol with type, line range, risk. Prefer over `glob` + `grep`.
- **Call path across modules** — `pie_call_chain(start_fn="...", end_module="...")` — shortest BFS path.
- **API diff between files** — `pie_compare_apis(path_a=..., path_b=...)` — only_in_a, only_in_b, signature mismatches.

## 📏 Token-Saving Rules

- Use `get_symbols_meta` before `get_symbol` — avoid fetching full source for low-value symbols.
- Batch `get_symbol` conservatively (2-3 names max per call unless `get_index_info` shows small avg token count).
- Always prefer passing multiple names in one `pie_get_symbol` call over reading whole files line by line.
- Prefer `pie_batch_file_api` when exploring ≥2 files.

## ⛔ Anti-Patterns to Avoid

- **AVOID** `search_symbols` with `top_k > 10` — large result sets waste tokens on irrelevant hits.
- **AVOID** `get_symbol` without checking `get_symbols_meta` first — you may fetch 500+ tokens for a symbol you didn't need.
- **AVOID** Deep recursive `get_callers_callees` beyond depth 2 — call graphs rarely yield new info past that.
- **AVOID** `Read` for kernel files without trying atlas tools first — the whole pipeline exists to avoid this.

## 🔁 Atlas Miss & Sync

- **Miss escalation:** `pie_search_symbols` (fuzzy) → `pie_file_api` (partial index) → `Read` (last resort). Do NOT skip directly to `Read`.
- **Reindex after kernel edits:** `cd codebase/agent_tools/atlas_tools && python run_cmds.py /path/to/project_tools.md "Make Codebase_atlas"`