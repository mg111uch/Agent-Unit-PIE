# Roadmap — Master (Level 1)

> Unimplemented / unproven work across PIE and FireFlow, consolidated from the four planning chats and the module docs. Module-level `roadmap.md` files (now supplied beside each README) hold finer detail; this file is the cross-module view. Compiled 2026-10-19.
> Status marks: ✅ shipped · 🟡 partial · ⬜ not built · ⛔ frozen/locked · ❓ unknown (ask coding agent). IDs refer to `03_loopholes_and_suggestions.md`.

## 1. Direction in one screen

**Stop feature expansion. Build and prove the closed loop that touches real money:**
`PIE finds a paying B2B problem → FireFlow executes → customer pays → ledger reconciles → PIE learns.`
The project's own words: until that loop is autonomous, "the marginal value of another UI feature is much lower than making the PIE → FireFlow → money → evidence → PIE loop actually autonomous."

Horizons (not phases — these are priorities, re-rank every iteration):

| Horizon | Theme | Contents |
|---|---|---|
| **Now** | Safety + proof + first rupee | doc fixes (DOC-01/02/03, DBT-01/02/03) · Loop Proof (INT-01/02/06) · money safety (FIN-01/02/04/05, OPS-01/02/03) · Revenue Sprint (REV-01…07, STR-03/05) |
| **Next** | Repeatability | QC + deliverable assembly · approval inbox · employer discovery (jobs) · real city feeds + scale-invariance · relation retrievers · compressed economic API |
| **Later** | Scale & leverage | recurring SKUs · worker pool growth · data marketplace (demand-first) · compute exchange (demand-first) · capital reinvestment · simulator sector economy |
| **Locked** | Moonshot | industrial pathfinder beyond services→components, space industry, cislunar, lunar; Civ-style game layer; public marketplace |

## 2. Closed-loop gates (replace "feature stages" as the measure of progress)

| Gate | Definition (all must hold) | Status |
|---|---|---|
| **G0 Loop Proof** | one real test-mode task + payment crosses transport → kernel event → signal → retrievable by PIE; replay is a no-op; actor = agent account | ❓/⬜ |
| **G1 First paid pilot** | PIE-found prospect → human-approved outreach → proposal accepted → delivered → payment recorded in ledger → PIE receives actual result | ❓ (no doc records one) |
| **G2 One customer, ten tasks** | 10 successful deliveries, positive contribution margin | ⬜ |
| **G3 Acquisition→delivery automated** | PIE discovers → FireFlow acquires → workers/agents execute → agent validates → automatic delivery | ⬜ |
| **G4 Multi-customer, no manual ops** | same workflow, several customers | ⬜ |
| **G5 Reinvest** | profitable workflow funds the next workflow | ⬜ |
| **Benchmark** | **10 independently acquired paying Indian customers, end-to-end execution, positive contribution margin, without you performing the service** | ⬜ |
| **C1 Real city data** | ≥10 real series per city, placeholder share reported | ⬜ |
| **C2 Scale invariance** | policy direction stable at 400 / 2k / 10k agents | ⬜ |
| **C3 OOS forecast** | held-out historical indicators reproduced within stated tolerance | 🟡 (baseline pop err 0.036 at cap 400) |
| **C4 Promotable finding** | multi-seed + falsify passed → first finding above HYPOTHESIS | ⬜ |
| **J1 First interview / J2 first offer** | job loop yields real outcomes; funnel recorded | ❓ |

## 3. Work tracks

### 3.1 Loop & plumbing (Now)
- FireFlow **outbox → PIE poller/webhook → `kernel_bus`**, idempotent, DLQ, replay (INT-01).
- Dedicated **agent account/scoped key** for PIE; `actor_type` on every mutation (INT-02).
- Version stamps (`app@commit`, `fee_policy_version`, `offer_template_version`) on economic findings (INT-06).
- CLI-proxy contract tests, timeouts, `UNSCORED` fallback (INT-03); ownership map `market.db` vs FireFlow (INT-04).
- ≤15-verb **economic API** toolset for the agent (INT-05): discover_prospects, get_prospect, create_opportunity, score_opportunity, create_offer, create_outreach, record_response, create_proposal, create_contract, create_project, create_task, verify_result, get_settlement, get_unit_economics, record_learning.
- Unattended **scheduler** for REVENUE_DISCOVERY_JOB → OUTREACH_JOB (draft only) → DELIVERY_JOB with a daily digest to the human ❓.

### 3.2 Revenue (Now → Next)
- Revenue Sprint cadence: 20 qualified prospects/day → 5 offers/day → 1 paid pilot; metric `time_to_first_revenue`.
- Top-of-funnel: GeM bid CSV import, trigger-event collectors, association directories; Udyam human-assisted; ONDC later (REV-02).
- One ICP + three outcome SKUs; service templates beyond the 2 seeds (competitor/price intelligence, catalogue/data cleaning, lead lists, document extraction, AI evaluation, Indic-language data) (STR-03).
- QC primitives, accuracy SLA, **deliverable assembly**, **customer portal** (REV-04/07).
- Pain-score calibration; recurring "price watch" SKU; personal vs company accounting (REV-08/09/10).
- Customer pipeline gaps: *negotiation* and *repeat* stages ⬜; LTV/repeat metrics ❓.
- Worker pool: passive path "earn by completing AI-assisted business tasks" (company research, website verification, price checking, catalogue verification, annotation, AI evaluation); referrals **after** demonstrated earnings.

### 3.3 Money & compliance (Now)
- `MONEY_MODE`, global kill switch, aggregate caps (FIN-01); no-escrow first-customer path + counsel review (FIN-02); invoices/GST/TDS (FIN-03); durability + restore drill + Postgres decision (FIN-04); reconcile against provider statements + aging (FIN-05); worker welfare transparency (FIN-06); multi-currency for exports (FIN-07).
- Compliance as substrate: gig-worker classification/records/benefits rails; DPDP-grade consent/purpose/retention for data and contacts [verify current rules/timelines].
- **Settlement completeness (from planning):** 8 payment states `pending/authorized/captured/settled/failed/refunded/disputed/reversed` ❓; DB-level invariants (no double claim, verified XOR cancelled) ❓ (FIN-08).

### 3.4 Sensors & trust (Next)
Independence tests incl. referral-graph check (SEN-01); gold audits + decay (SEN-02); pay-on-verification (SEN-03); coarse geography/retention (SEN-04). Agent security model fully realized: `agent identity → organization → role → allowed tools → resource scopes → financial limit → approval policy → time limit → audit trail`, enforced server-side (🟡).

### 3.5 Kernel & cognition (Next)
Relation/hierarchy retrievers via the city graph (KRN-02) · activation-debt reporting & pruning (KRN-01) · claim-strength ladder (KRN-06) · SQLite concurrency (KRN-04) · re-verify manual (KRN-05) · gate false-negative measurement (KRN-03) · compression min-support (KRN-07) · formal 14-step city-twin workflow (INGEST→…→PIE DECISION) instead of one slice · `promote --keep`.

### 3.6 City twins & simulation (Next/Later, small parallel slice)
Real feeds (TWN-01) · VOI-driven collection (TWN-02) · third-city generality test (TWN-03) · invalidated-sim rerun queue (TWN-04) · weighted representative agents + scale invariance (SIM-01) · param-set identity (SIM-02) · sector-structured economy / eco_sim fit (SIM-03) · capability vector + Pareto (SIM-04) · hybrid macro/micro (SIM-06) · policy object completeness · simulator realism backlog (seasonal yields, soil degradation, weather, pollution, pathfinding, communities/cities, conflict, new agents, geospatial map — see `populaDyn_simu/README.md` §5) · externalized YAML simulation definitions + generic resource system.

### 3.7 Job module (Next)
Soft timezone score + US-hours experiment arm (JOB-01) · employer discovery + contact channel + enrichment (JOB-02) · Workable/Recruitee adapters · assisted submission (JOB-03) · evidence-binding tests (JOB-04) · interview prep, offer tracking, actual-comp feedback into learning · `require_human_for` list (salary negotiation, legal attestation, demographic questions, employment contract) ❓ · **generalize**: Candidate / Business / AI Agent all as economic units so FireFlow supports job-for-person, contract-for-freelancer, task-for-worker, project-for-business, task-for-AI-agent — a labor-and-opportunity matching engine.

### 3.8 App & UX (Now, minimal)
**Approval inbox** (money, outreach, proposals, job outreach, agent needs-approval) + risk tiers (STR-05); customer portal (REV-07); everything else in the social surface stays frozen. Upgrade/audit Next.js (OPS-05).

### 3.9 Ops (Now)
Backups, supervisor, health, alerting (OPS-01) · CI (OPS-02) · secrets (OPS-03) · hash-chained audit incl. `--force` overrides (OPS-04) · env-var paths (OPS-06) · LLM budgets/cost logging (OPS-07).

### 3.10 Docs (Now)
DOC-01…07, DBT-01/02/03; supply the missing docs (AGENTS.md, roadmaps, status files, prompt fragments, stock/eco_sim docs) or digests.

### 3.11 Debate (Later)
Fix paths/vocab/chroma (DBT-02/03/05) · rewrite compiler on top of `topic_ops batch` (DBT-04) · reuse for opportunity challenge (DBT-08) · multi-user belief stores · behavior/soft-science layers stay sandboxed hypotheses (STR-07).

## 4. Frozen / locked, with unlock criteria

| Item | State | Unlock criteria |
|---|---|---|
| Social features, elaborate frontend, communities, complex prediction markets | ⛔ freeze | only if they directly serve the revenue loop |
| Ride-hailing, full e-commerce | ⛔ | after marketplace unlock; ride-hailing only as a logistics capability |
| Public marketplace launch | ⛔ | ≥3 recurring workflows, ≥20 workers earning monthly, ≥10 customers (STR-06) |
| Public compute exchange | ⛔ | real workload in hand **and** node attestation, heartbeat, benchmark, scheduling, job isolation, result verification, failure handling, power/network economics, provider payout, data confidentiality |
| Data marketplace as product | ⛔ | customer requirement first (collect → verify → deliver → pay), then productize recurring datasets |
| Industrial flywheel (B2B intelligence → supplier graph → component brokerage → prototype sourcing → research commercialization → own products → manufacturing) | ⛔ later | revenue exists; PIE must *discover* (rising demand + import dependence + margin + accessible manufacturing + skills + manageable capex), not decide, e.g., "robotics parts" |
| Moonshot ladder (city → India twin → technology graph → space → cislunar → lunar) | ⛔ LOCKED | ≥10 paying customers positive margin; ≥1 city twin validated OOS on real feeds; repeatable recurring workflow (STR-02) |
| Civ-style game layer | ⛔ | after C3/C4 |

## 5. Recommendation ledger (every idea from the four planning chats)

Legend as above. **Src:** FI = `FeatureIdeas`, FX = `FixesIssues`, PP = `PhasePlan` response, JB = `PlanFixes2` (jobs), SD = `SimDvptPhases`.

### 5.1 FI — FireFlow review
| # | Recommendation | Status | Where |
|---|---|---|---|
| FI-1 | Hard boundary: PIE cognition / FireFlow execution; no second brain | ✅ | FireFlow README, master §3 |
| FI-2 | `pie_fireflow_gateway` (envelopes, receipts, RBAC) | ✅ (transport 🟡) | fireflow_app §3.6 |
| FI-3 | Authoritative ledger: debit/credit, provider id, contract id, actor, idempotency, evidence; 8 states | 🟡 states ❓ | FIN-08 |
| FI-4 | Settlement engine; idempotent money ops; DB invariants | ✅ / ❓ invariants | fireflow_app §3.3 |
| FI-5 | Don't launch as a marketplace; AI-operated B2B service first | ✅ strategy | economy §1 |
| FI-6 | Wedge = AI Industrial Intelligence Service (13 service types) | 🟡 2 templates | STR-03 |
| FI-7 | Execution swarm: decompose → claim → auto QC → cross-verify → assemble → approve → pay → learn | 🟡 decompose/claim/pay ✅; QC/assembly ❓ | REV-04/07 |
| FI-8 | Evidence-based opportunity: evidence types, confidence, age, count, diversity, EV | ✅ | economy §2.1 |
| FI-9 | `customer_pipeline` prospect→…→repeat | 🟡 negotiation/repeat ⬜ | fireflow_app §3.7 |
| FI-10 | `unit_economics` (12 cost/revenue lines; kill when revenue↑ contribution↓) | 🟡 margin gate/fiscal ✅; AI/support/CAC lines ❓ | OPS-07 |
| FI-11 | Sensor anti-fraud; per-capability reputation | ✅ / collusion 🟡 | SEN-01 |
| FI-12 | `dataset_license` first-class (rights→consent→transform→annotate→QA→license→restrict→revoke→provenance) | ✅ core; full chain ❓ | fireflow_app §3.5 |
| FI-13 | Compute exchange launch-late + 10 prerequisites | 🟡 / ⛔ public | §4 |
| FI-14 | Agent security model (8 layers) | 🟡 | §3.4 |
| FI-15 | Business agents as event-driven workers | ✅ events; PIE-in-loop ❓ | fireflow_app §3.4 |
| FI-16 | Truth hierarchy (6 tiers) | ✅ | twins §3 |
| FI-17 | Cold start: first paying customer before users; referrals after earnings | 🟡 | REV-01 |
| FI-18 | Hunt India for agent-friendly problems | 🟡 seeds | REV-02 |
| FI-19 | Industrial flywheel after revenue | ⛔ | §4 |
| FI-20 | Closed-loop milestones M1–M5 | ✅ adopted (G1–G5) | §2 |
| FI-21 | Freeze list | ✅ adopted | STR-01 |
| FI-22 | Compliance in substrate (Social Security Code, DPDP) | 🟡 | FIN-03/06 |

### 5.2 FX — Kernel revival & city twins
| # | Recommendation | Status | Where |
|---|---|---|---|
| FX-1 | Kernel events as universal currency | 🟡 | kernel §1 |
| FX-2 | `KernelEvent` schema fields | 🟡 `economic_delta`/causes/effects ❓ | kernel §1 |
| FX-3 | `kernel_activation_registry` | ✅ 66 entries | kernel §3.4 |
| FX-4 | Revive in order: identity → observations → signals → patterns | 🟡 (identity ✅, rest via slices) | KRN-01 |
| FX-5 | Causal engine = candidates only | ✅ policy | master §5.3 |
| FX-6 | Retrieval cascade unit→state→events→signals→patterns→relations→history | 🟡 relations ⬜ | KRN-02 |
| FX-7 | Compression only after event flow works | ✅ per-sim | kernel §3.2 |
| FX-8 | City twin at zone/ward level with representative agents (~10,000) | 🟡 cap 400 | SIM-01 |
| FX-9 | One generic `city_twin`, `city_id` config | ✅ | twins §3 |
| FX-10 | `CityState` + per-field provenance | ✅ | twins §3 |
| FX-11 | Parallel Kanpur/Delhi adapters | ✅ static; feeds ⬜ | TWN-01 |
| FX-12 | Data model first, no 3D | ✅ | twins §1 |
| FX-13 | Calibration engine | ✅ | twins §3 |
| FX-14 | Historical snapshots 2011→2025; train/lock/forecast | ✅ sparse | twins §3 |
| FX-15 | Structured `Policy` objects (8 fields) | 🟡 | twins §5 |
| FX-16 | Kanpur vs Delhi contrast lab | ✅ (null verdict) | twins §3 |
| FX-17 | `policy_experiment_registry` | ✅ | twins §3 |
| FX-18 | `twin_versioning` | ✅ | twins §3 |
| FX-19 | Relations as city graph | ⬜ | twins §6 |
| FX-20 | Kernel as FireFlow economic memory | 🟡 shape-only | INT-01 |
| FX-21 | City twins consume FireFlow as sensor | 🟡 `flywheel.py` slice | twins §3 |
| FX-22 | Compression for scale (events→signals→patterns→semantic) | 🟡 | KRN-07 |
| FX-23 | 14-step city-twin loop as formal workflow | 🟡 one slice | §3.5 |
| FX-24 | Seven build targets (bus, registry, adapter, city_twin, ingestion, calibration, policy experiment) | ✅×6, ingestion 🟡 | — |
| FX-25 | 90-day objective: calibrated, versioned, uncertainty-aware models | 🟡 | C1–C4 |
| FX-26 | Capability vector + Pareto | 🟡 Pareto only | SIM-04 |
| FX-27 | Moonshot ladder | ⛔ LOCKED | §4 |

### 5.3 PP — Revenue acquisition
| # | Recommendation | Status | Where |
|---|---|---|---|
| PP-1 | `revenue_acquisition` loop | ✅ built | economy §2.2 |
| PP-2 | FireFlow = infrastructure, PIE = sales machine | ✅ | economy §1 |
| PP-3 | 15 sellable service types | 🟡 2 templates | STR-03 |
| PP-4 | Prospect engine: Udyam, GeM, ONDC, public sites + trigger events | 🟡 stubs | REV-02 |
| PP-5 | Search for pain, not companies; prospect score | ✅ | economy §2.2 |
| PP-6 | `customer_evidence` object | ✅ | economy §2.2 |
| PP-7 | Outcome offer, fixed price/scope/deadline; price discovered by experiment | ✅ | economy §2.2 |
| PP-8 | Service template before selling | ✅ | economy §2.2 |
| PP-9 | `outreach_agent` + response classes + rules | ✅ | economy §2.2 |
| PP-10 | Continuous India-wide search, geography as a variable | 🟡 | REV-02 |
| PP-11 | Prospect→task bridge | ✅ proposal launch | fireflow_app §3.7 |
| PP-12 | Passive worker pool | 🟡 | §3.2 |
| PP-13/14 | Data/compute demand-first | ✅ policy | §4 |
| PP-15 | `revenue_metrics`, `time_to_first_revenue` | ✅ (repeat/LTV ❓) | fireflow_app §3.7 |
| PP-16 | Sales-process experiments | ✅ min-N A/B | REV-05 |
| PP-17 | Revive kernel through sales (obs→event→signal→pattern→hypothesis) | 🟡 | INT-01 |
| PP-18 | Tiny compressed economic API (15 verbs) | ⬜/❓ | INT-05 |
| PP-19 | REVENUE_DISCOVERY / OUTREACH / DELIVERY jobs | 🟡 scheduler ❓ | economy §4 |
| PP-20 | 30-day goal / 10-customer benchmark | ❓ | §2 |
| PP-21 | Bootstrap objective: validated contribution per unit of agent effort | 🟡 add to scoring | master §0 |
| PP-22 | Customer-discovery hierarchy L1–L5 | 🟡 | economy §1 |

### 5.4 JB — Job agent
| # | Recommendation | Status |
|---|---|---|
| JB-1 | `candidate_twin` from `resume.md` with evidence pointers | ✅ |
| JB-2 | Ingestion: RemoteOK, WWR, Greenhouse, Lever, Ashby (+Workable, Recruitee) | ✅ 6 adapters; Workable/Recruitee ⬜ |
| JB-3 | Normalizer incl. `eligible_countries`, timezone | ✅ (field coverage ❓) |
| JB-4 | Fit engine: hard constraints + components; FIT/CONFIDENCE/MISSING/EVIDENCE; 4 verdicts | ✅ verdicts; confidence/missing ❓ |
| JB-5 | Application optimizer: resume variant, cover letter, answers, portfolio, recruiter message | 🟡 variants ✅ |
| JB-6 | Tracker state machine | ✅ |
| JB-7 | Job-search learning + experiments (H1–H3) | ✅ learning; H3 blocked by gate (JOB-01) |
| JB-8 | Employer discovery | ⬜ |
| JB-9 | Direct outreach with follow-up/opt-out | ✅ / follow-up ❓ |
| JB-10 | No LinkedIn automation | ✅ policy |
| JB-11 | Human-approval boundary + `application_policy` | ✅ submit gate |
| JB-12 | Job economics (income, P(interview), P(offer), cost, stability, growth, network/strategic value) | 🟡 EV/application |
| JB-13 | Generalize to person/business/agent matching | ⬜ |
| JB-14 | 13 DB objects (candidates … job_experiments) | 🟡 interviews/offers/contacts/job_events ❓ |
| JB-15 | Interview prep → offer → actual comp → kernel | ⬜ beyond outreach/tracker |

### 5.5 SD — Simulator plan: see `populaDyn_simu/README.md` §5 (communities/cities, conflict, civilization, visualization, seasonal yields, soil, weather, pollution, pathfinding, new agents, world map, game layer).

### 5.6 Original master-README vision items
Ingestion engine ❓ · Behavioral Intelligence ❓ · Soft-sciences hypothesis systems ❓ · Spatial Intelligence ❓ · capital_flow / corruption / gdp / investment engines (🟡/❓) · Personal Wealth Intelligence ❓ · Corruption & public-flow analysis ❓ (guardrails: STR-07) · Stock intelligence ✅ (separate) · Self-evolution mechanisms 🟡. None of these is confirmed by supplied docs; treat as **vision until the coding agent confirms** (master §6).
