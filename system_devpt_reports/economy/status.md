# Economy Status
_Last verified: 2026-09-06_

> Agent rule: Recent holds max 5 entries (newest first). Shipped detail lives in README Features — never duplicate the full ship list here; drop oldest when adding.

## Current State
- Economic layer live: object model + ledger, opportunity engine, twin sync both ways, firm hire/invest, capital books + approval gate, execution pipeline, economic loop subgraph, industrial graph lite, barter kernel, fiscal ledger (all rows in README Features; smoke ok, harness 5/5 at ship time).

## Next (single source for the next task)
_Economic core + twin sync + fiscal record shipped. Next slice TBD (supplier graph expansion or export engine)._

## Recent (newest first, max 5)
- 2026-09-09: Opportunity engine 7-factor — scalability/adjacency added (objects/ledger/scoring/challenge + FireFlow thin proxy via score_cli, no duplicated weights); tmp-DB smoke ok.
- 2026-09-08: Fiscal ledger shipped — fiscal.py (fiscal_runs in market.db, record_fiscal/query_fiscal, net column) wired into execution.record_outcome_tx; smoke ok on tmp DB (net=15, idempotent), sim determinism intact.
- 2026-09-08: Barter kernel shipped — scoring.barter_price over popula_dyn scarcity, no ledger writes, sim direction-verified.
- 2026-09-08: Actor→Unit rename shipped — objects/ledger (units table + actors→units migration, actors never dropped) + all callers; tmp-DB smoke ok.
- 2026-09-06: Industrial graph lite shipped — industrial.py graph queries, smoke ok, harness 5/5.

(End of file)
