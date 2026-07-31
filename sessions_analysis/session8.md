## Session retro: where tokens went & what would have helped

Evidence from this session (4 merge/rename tasks: batch tools, todo, kernel-warning removal, tool-mode design):

**The #1 token hotspot was cross-file tool tracing.** For each task I re-traced the same tool through ~9 files by hand: `__init__.py` (registration) → impl (`meta_ops.py`/`file_ops.py`) → `stepper.py` → `session_state.py` → `audit.py` → `mock_provider.py` → tests → prompt fragments → `mcp_server.py`. I did this ~4× (batch, todo, kernel, mode). That's an estimated 60–70% of session tokens.

**#2: whole-file reads for small slices.** `file_ops.py` (627 lines) read 3+ times; `registry.py`, `stepper.py`, `session_state.py` similar. The existing **codebase atlas** (`get_symbol`, `symbols_by_file`, `file_api`, `batch_file_api`, `call_chain`, `find_impact`, `minimal_context_dump`) would have turned these into single-function fetches — but the `code_rag` pack is **off** in config.json and the atlas DB is **4 days stale** (Jul 27), so it wasn't available. That's the single biggest lever, already built.

---

## Recommendations (each checked against existing tools — no duplicates)

### 1. `tool_anatomy` — NEW tool (highest value, nothing like it exists)
Deterministic repo-scan, one call replaces the #1 hotspot:
- registration `file:line` + category + `mcp_expose` + schema params
- implementation function `file:line`
- every reference: prompt fragments, mock scenarios, tests, `stepper._EDIT_TOOLS`, `audit._WRITE_TOOLS`, `session_state` observers, MCP exposure
- optional "history" line (e.g. "merged from batch_edit → edit_file(edits), 2026-07-31")

Not a duplicate: the atlas indexes *symbols in source*; `report_inventory` scans `system_devpt_reports`; `list_capabilities` is the hypothesis engine; `hot_reload` reloads modules. This was proposed as `trace_registration` in session1.md but never built.

###  DUPLICATE from session2 - `tool_inventory` — list registered tools grouped by category

Would have saved reading `__init__.py` multiple times just to answer questions like:
- "Is `check_path_exists` under CAT_FILE or CAT_META?"
- "Which tools are registered in CAT_DEBATE?"
- "What file does `batch_edit_tool` live in?"

**Example output:**

```
CAT_FILE:
  read_file              → file_ops.py:57
  list_files             → file_ops.py:106
  write_to_file          → file_ops.py:157
  edit_file              → file_ops.py:233
  execute_command        → __init__.py:149
  glob_search            → file_ops.py:332
  grep_search            → file_ops.py:347
  todo_write             → file_ops.py:25
  todo_read              → file_ops.py:63
  ask_user_question      → question_ops.py

CAT_META:
  check_path_exists      → meta_ops.py
  get_workspace_info     → meta_ops.py
  batch_read             → meta_ops.py
  read_section           → meta_ops.py
  batch_edit             → meta_ops.py
  run_tests              → test_ops.py
  undo_last_edit         → undo_ops.py
  checkpoint_info        → undo_ops.py
  extract_symbols_to_file → code_rag.py
```

**Novelty check:** No existing tool does this. `grep_search` finds raw registration lines but doesn't group/categorize. `get_symbol` only works on atlas-indexed code (not registered tools). `get_workspace_info` shows file layout, not tool-to-category mapping.

**Implementation:** Uses the already-populated `registry.meta_dict` and `registry._categories` — just formats them. ~40 lines.

---

### 2. Activate the existing atlas — NO new code, just config + regen
Enable `code_rag: true` in tool_packs and regenerate the atlas (`run_cmds.py … "Make Codebase_atlas"`). This single change converts most whole-file reads into `get_symbol`/`batch_file_api` calls — the exact fix for pattern #2. I'd argue this plus #1 gives ~70% of the total win.

---

### 3. `worklog` post-chat hook + `session_handoff` pre-chat hook — NEW hooks
- **Post-chat:** write a structured delta to sqlite (one persistence path per AGENTS.md): files touched (path + mtime + 1-line diff summary), tools added/merged/renamed, decisions, pending TODOs.
- **Pre-chat:** inject ≤300 tokens at session start — "Last session changed {files}→{summary}; watch {files}; pending {todo}."
This directly answers "next agent accessing the same files should be faster." It complements `kernel_retrieve` (semantic embedding memory) and `session_state` (in-memory, resets each turn) — neither gives a structured delta. Related to session6.md's `session_history` proposal, but harness-side so it happens without the LLM asking.

### DUPLICATE from session1 - `session_diff` — **Low-medium impact**
**What it does:** Show a structured diff of what was changed in this session: files modified, new functions added, registration changes. Useful when resuming a session after a context reset or when the agent needs to verify its own work without re-reading every modified file.
**Not a duplicate of:** `git_diff` (shows line-level diff, no semantic understanding; also requires git commits which may not happen mid-session). This would show semantic change summaries (e.g., "Moved check_path_exists from CAT_META to CAT_FILE").

#### DUPLICATE from session4 -  `session_map` — Working set tracker
Tracks which files were read/edited in the current session and their relevant context. A compact session memory so you don't re-discover the same files.
```
session_map()
  → Files accessed:
      engine.py        (read 4×, edited: lines 150-152, 197, 249-275)
      stepper.py       (created, 353 lines)
      file_ops.py      (read 2×, edited: lines 380-392, 423-424)
      config.py        (read 1×, edited: line 82)
      ...
  → Last edit context: schema caching → moved get_schemas outside loop
```
**vs existing tools:**
- `get_workspace_info` — shows workspace root, file cache, but not session-specific access history
- `todo_write` — tracks task plans, not file access history
- Session `dir_cache` — caches directory listings, not file read/edit history
**Novelty:** Cross-file session-aware context that persists across turns. Currently the agent re-discovers file structures every turn.

#### DUPLICATE from session5 -  `changeprint`**
After a session's edits, produce a compact relational summary: which files changed, what kind of changes (new function, refactored block, deleted code), and a before/after token count. Useful for both the current agent and any future agent picking up the work.
*Not duplicate of `git diff`* — git diff shows raw lines; this shows semantic intent and token impact.

#### DUPLICATE from session6 - Analytics / Tracking Enhancements
- **`session_summary`** — Summarize the current session (tools called, files changed, time elapsed) — a lightweight version of the observer logging.

#### DUPLICATE from session6 -
| Tool/Hook | What it does | Why it helps future agents |
|---|---|---|
| **`session_history`** (new tool under CAT_META) | Return summary of last session: files edited, decisions made, blockers. Returns `"Last session: edited 3 files (index.html, AgentChat.js, style.css) to add markdown rendering. No blockers."` | Lets a new agent pick up where the previous one left off without re-exploring. Complements `kernel_retrieve` (which is semantic memory) with a concrete session log. |

#### DUPLICATE from implement_fix -
`pie_session_summary()`- Output a compact summary of all edit, read, and grep operations in the
      current session, grouped by file, with token cost per file. Lets the agent
      audit its own efficiency and adjust strategy mid-session. This session's
      40+ file operations could have been collapsed to ~15.
---

### 4. Post-edit import-check hook — NEW hook, tiny
After any change under `agent_core/tools/`, run `python -c "import agent_core.tools"` automatically. Catches schema/registration errors (the unhashable-type bug) in seconds, not a debug cycle. Nothing like it exists (`hot_reload`/`kernel_reload` are manual).

### 5. Mode-aware prompt trimming — assembly tweak (ties into the tool_mode work)
In `read_only`/`shell_only`, exclude edit-oriented fragments (`file_ops_workflow.md` talks about `edit_file`/`write_to_file`; `meta_playbook.md` about edits/checkpoints). Fewer prompt tokens per call + less drift for smaller LLMs. Not a new tool.

### 6. Hardcode-able chains — reuse, don't build

- **pre-change context prep** → `minimal_context_dump` already chains `get_symbol`+`find_impact`+`batch_file_api` into one capped file. Recommendation: harness auto-invokes it (or a cached lighter variant) before multi-edit tasks instead of the LLM making 4–6 individual atlas calls. Don't duplicate it.

