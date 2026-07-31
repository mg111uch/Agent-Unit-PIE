## Session retro: where tokens went & what would have helped

Evidence from this session (4 merge/rename tasks: batch tools, todo, kernel-warning removal, tool-mode design):

**The #1 token hotspot was cross-file tool tracing.** For each task I re-traced the same tool through ~9 files by hand: `__init__.py` (registration) → impl (`meta_ops.py`/`file_ops.py`) → `stepper.py` → `session_state.py` → `audit.py` → `mock_provider.py` → tests → prompt fragments → `mcp_server.py`. I did this ~4× (batch, todo, kernel, mode). That's an estimated 60–70% of session tokens.

**#2: whole-file reads for small slices.** `file_ops.py` (627 lines) read 3+ times; `registry.py`, `stepper.py`, `session_state.py` similar. The existing **codebase atlas** (`get_symbol`, `symbols_by_file`, `file_api`, `batch_file_api`, `call_chain`, `find_impact`, `minimal_context_dump`) would have turned these into single-function fetches — but the `code_rag` pack is **off** in config.json and the atlas DB is **4 days stale** (Jul 27), so it wasn't available. That's the single biggest lever, already built.

**#3: a real import bug cost a debug cycle.** My read_file schema used an unhashable item type; it only surfaced as an exception at `_register_all()` — a post-edit import-check hook would have caught it instantly.

---

## Recommendations (each checked against existing tools — no duplicates)

### 1. `tool_anatomy` — NEW tool (highest value, nothing like it exists)
Deterministic repo-scan, one call replaces the #1 hotspot:
- registration `file:line` + category + `mcp_expose` + schema params
- implementation function `file:line`
- every reference: prompt fragments, mock scenarios, tests, `stepper._EDIT_TOOLS`, `audit._WRITE_TOOLS`, `session_state` observers, MCP exposure
- optional "history" line (e.g. "merged from batch_edit → edit_file(edits), 2026-07-31")

Not a duplicate: the atlas indexes *symbols in source*; `report_inventory` scans `system_devpt_reports`; `list_capabilities` is the hypothesis engine; `hot_reload` reloads modules. This was proposed as `trace_registration` in session1.md but never built.

### 2. Activate the existing atlas — NO new code, just config + regen
Enable `code_rag: true` in tool_packs and regenerate the atlas (`run_cmds.py … "Make Codebase_atlas"`). This single change converts most whole-file reads into `get_symbol`/`batch_file_api` calls — the exact fix for pattern #2. I'd argue this plus #1 gives ~70% of the total win.

### 3. `worklog` post-chat hook + `session_handoff` pre-chat hook — NEW hooks
- **Post-chat:** write a structured delta to sqlite (one persistence path per AGENTS.md): files touched (path + mtime + 1-line diff summary), tools added/merged/renamed, decisions, pending TODOs.
- **Pre-chat:** inject ≤300 tokens at session start — "Last session changed {files}→{summary}; watch {files}; pending {todo}."
This directly answers "next agent accessing the same files should be faster." It complements `kernel_retrieve` (semantic embedding memory) and `session_state` (in-memory, resets each turn) — neither gives a structured delta. Related to session6.md's `session_history` proposal, but harness-side so it happens without the LLM asking.

### 4. Post-edit import-check hook — NEW hook, tiny
After any change under `agent_core/tools/`, run `python -c "import agent_core.tools"` automatically. Catches schema/registration errors (the unhashable-type bug) in seconds, not a debug cycle. Nothing like it exists (`hot_reload`/`kernel_reload` are manual).

### 5. Mode-aware prompt trimming — assembly tweak (ties into the tool_mode work)
In `read_only`/`shell_only`, exclude edit-oriented fragments (`file_ops_workflow.md` talks about `edit_file`/`write_to_file`; `meta_playbook.md` about edits/checkpoints). Fewer prompt tokens per call + less drift for smaller LLMs. Not a new tool.

### 6. Hardcode-able chains — reuse, don't build
- **verify-after-edit** → already solved (`edit_file` returns diff; `read_file` auto-cache).
- **batch read/edit** → already solved via `paths`/`edits` params (this session).
- **pre-change context prep** → `minimal_context_dump` already chains `get_symbol`+`find_impact`+`batch_file_api` into one capped file. Recommendation: harness auto-invokes it (or a cached lighter variant) before multi-edit tasks instead of the LLM making 4–6 individual atlas calls. Don't duplicate it.
- **plan_validate** (optional, session6.md): pre-validate `old_string`s before applying to cut fail-recover cycles on edit-heavy tasks. The merged `edit_file(edits)` partially mitigates; a no-write validation call would be novel but is the weakest of these.

---

## Suggested build order for the fresh session
1. Enable `code_rag` pack + regenerate atlas (immediate, zero new code)
2. `tool_anatomy` tool
3. `worklog`/`session_handoff` hooks
4. Post-edit import-check hook
5. Mode-aware prompt trimming (alongside the tool_mode implementation)

Want me to fold these into a concrete implementation plan for the fresh session (start with 1–3)? I'd also scope the `tool_anatomy` schema and the worklog sqlite schema before we build.