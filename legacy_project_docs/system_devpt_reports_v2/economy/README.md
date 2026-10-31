# Economy (Level 1) — PIE-side economic layer ("Moonshot economic layer")

> Agent rule: shipped features → §2; unimplemented → `roadmap_master.md`; next task → `iteration_log.md`. **No Status column; no session-step labels** (`Phase X`, `Twin-bridge X`, …) — name features by what they are.
> Code: `$PIE_ROOT/codebase/modules/economy/` · Ledger/domain store: `data/market.db` (kernel.db stays cognition-only) · FireFlow counterpart: `fireflow_app/README.md`.

## 1. Purpose & position

The economy module turns PIE cognition into **earning**: score demand with evidence, find prospects with a concrete pain, design a sellable offer, draft evidence-only outreach, hand accepted work to FireFlow for execution/settlement, and learn from the funnel. It also hosts the **job-search agent** — the first specialized economic agent (your own career as customer #1).

**Bootstrap strategy (adopted):** FireFlow is infrastructure; PIE is the sales machine. Sell *outcomes* (fixed price, scope, deadline, acceptance criteria), not "an AI economic OS". Early offers: supplier discovery, vendor comparison, competitor intelligence, industrial market research, lead lists, price collection, catalogue creation, data cleaning/enrichment, document extraction, AI response evaluation, Indian-language data generation, local market verification, procurement/export-market research. **Hunt existing-world revenue first** (customer-discovery levels: 1 explicit demand → 2 observable pain → 3 recurring industry pain → 4 emerging opportunity → 5 new venture, only after evidence).

## 2. Features (shipped)

### 2.1 Economic core
| Feature | Notes |
|---|---|
| Economic Object Model (Unit / Opportunity / Task / Transaction + ledger in `market.db`) | shared language with FireFlow |
| Opportunity engine | demand×fit×margin×speed×cost×scalability×adjacency + debate hook — `scoring.py`, `challenge.py`, `score_cli.py` (FireFlow thin proxy) |
| Opportunity evidence + expected value | `scoring.score_with_evidence`: confidence, evidence_age, evidence_count, source_diversity gate/scale the 7-factor score (no-evidence PASS capped at WATCH); EV = P×contribution − loss − opportunity_cost |
| Twin snapshots → Unit ledger | `twin_bridge.py`: CityTwin/CompanyTwin snapshot to ledger |
| Twin → sim params + epoch heuristic | `twin_bridge.py` `twin_to_params` / `twin_to_epoch` |
| Sim outcome → twin timeline + economy sync | `twin_bridge.py` `record_outcome` / `sync_economy` |
| Enterprise sim | `popula_dyn` firm hire/invest behaviours + firm factory |
| Capital books | `capital.py` earn/spend/propose/approve — cash books + human-approval gate |
| Execution pipeline | `execution.py` run_experiment / record_outcome_tx: score→stage→approve→delta |
| Economic loop subgraph | `data/workflows/economic_loop.json` (12-node observe→pivot→observe), wired into `research_development` |
| Industrial graph lite | `industrial.py` suppliers/map/gaps/paths — no new tables |
| Fiscal ledger | `fiscal.py` record_fiscal/query_fiscal; `fiscal_runs` in `market.db` — runs → queryable cost-vs-benefit |
| Barter kernel | `scoring.barter_price` wraps popula_dyn `core/scarcity.py`; no currency, no ledger writes |
| Economic event adapter | `event_adapter.py`: FireFlow-shaped `PaymentSettled` → kernel event + `capital_flow` signal via `kernel_bus` (**no external calls**) |
[LOOPHOLE INT-01 · S1] The event adapter is shape-only; no documented live FireFlow→kernel transport. [/LOOPHOLE]
[LOOPHOLE INT-04 · S2] `market.db` ledger/prospects overlap FireFlow's authoritative store — declare ownership. [/LOOPHOLE]

### 2.2 Revenue acquisition (prospect → offer → outreach → delivery)
| Feature | Notes |
|---|---|
| Prospect evidence + pain score + decision | `prospects.py`: `pro_<hash>` id; evidence/triggers/value/contactability/confidence; geometric-mean pain (evidence×value×fit×access×urgency×pilot_prob); decide IGNORE / RESEARCH / OUTREACH / PILOT; persisted in `market.db.prospects` |
| Prospect discovery + ranking | `discovery.py`: manual/signal collectors; **honest deferred stubs for live Udyam / GeM / ONDC**; `rank()` dedups and orders by pain with decision attached |
| Service templates + quote | `service_templates.py`: 2 seeds (`supplier_discovery_100`, `price_collection_50`); cost-plus quote; `instantiate()` emits FireFlow tasks + PIE proposal envelope |
| Outreach drafts + gates | `outreach.py`: evidence-only drafts (STOP footer), approval gate (price/confidence), keyword response classifier, 7-day frequency cap |
| Delivery bridge + margin gate | `delivery.py`: template→project tree; `check_margin()` blocks negative-contribution payouts; `worker_brief()` earn-path instructions |
| Revenue metrics + experiments | `revenue.py`: funnel conversions, time-to-first-revenue, min-N A/B with kernel-ready findings |
| Live discovery job | `revenue_job.py`: real 2026 expansion seeds → rank → top-5 priced offers; persists to `market.db`, **sends nothing** |

### 2.3 Job-search agent
| Feature | Notes |
|---|---|
| Candidate twin | `jobs/candidate.py`: `resume.md` → evidenced skills + hard-gate prefs (₹1 L/mo floor, ±3 h overlap, full-time/contract); every claim has an evidence pointer; master resume never edited |
| Job ingestion | `jobs/sources.py`: RemoteOK / WeWorkRemotely / Greenhouse / Lever / Ashby / Hasjob adapters + canonical normalizer (fail-soft, no scraping) |
| Job fit engine | `jobs/fit.py` + `fit_cli.py`: hard gates (remote, employment, seniority, India eligibility, comp floor; unknown comp never rejects), india-first + no-relocation caps, description match → APPLY / TAILOR / OUTREACH / SKIP |
| Application packs + tracker | `jobs/apply.py`: evidence-bound variants + submit policy gate |
| Job outreach + policy | `jobs/job_outreach.py`: network-first notes, daily caps, human approves every send |
| Job learning + economics | `jobs/learning.py`: funnel/source rates, min-N hypotheses, EV per application (pending-comp honest) |

Never build a LinkedIn scraper/automation bot; use official APIs, public ATS feeds, RSS, company career pages, email; hand off when terms forbid automation.

## 3. Runbook (next-agent)

```bash
cd $PIE_ROOT
conda run -n myenv python codebase/modules/economy/revenue_job.py --no-persist   # dry run: 20 seeds → rank → top-5 offers
conda run -n myenv python codebase/modules/economy/revenue_job.py                 # live: persists to market.db, sends nothing
# inspect CRM
conda run -n myenv python -c "import sys;sys.path.insert(0,'codebase');from modules.economy import ledger;print(len(ledger.list_table('prospects')))"
```
Push to FireFlow (server up first: `cd $FIREFLOW_ROOT/backend && npm start`). Mint a fresh JWT each session (1 h) from `/api/auth/login` as `pie_operator` using `backend/.pie_operator`; then `POST /api/prospects/import` with `{"items":[{"company":"X","problem":"supplier discovery"}]}` and `GET /api/metrics/funnel`.
**Rules:** seeds live in `revenue_job.py:SEEDS` (real 2026 evidence, source-tagged) — **never invent companies**. PILOT/OUTREACH = cleared for contact lookup + human approval; drafts via `outreach.draft_message`; sends only through `/api/outreach` approve→send. Signature auto-appends from `backend/.sender_identity`. Live Udyam/GeM/ONDC connectors deferred.
[LOOPHOLE INT-02 · S1] This runbook uses a shared human-style operator login; move to a scoped agent account. [/LOOPHOLE]

## 4. Intended end-to-end flows

```
REVENUE_DISCOVERY_JOB  India → search (manufacturing, engineering, export, industrial services, research, AI/data needs)
   → collect public evidence → infer ONE concrete problem → estimate value → estimate service cost
   → create opportunity → challenge → rank → TOP-20 opportunities, TOP-20 prospects, TOP-5 sellable offers
OUTREACH_JOB           approved prospect → personalized proposal → permitted channel → send → track → classify → follow-up within policy
DELIVERY_JOB           accepted → contract → (escrow) → project → tasks → workers/agents → verification → settlement → feedback → PIE learning
```
Status: discovery ✅ (seeded), outreach ✅ (API, human-gated), delivery bridge ✅; **an unattended scheduler running these three jobs is ❓**.

## 5. Targets & metrics

- **Launch metric:** `time_to_first_revenue` (not downloads/posts/GMV).
- **Funnel:** prospects → researched → contacted → responses → meetings → proposals → pilots → won → revenue → cost → gross margin → worker payout → repeat customers → LTV.
- **Cadence goals (adopted from planning):** 20 qualified prospects/day → 5 personalized offers/day → 1 paid pilot → automated delivery → repeat → **10 independently acquired paying customers with positive contribution margin, without manual service**.
- **Experiments to run:** offer A/B, price A/B, industry A/B, message A/B, delivery-time A/B, pilot-size A/B — store hypothesis / experiment / population / result / confidence; kernel learns patterns (e.g., supplier-intelligence outperforms generic AI automation for manufacturing).

## 6. Suggestions & loopholes (inline index)

[SUGGESTION REV-01 · P0] Run a time-boxed Revenue Sprint; no new modules until the first paid pilot. [/SUGGESTION]
[SUGGESTION REV-02 · P0] Add **GeM-bid CSV import** and public trigger-event collectors before any scraper; Udyam stays human-assisted. [/SUGGESTION]
[SUGGESTION REV-03 · P0] Agent-first delivery with human QC; measure cost per verified record. [/SUGGESTION]
[SUGGESTION REV-04 · P1] QC primitives (duplicate blind assignment, gold records, spot-check, SLA/refund). [/SUGGESTION]
[SUGGESTION REV-05 · P1] Label small-N findings `HYPOTHESIS`; use sequential stopping. [/SUGGESTION]
[SUGGESTION REV-06 · P0] Resolve outreach transport + compliance (DPDP, deliverability, opt-out) before first send. [/SUGGESTION]
[SUGGESTION REV-08 · P1] Calibrate the pain score against outcomes. [/SUGGESTION]
[SUGGESTION REV-09 · P2] Productize recurring "price watch"/"catalogue refresh". [/SUGGESTION]
[SUGGESTION REV-10 · P2] Tag ledger rows by owning Unit so personal job EV never mixes with company economics. [/SUGGESTION]
[SUGGESTION STR-03 · P1] Choose one ICP and three outcome SKUs; only 2 of ~13 listed services have templates. [/SUGGESTION]
[SUGGESTION JOB-01 · P1] Turn the ±3 h overlap hard-gate into a soft score with an experiment arm. [/SUGGESTION]
[SUGGESTION JOB-02 · P1] Build employer discovery next (company → hiring team → jobs → stack → decision-maker → channel). [/SUGGESTION]
[SUGGESTION JOB-03 · P1] Define "submit" as assisted submission (human clicks), never a browser bot. [/SUGGESTION]
[SUGGESTION JOB-04 · P1] Test that tailored variants contain no claim without an evidence pointer. [/SUGGESTION]
[VERIFY REV-01] Funnel numbers from `GET /api/metrics/funnel`; any sent/replied/paid records? [/VERIFY]
[VERIFY REV-06] Is `send` a real transport? provider/domain/caps? [/VERIFY]
[VERIFY OPS-07] Which LLM/provider runs the agent; is model cost included in `check_margin`/unit economics? [/VERIFY]
