## Tool — Session worklog + handoff (merges `worklog` + `session_handoff` + `session_diff` + `session_map` + `changeprint` + `session_summary` + `session_history` + `pie_session_summary`)

**Name options:** hooks: `session_handoff` (recommended) · `worklog` · `session_log` · `session_anchor`. Query tool: `session_summary` (recommended) · `session_map` · `session_diff`

**Why we need**  Nothing persists a structured per-session delta. `session_state` is in-memory (resets each turn), `kernel_retrieve` is fuzzy semantic memory, `audit` is per-call raw logs, `tool_stats`/`file_stats` are counters only. A next agent must re-discover "what changed, what's pending" from scratch — `AGENTS.md`'s "single persistence path: SQLite" makes this natural to add to `kernel.db`.

**Design (2 halves, ~300 LOC total):**
1. **Harness hooks (no LLM call):**
   - New `sessions` table in `kernel/persistence/db.py` (`SCHEMA_SQL` + ~4 methods): `session_id, ts, files_changed(json: path+mtime+1-line summary), tools_added/merged/renamed, decisions, pending_todos, token_estimate, blockers`.
   - Post-chat `write_worklog()` — called in `iter_agent_events` `finally` block (engine.py:97); data from `SessionState` (`edits_log`, `files_touched`, `todo_plan`) + the tool_result stream; tool registration changes go to a `tool_history` table (feeds Tool 1).
   - Pre-chat `build_handoff()` — at engine.py:54 injection point, reads latest session row, renders ≤300 tokens: `"Last session changed {files}→{summary}; watch {files}; pending {todo}."`, appended to `context_info`.
2. **Queryable tool `session_summary` (CAT_META, `agent_core/tools/session_ops.py`):**
   - Current session: tools called (counts, ok/err), files changed with edit summaries, per-file token cost (from `file_access`/`output_chars`), pending todos.
   - `session_summary(last=1)`: reads persisted worklog → "last session…" (session_history behavior).
   - `session_summary(force=True)`: lets the LLM checkpoint mid-session (merges session6's `compact_history` intent).

**Add-ons to include:**
- Real before/after 1-line summaries using undo checkpoints or `edit_file`'s already-computed unified diff (`_render_unified_diff` in file_ops.py:330).
- Pending-todo + blocker carryover so a stopped agent resumes without re-exploring.
- Skip paths that no longer exist at handoff; hard token cap on the injected snippet.

---
