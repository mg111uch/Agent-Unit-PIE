# Economy — Moonshot economic layer (Phase 1+)

> Agent rule: shipped features → Features table here; unimplemented → `roadmap.md`; next task → `status.md`. Follows populaDyn_simu/stock_analyser convention. No Status column (per user rule).

## Features

| Feature | Notes |
|---|---|
| _none yet — Phase 1 in progress_ | |
| Phase 1: Economic Object Model (Actor/Opportunity/Task/Transaction + ledger in market.db) | `codebase/modules/economy/` |
| Phase 2: opportunity_engine (score demand×capability×margin×speed×cost + debate hook) | `scoring.py`, `challenge.py` |
| Twin-bridge A: CityTwin/CompanyTwin → Actor snapshot to ledger | `twin_bridge.py` |
| Twin-bridge B: CityTwin → sim params + epoch heuristic | `twin_bridge.py` twin_to_params/twin_to_epoch |
| Twin-bridge C: sim outcome → twin timeline + economy sync | `twin_bridge.py` record_outcome/sync_economy |
| Phase 3: enterprise_sim (firm hire/invest behaviours in popula_dyn) | `popula_dyn/behaviours/hire.py`, `invest.py` + firm factory |
| Phase 4: capital_engine (cash books + human-approval gate) | `capital.py` earn/spend/propose/approve |
| Phase 5: execution_engine (score→stage→approve→delta pipeline) | `execution.py` run_experiment/record_outcome_tx |
| Phase 6: economic loop subgraph (12-node observe→pivot→observe) | `data/workflows/economic_loop.json`, wired in research_development subgraphs |
| Phase 7: industrial graph lite (supplier/capability queries) | `industrial.py` suppliers/map/gaps/paths, no new tables |

## Identity

- Code: `codebase/modules/economy/`
- Ledger: `data/market.db` (domain store, stock precedent; kernel.db stays cognition-only)
- Docs: `system_devpt_reports/economy/`

(End of file)
