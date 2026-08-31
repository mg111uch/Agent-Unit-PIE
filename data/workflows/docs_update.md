# Docs Update — General Subgraph (Injectable)

General doc-sync loop for any module. Inject after `validate` (or before `loop/stop`) in parent workflow. Parent adds one node:

```
["doc_sync", "DOC SYNC\nreport_freshness→update docs", "rect", "#e0e0ff", x,y,w,h, "", "docs_update.json"]
```

Click-through in `workflow_graph.html` opens this subgraph.

## Detect Stale

```bash
conda run -n myenv python -c "from agent_core.tools.code_rag.tools import report_freshness_tool; print(report_freshness_tool({}))"
# or via tool: report_freshness
```

Lists `system_devpt_reports/*/README.md` + `status.md` + `usage.md` where `_Last verified` < last git change or cited `file:symbol()` missing in atlas. Empty → docs fresh → stop.

## Identify Scope

Scope from changed paths (via `git diff --name-only`):

- `codebase/kernel/*` → `system_devpt_reports/kernel/README.md`, `usage.md`, `PhasePlan.md` Phase entry
- `codebase/modules/simulators/<sim>/*` → `SimDvptPhases.md` / module README
- `data/workflows/*` → `*.md` companion + `research_development.md` if top-level
- Always: `codefiles_map.md` (auto) and `system_devpt_reports/PhasePlan.md` (phase summary)

## Update Docs

- Prose docs: `edit_file` (old_string must match once) — never hand-edit `data/topics/*/graph.json` (derived).
- Auto docs:
  ```bash
  conda run -n myenv python -c "import codebase.agent_tools.atlas_tools.run_cmds; ..." # codefiles_map if exists
  conda run -n myenv python scripts/render_status.py --write  # if status regeneration needed
  ```
- Include `file:line` citations + `_Last verified: YYYY-MM-DD` bump.

## Verify

```bash
conda run -n myenv python -c "from agent_core.tools.code_rag.tools import report_freshness_tool, report_schema_check_tool; print(report_freshness_tool({})); print(report_schema_check_tool({}))"
```

If stale remains → loop to `update_docs`. Pass → return to parent `loop→orient`.

## Injection Recipe

In parent `*.json` (kernel/sims):

1. Add node `["doc_sync", "DOC SYNC\nreport_freshness→update docs", "rect", "#e0e0ff", x,y,w,h, "", "docs_update.json"]`
2. Rewire `validate→doc_sync→loop` (or `compress→doc_sync→loop` for popu_sim). Keep legacy array format — `workflow_graph.html` handles both array `n[8]` and dict `n.mdRef`.

Parent `*.md`: add `## Doc Sync` section linking to `docs_update.md#detect-stale`.

No extra persistence — uses existing `citation_cache` + `report_freshness` (kernel.db one path).
