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
| Economic event adapter (FireFlow-shaped → kernel bus) | `event_adapter.py` translates `PaymentSettled` payloads (score_cli proxy pattern, no external calls) into kernel event + `capital_flow` signal via `kernel_bus` |
| Opportunity evidence + expected value | `scoring.score_with_evidence`: {confidence, evidence_age, evidence_count, source_diversity} gates/scales the 7-factor score (no-evidence PASS capped at WATCH) + EV = P×contribution − loss − opportunity_cost |
| Prospect evidence + pain score + decision | `prospects.py`: `pro_<hash>` id, evidence/triggers/value/contactability/confidence, geometric-mean pain (evidence×value×fit×access×urgency×pilot_prob), decide IGNORE/RESEARCH/OUTREACH/PILOT; persisted in market.db `prospects` |
| Prospect discovery + ranking | `discovery.py`: manual/signal collectors, honest deferred stubs for live Udyam/GeM/ONDC, `rank()` dedups + orders by pain with decision attached |
| Service templates + quote | `service_templates.py`: 2 seeds (supplier_discovery_100, price_collection_50), cost-plus quote, `instantiate()` emits FireFlow tasks + PIE proposal envelope |
| Outreach drafts + gates | `outreach.py`: evidence-only drafts (STOP footer), approval gate (price/confidence), keyword response classifier, 7-day frequency cap |
| Delivery bridge + margin gate | `delivery.py`: template→project tree, `check_margin()` blocks negative-contribution payouts, `worker_brief()` earn-path instructions |
| Revenue metrics + experiments | `revenue.py`: funnel conversions, time-to-first-revenue, min-N A/B with kernel-ready findings |
| Live discovery job | `revenue_job.py`: real 2026 expansion seeds → rank → top-5 priced offers; persists to market.db, sends nothing |
| Candidate twin | `jobs/candidate.py`: resume.md → evidenced skills + hard-gate prefs (₹1L/mo, ±3h overlap, full-time/contract) |
| Job ingestion | `jobs/sources.py`: RemoteOK/WWR/Greenhouse/Lever/Ashby/Hasjob adapters + canonical normalizer (fail-soft, no scraping) |
| Job fit engine | `jobs/fit.py` + `fit_cli.py`: hard gates (remote/employment/junior/India/comp-floor, unknown comp never rejects), india-first + no-relocation caps, description match → APPLY/TAILOR/OUTREACH/SKIP |
| Application packs + tracker | `jobs/apply.py`: evidence-bound variants (master never edited) + submit policy gate |
| Job outreach + policy | `jobs/job_outreach.py`: network-first notes, daily caps, human approves every send |
| Job learning + economics | `jobs/learning.py`: funnel/source rates, min-N hypotheses, EV per application (pending-comp honest) |

## Identity

- Code: `codebase/modules/economy/`
- Ledger: `data/market.db` (domain store, stock precedent; kernel.db stays cognition-only)
- Docs: `system_devpt_reports/economy/`

## Revenue loop — next-agent runbook

```bash
cd /home/manigupt/Hello/Agentic_Unit_PIE
# 1. Dry-run discovery (no writes): 20 seeds → rank → top-5 offers
conda run -n myenv python codebase/modules/economy/revenue_job.py --no-persist
# 2. Live run (persists to market.db, sends nothing): drop the flag
conda run -n myenv python codebase/modules/economy/revenue_job.py
# 3. Inspect the CRM
conda run -n myenv python -c "import sys;sys.path.insert(0,'codebase');from modules.economy import ledger;print(len(ledger.list_table('prospects')))"
```

Push to FireFlow (server up first: `cd backend && npm start`). Reuse the shared
local operator — password lives in `backend/.pie_operator` (chmod 600, local-only,
never paste it into docs), JWTs expire in 1h so mint a fresh token each session:

```bash
export TOKEN=$(curl -s -X POST localhost:5000/api/auth/login -H 'Content-Type: application/json' \
  -d "{\"username\":\"pie_operator\",\"password\":\"$(cat /home/manigupt/Hello/reddit-clone/backend/.pie_operator)\"}" \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")
```

```bash
curl -s -X POST localhost:5000/api/prospects/import -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"items":[{"company":"X","problem":"supplier discovery"}]}'
curl -s localhost:5000/api/metrics/funnel -H "Authorization: Bearer $TOKEN"
```

Rules: seeds live in `revenue_job.py:SEEDS` (real 2026 evidence, source-tagged); never invent companies. PILOT/OUTREACH = cleared for contact lookup + human approval — drafts via `outreach.draft_message`, sends only through `/api/outreach` approve→send. Sender signature auto-appends from `backend/.sender_identity` (local-only, never paste into docs). Live Udyam/GeM/ONDC connectors still deferred (`discovery.collect` says so).

(End of file)
