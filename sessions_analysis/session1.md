Based on this session, here's my analysis.

## Where tokens actually went (this session)

| Step | Cost driver | Est. share |
|---|---|---|
| Understanding tool registration (`registry.py` 304L + `tools/__init__.py` 487L + `config.py` + `config.json`) | Full-file reads of dense registration/config code | ~35% |
| MCP policy change | Full read of `mcp_server.py` + repeated `python -c` smoke tests to check exposure | ~15% |
| README + status.md audits | 307L README read (twice, chunked) + `status.md` + `validate_capabilities.py` + `citations.py` | ~25% |
| **Repeated verification smoke tests** | 6+ separate `python -c` runs: count tools, per-category counts, mcp exposure, flag simulation, schema checks | ~15% |
| Edits + exact-string re-reads | re-reading to confirm `old_string` uniqueness | ~10% |

**Single biggest sink:** reading `tools/__init__.py` + `registry.py` end-to-end to discover "which tools exist, in which category, which are flag-gated, what's exposed via MCP" — then re-deriving it again via smoke tests when counts changed.

## Repeated tool-call patterns (candidates to hardcode)

1. **"Discover live tool surface"** — I did this 3 separate ways: read files, then `python -c` counting, then grep. Repeated every time a tool changed.
2. **"What is actually active?"** — trace `config.json` → `config.py` → `resolve_active_tool_packs()` → registry. Did it for both subagent and MCP tasks.
3. **"Audit docs vs code"** — manually cross-checking README/status claims against code, then re-verifying with `report_schema_check`/`report_freshness` (the tools exist but I had to know to call them and parse JSON).
4. **"grep → bounded context read → targeted edit"** — already covered by `grep_search(context_lines=)` + `read_section` + `check_before_edit` + `edit_file(edits=[...])`. No new tool needed here.

## Novel recommendations (verified against existing tools — no duplicates)

**1. `tool_surface` tool (CAT_META)** — returns the *live* registry manifest in one call: `{tool: {category, mcp_expose, flag_gated, enabled_now}}` plus resolved config (`active packs`, `tool_mode`, `subagent_task_enabled`, `git_tools_enabled`). 
- *Why novel:* `get_index_info` = atlas symbols/stats (not the tool registry); `tool_stats` = *runtime usage* telemetry; `TOOLS`/`TOOL_META` = names+descriptions only, no category/mcp/gating. None expose the category→tool→flag→mcp mapping I had to read ~800 lines to learn.
- *Saves:* the entire discovery phase + all 6 smoke-test runs. This was the #1 token cost.

**2. `md_outline` tool (CAT_META)** — heading tree of a markdown file with line ranges + per-section line counts (`##`/`###` + word counts).
- *Why novel:* `file_skeleton` is **AST-based, Python-only**. `read_section` requires you to already *know* a regex to search for. Neither gives "here's the section map, jump to line N" — which is what I needed for the README/status audits. Cuts a 307L read to a ~15-line outline + targeted `read_file(offset=...)`.

**3. Pre-chat hook: inject a cached `tool_surface` manifest into the system prompt at turn 0.**
- The model receives tool *schemas* but never the *semantics* (which tools are category-gated, flag-gated, MCP-exposed, effective config). A compact one-time manifest (50–60 lines) would eliminate re-discovery entirely for every future session — the single biggest structural saving. Recompute on `hot_reload`.

**4. Post-edit / session-end hook: run the report maintenance chain automatically.**
- The protocol already exists in `prompt_fragments/sys_devpt_reports.md` (bump `_Last verified`, append Recent Changes, `validate_capabilities`) but is manual. A hook that: `report_freshness` on session start, and on code-change end auto-runs `report_schema_check` + `validate_capabilities` for touched modules. No new tool — just wiring existing ones.

**5. Extend `report_freshness`/`resolve_citations` scope** rather than a new tool — they already cover `system_devpt_reports/*.md`. The gap is they're JSON-only, so an LLM must parse them; a thin wrapper that returns *human-readable* "these 4 citations are broken: ..." would help small LLMs. This is an extension, not a duplicate.

## Recommended (best ROI) plan

1. Implement **`tool_surface`** (novel, replaces discovery + smoke tests) and **`md_outline`** (novel, cuts doc-audit reads) as CAT_META tools.
2. Wire **pre-chat hook** to inject the tool_surface manifest once at session start; recompute on hot_reload.
3. Wire **session-end hook** to auto-run `report_schema_check` + `validate_capabilities` on touched modules (uses existing tools).
4. Optionally, a human-readable wrapper over `report_freshness`.

-------

## Token consumption for future agents

**A. Shrink the per-turn schema payload (highest recurring cost).**
`get_schemas()` serializes all 58 tool descriptions into every LLM call. The loop already filters by active pack (`engine.py:146`), but the CLI path (`run_agent_turn` → `tool_categories=None` → `resolve_active_tool_packs()`) only gets `['file']` by default. Ensure `stepper.py`/CLI always pass the resolved pack list.

## C. Token-consumption optimizations (for future agents)

1. **`tool_surface` tool (CAT_META)** — the biggest token saver from this session. One call returns the live `{tool → category, mcp_expose, flag_gated, enabled}` manifest + resolved config. Replaces reading ~800 lines (`registry.py` + `tools/__init__.py` + `config.py`) and 6+ smoke-test runs.
2. **`md_outline` tool (CAT_META)** — heading map with line ranges for markdown files. Cuts the 307-line README audit to a ~15-line outline + targeted `read_file(offset=...)`.
3. **Pre-chat hook**: inject the `tool_surface` manifest into the system prompt once at turn 0 (recompute on hot_reload). Eliminates registry re-discovery for every session.
4. **Report tools should offer a compact summary mode** — the JSON report output is verbose for LLM consumption; a `detail="summary"` param returning just counts/names would cut tokens.

## Execution/token optimization

- **`tool_anatomy` tool** (registration→file:line, category, mcp_expose, mock scenario, test, prompt-fragment refs) — removes the repeated manual tracing.
- **Post-edit import/syntax check hook** after `edit_file` on `.py` files — catches regressions before pytest, cheaper than a full test run.
- **Mode-aware prompt trimming** for read_only/shell_only (don't load fragments for unavailable tools).
- **Notes / out of scope:** base_persona.md and response_contract.md still mention get_workspace_info/read_file/check_path_exists, which are unavailable in shell_only — cosmetic, out of scope unless you want them tagged later.
implementation_guardrails.md items 5/10/11 reference todo/edit_file — also stale in read_only; left as-is per your ask.

