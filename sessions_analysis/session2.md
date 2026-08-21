## Token Burn Analysis 1

**#1 consumer:** Reading `__init__.py` (546 lines) **5 times** — each re-read to verify registration positioning after edits. Total: ~2500+ lines.

**#2 consumer:** Reading `file_ops.py` (593 lines) **3 times** — same reason.

**#3 consumer:** Re-reading files after small edits to verify correctness, even though I should have trusted `edit`'s "success" return.

## Token Burn Analysis 2

| Step | Tokens | Why |
|------|--------|-----|
| Explore agent for tool call architecture | ~8-10K | Returned full code of engine.py (712 lines), executor.py, ws_handler.py, registry.py — I had to skim through massive output |
| Reading engine.py in chunks | ~5 reads × 60-200 lines each | Had to re-read same file 5+ times to find exact edit locations |
| Edit failures / re-reads | ~2-3 cycles | `old_string` match failures because I didn't have precise line context |
| Understanding registration patterns | Grep + read __init__.py multiple times | Had to manually trace which `_register_*` function a tool belongs to |
---

## Behaviors that wasted tokens (no new tool needed)

| Waste | Fix (already possible) |
|---|---|
| Re-reading full files after edits | Trust `edit`'s success return + the diff it returns |
| Reading whole `__init__.py` to find one function | Use `read_section` with pattern `def _register_file_tools` |

## ♻ Generalized Workflow (Any Issue)

The **same 8-phase workflow** applies to any issue-resolution task:

1. **SCOPE** — Read task + devpt reports + diagnosis/fix plan. Identify BLOCKER vs HIGH vs MED/LOW. Understand the data flow for each fix. Read the AGENTS.md for workflow rules.
2. **TRACE** — For each fix, read ALL files in the data flow chain (not just the symptom location). Map where values originate, transform, and terminate. Use pie_batch_read for 2+ files.
3. **PLAN** — Group all edits by file. Check blast radius with `pie_find_impact` for every symbol you plan to edit. Identify repeated patterns (same change in 3 places) for batch. Identify cross-file patterns (same uuid fallback in 4 files) for parallel editing.
4. **FIX** — Apply edits root-cause-first, defense-in-depth at every consumer. Read a file once, apply ALL its edits, move on. Use individual `edit` for multi-line blocks; use `replace_all` for isolated renames.
5. **VALIDATE** — Run seed_hypotheses + validate_capabilities (or equivalent module tests). Fix regressions before moving on. Batch 3-5 fixes per validation run.
6. **DOCUMENT** — Update status.md: add Recent Changes line, remove fixed Known Gaps, bump _Last verified. Append checklist ticks to fix plan. Update the workflow graph/page (workflow_graph.html) with new patterns.
7. **OPTIMIZE** — Review for: double work (blocking+streaming LLM calls), unnecessary re-reads, missed batch opportunities, argumentation loops with reviewer. Collapse into one source of truth.
8. **GENERALIZE** — Create/update workflow HTML so future agents reuse the pattern instead of rediscovering it. Add any new tool suggestions discovered during the session.