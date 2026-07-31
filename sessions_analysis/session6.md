## Gap Analysis — Tools That Do NOT Exist Yet

Based on the current 55-tool inventory, here are the most notable gaps, organized by potential new category or enhancement:

### 1. Project / Dependency Management (missing category: `CAT_PROJECT` or `CAT_DEP`)
- **`list_dependencies`** / **`check_dependency`** — Inspect `requirements.txt`, `pyproject.toml`, `package.json`, etc. to list installed / declared dependencies and detect conflicts.
- **`find_imports`** — Find all import/require statements in a file (complementary to `get_callers_callees` but at module level, not just symbol level).
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

### 10. Analytics / Tracking Enhancements
- **`session_summary`** — Summarize the current session (tools called, files changed, time elapsed) — a lightweight version of the observer logging.

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
| **`file_diff`** | `CAT_FILE` | Show lines changed since last `edit_file`/`write_to_file` checkpoint on a file. Unlike `git_diff` (git-tracked changes), this works on any file regardless of git. After making 3 edits to a file, the agent calls `file_diff` and gets 5 changed lines instead of re-reading 300 lines. | **40x** (~8k → ~200 tokens per verification) |
| **`context_budget`** | `CAT_OBSERVER` | Return current session's estimated token consumption: total tokens read, per-file read costs, per-edit costs, tokens in message history, estimated remaining budget. Unlike `user_reading_budget` (tracks human reading), this tracks the **agent's own context usage** so it can self-regulate. | **Prevents entire drift sessions** (unbounded) |
| **`plan_validate`** | `CAT_META` | Before executing a multi-edit plan, validate that all target files exist and all `old_string` edit patterns match exactly once. Returns success/failure per edit with nearby context for mismatches. Unlike `check_path_exists` (file existence only), this validates the actual edit targets. | **2-5x** on edit-heavy tasks (prevents fail-recover cycles) |
| **`compact_history`** | `CAT_META` | Compress the agent's conversation history (`step_state.current_messages`) into a compact summary preserving: goal, files touched, decisions made, pending work. The agent calls this mid-session when context feels bloated. Unlike `compact_messages` (internal session_state function, not a callable tool), this is an explicit tool the agent controls. | **~10x** (50k → 5k tokens for subsequent LLM calls) |

### Novel hooks (no tool call needed, fire automatically)

| Hook | Location | What it does | Tokens saved |
|---|---|---|---|
| **`read_file` auto-cache** | `file_ops.py:read_file` | Store `(path, mtime, content_hash, line_count)` in session state. On repeat reads of the same unchanged file, return `"(cached: 544 lines, unchanged since earlier read)"` instead of re-reading from disk. Agent can still force a fresh read with `force=True`. | **3x** per repeat-read (prevents the "re-read 6 cached files" pattern that started the drift) |
| **Edit pre-validation** | `file_ops.py:edit_file` | Before applying, check `old_string` exists exactly once. If zero matches, scan nearby for fuzzy matches and return a clear error with suggestions. If multiple matches, list them. Catches the stale-plan problem in the tool itself instead of requiring an LLM cycle to diagnose. | **1 full LLM cycle** per failed edit |

---

### Comparison with existing tools (why these are novel)

| Existing tool | Why it doesn't solve the problem | Novel replacement |
|---|---|---|
| `git_diff` | Only shows **uncommitted git changes**, not edits from the current session. If a file was edited via `edit_file` 2 turns ago, `git_diff` shows nothing new. | `file_diff` — tracks all changes regardless of git. |
| `read_section` | Requires a regex pattern. Doesn't help when you don't know the exact pattern, or when you want to verify what changed without specifying what to look for. | `file_diff` — shows what *actually* changed. |
| `user_reading_budget` | Tracks **human reading time**, not LLM context tokens. Says "you've read 30 min today" not "you've consumed 60k tokens this session." | `context_budget` — tracks agent's own token consumption. |
| `check_path_exists` | Returns `true/false` only. Doesn't validate edit patterns. | `plan_validate` — validates `old_string` targets before the first edit call. |
| `batch_edit` | Applies multiple edits in one call, but doesn't validate them beforehand. A failing edit still wastes the whole batch. | `plan_validate` + `batch_edit` — validate then execute. |
| `compact_messages` (internal) | Internal function, not a tool. Agent cannot call it. Runs automatically based on `COMPACTION_TRIGGER_CHARS`, not on demand. | `compact_history` — agent-controlled, on-demand compression. |
| `undo_last_edit` | Reverts an edit. Doesn't show what changed. | `file_diff` — shows what changed without reverting. |

### Cross-Session / Cross-Agent Optimization

| Tool/Hook | What it does | Why it helps future agents |
|---|---|---|
| **`session_history`** (new tool under CAT_META) | Return summary of last session: files edited, decisions made, blockers. Returns `"Last session: edited 3 files (index.html, AgentChat.js, style.css) to add markdown rendering. No blockers."` | Lets a new agent pick up where the previous one left off without re-exploring. Complements `kernel_retrieve` (which is semantic memory) with a concrete session log. |
| **`read_file` cache in session_state** | Store `(path, mtime, hash, line_count)` on first read; skip re-read on subsequent calls if file unchanged | Prevents the "re-read 6 already-cached files" pattern that started the drift. **This is the single most impactful fix for drift** — it removes the agent's incentive to re-read. |
| **`file_diff` tool** | Show diff between last edit checkpoint and current state | After editing, agent calls `file_diff` instead of re-reading the whole file. Saves tokens and removes the incentive to "verify by re-reading." |

---

### Summary

The single highest-leverage change is the **`read_file` auto-cache hook** — it would have prevented the drifting agent from re-reading 6 unchanged files (step 1 of the drift). The second is **`file_diff`** — it replaces full-file re-reads with minimal diffs, saving ~8k tokens per verification.

======================================

