## Gap Analysis — Tools That Do NOT Exist Yet

Based on the current 55-tool inventory, here are the most notable gaps, organized by potential new category or enhancement:

### 1. Project / Dependency Management (missing category: `CAT_PROJECT` or `CAT_DEP`)
- **`list_dependencies`** / **`check_dependency`** — Inspect `requirements.txt`, `pyproject.toml`, `package.json`, etc. to list installed / declared dependencies and detect conflicts.
- **`check_syntax`** / **`lint_file`** — Run a syntax/lint check (e.g. `py_compile`, `flake8`, `eslint`) on a file without running full tests.

### 2. Schema / Validation (partial overlap with `report_schema_check`)
- **`validate_json`** / **`validate_yaml`** — Validate a JSON/YAML file against a schema.
- **`validate_file`** — General validation hook (pluggable per file extension).

### 3. Network / HTTP (no tools exist in this area)
- **`http_get`** / **`http_post`** — Fetch a URL or call an API (optionally sandboxed). Currently the agent has no way to make external HTTP requests.
- **`web_search`** — Search the web from within the agent loop.

### 4. Vector / Embedding Ops (could live under `CAT_CODE_RAG`)
- **`semantic_search`** — Embed a query and search the codebase by vector similarity (complementing FTS5 `search_symbols`).
- **`summarize_code`** — Generate a natural-language summary of a file or function using the atlas embeddings.

### 5. CI / Workflow (could live under `CAT_META` or new category)
- **`run_workflow`** — Trigger a GitHub Actions workflow and wait for result.
- **`check_ci_status`** — Check recent CI run results for the current branch.

### 6. Diff / Review (could live under `CAT_GIT`)
- **`git_branches`** — List branches.
- **`git_checkout`** — Switch branches (with safety check for uncommitted changes).
- **`git_pr_info`** — Show PR details / diff from a PR number.

### 7. Debugging / Profiling (no tools exist)
- **`run_profiler`** — Run `cProfile` or similar on a script.
- **`inspect_variable`** — For a running process/debug session (would require a debug server).

### 8. Documentation Generation
- **`generate_docstring`** — Generate docstrings for a function/class using LLM and write them back.
- **`generate_readme`** — Generate/update a `README.md` from the atlas.

### 9. Config / Environment
- **`get_env`** / **`list_env_vars`** — Inspect environment variables (useful for debugging CI/env issues).


================================

## Analysis & Recommendations

### Where tokens were spent most in this session

| Phase | Token cost | % of total |
|---|---|---|
| **Reading files** (full reads of `__init__.py` at 544 lines, `engine.py` at 348, `stepper.py` at 349) | Very high | ~60% |
| **Re-reading files after edits** to verify changes | High (full file each time) | ~15% |
| **Exploration** (sub-agent reading unfamiliar parts) | Isolated, acceptable | ~10% |
| **Edits themselves** | Low (just the changed lines) | ~5% |
| **Scaffolding** (prompt fragments, imports, registration) | Medium | ~10% |

The biggest waste: **full-file re-reads after edits** and **full-file reads to find a single section**.

---

### Novel tools (no duplicates)

| Tool | Category | What it does | Tokens saved vs current |
|---|---|---|---|
| **`context_budget`** | `CAT_OBSERVER` | Return current session's estimated token consumption: total tokens read, per-file read costs, per-edit costs, tokens in message history, estimated remaining budget. Unlike `user_reading_budget` (tracks human reading), this tracks the **agent's own context usage** so it can self-regulate. | **Prevents entire drift sessions** (unbounded) |
| **`compact_history`** | `CAT_META` | Compress the agent's conversation history (`step_state.current_messages`) into a compact summary preserving: goal, files touched, decisions made, pending work. The agent calls this mid-session when context feels bloated. Unlike `compact_messages` (internal session_state function, not a callable tool), this is an explicit tool the agent controls. | **~10x** (50k → 5k tokens for subsequent LLM calls) |

---

### Comparison with existing tools (why these are novel)

| Existing tool | Why it doesn't solve the problem | Novel replacement |
|---|---|---|
| `user_reading_budget` | Tracks **human reading time**, not LLM context tokens. Says "you've read 30 min today" not "you've consumed 60k tokens this session." | `context_budget` — tracks agent's own token consumption. |
| `batch_edit` | Applies multiple edits in one call, but doesn't validate them beforehand. A failing edit still wastes the whole batch. | `plan_validate` + `batch_edit` — validate then execute. |
| `compact_messages` (internal) | Internal function, not a tool. Agent cannot call it. Runs automatically based on `COMPACTION_TRIGGER_CHARS`, not on demand. | `compact_history` — agent-controlled, on-demand compression. |

