# Onboarding (project context, cheap)

Before deep-diving a module, orient via cheap sources in this order:

1. `project_history` topic — prior decisions and intentional removals,
   stored in kernel semantic memory (SQLite). Query it with
   `python scripts/topic_ops.py list --topic project_history [--side decision]`
   (add `--json` for machine-readable output). Nodes carry `side=decision`
   with a `premise` (why), `sources`, and removal rationale linked via
   `contradicts` edges. Check before re-adding "missing" code — it may have
   been removed deliberately. Do NOT read
   `data/topics/project_history/graph.json` directly; it is a derived export.
2. `list_capabilities` — live `capability_claim` / `known_gap` hypothesis
   state (id, status, evidence path/symbol) from the HypothesisEngine. This is
   the source of truth for "what works", not phase diaries.
3. `report_inventory` / `report_freshness` / `report_schema_check` — report
   health without reading whole files. Treat a status.md without `_Last
   verified` as empty.

**For simulation topics (e.g., `popu_sim`):**
- Run `python scripts/find_untested_parameters.py --topic <name> --suggest`
  to find untested parameter ranges
- Use `python scripts/topic_ops.py list --topic popu_sim --json` to see
  structured findings with IMPROVED/DEGRADED/COLLAPSED verdicts
- See `data/workflows/popu_sim_dev.json` for the simulation development loop

Recording an intentional removal: run `scripts/record_removal.py --name N
--premise P [--contradicts T]` (see `system_devpt_reports/kernel/usage.md`).
It persists via the kernel and emits a contradiction signal when a contradicts
edge joins two agreed beliefs.
