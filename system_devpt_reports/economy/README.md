# Economy — Moonshot economic layer

> Agent rule: shipped features → Features table here; unimplemented → `roadmap.md`; next task → `status.md`. Follows populaDyn_simu/stock_analyser convention. No Status column (per user rule).
> Naming rule: NEVER use session-step labels (`Phase X`, `Twin-bridge X`, or any numbered/lettered build-stage tag) in this table. List features by what they ARE (e.g. `Capital books`, not `Phase 4`). Stage labels belong to session history only, never to shipped-feature docs.

## Features

| Feature | Notes |
|---|---|
| Economic Object Model (Unit/Opportunity/Task/Transaction + ledger in market.db) | `codebase/modules/economy/` |
| Opportunity engine (score demand×fit×margin×speed×cost×scalability×adjacency + debate hook) | `scoring.py`, `challenge.py`, `score_cli.py` (FireFlow thin proxy) |
| Twin snapshots → Unit ledger (CityTwin/CompanyTwin snapshot to ledger) | `twin_bridge.py` |
| Twin → sim params + epoch heuristic | `twin_bridge.py` twin_to_params/twin_to_epoch |
| Sim outcome → twin timeline + economy sync | `twin_bridge.py` record_outcome/sync_economy |
| Enterprise sim (firm hire/invest behaviours in popula_dyn) | `popula_dyn/behaviours/hire.py`, `invest.py` + firm factory |
| Capital books (cash books + human-approval gate) | `capital.py` earn/spend/propose/approve |
| Execution pipeline (score→stage→approve→delta) | `execution.py` run_experiment/record_outcome_tx |
| Economic loop subgraph (12-node observe→pivot→observe) | `data/workflows/economic_loop.json`, wired in research_development subgraphs |
| Industrial graph lite (supplier/capability queries) | `industrial.py` suppliers/map/gaps/paths, no new tables |
| Fiscal ledger (runs → queryable cost-vs-benefit record) | `fiscal.py` record_fiscal/query_fiscal, `fiscal_runs` in market.db |
| Barter kernel: scarcity-priced exchange (no currency) | `scoring.barter_price` wrapper over popula_dyn `core/scarcity.py`; used by sim `trade_ag`/`produce`, no ledger writes |

## Identity

- Code: `codebase/modules/economy/`
- Ledger: `data/market.db` (domain store, stock precedent; kernel.db stays cognition-only)
- Docs: `system_devpt_reports/economy/`

(End of file)
