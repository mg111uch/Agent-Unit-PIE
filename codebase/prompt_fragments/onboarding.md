# Onboarding (project context, cheap)

Before deep-diving a module, orient via cheap sources in this order:

1. `project_history` graph (`data/topics/project_history/graph.json`) — prior
   decisions and intentional removals. Nodes carry `side=decision` with a
   `premise` (why), `evidence`, and `sources`; removal rationale is linked via
   `contradicts` edges. Check it before re-adding "missing" code — it may have
   been removed deliberately.
2. `list_capabilities` — live `capability_claim` / `known_gap` hypothesis
   state (id, status, evidence path/symbol) from the HypothesisEngine. This is
   the source of truth for "what works", not phase diaries.
3. `report_inventory` / `report_freshness` / `report_schema_check` — report
   health without reading whole files. Treat a status.md without `_Last
   verified` as empty.

Do NOT read entire `system_devpt_reports/*/status.md` or roadmap files to
answer "what works?" — use the tools above. Read a report file only when you
need the raw bullet text.
