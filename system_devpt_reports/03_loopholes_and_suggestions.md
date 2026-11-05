# Loopholes & Suggestions Register (Level 1)

> Compiled 2026-10-19 by cross-reading all supplied docs. **Evidence = which doc says it.** *Ask* = a question for the **coding agent** (who has the code) — the user pastes the answer into the next session; no code is ever pasted.
> Severity: **S1** can lose money/data, create legal exposure, or block revenue · **S2** important · **S3** hygiene. Priority: **P0** next iteration · P1 soon · P2 later · P3 opportunistic.
> Statements about Indian law/tax/regulation are *flags to verify with a lawyer/CA*, not advice.

## Index

| Area | IDs |
|---|---|
| A. Integration & plumbing | INT-01 … INT-07 |
| B. Money, ledger, compliance | FIN-01 … FIN-08 |
| C. Revenue & go-to-market | REV-01 … REV-10 |
| D. Sensor / data trust | SEN-01 … SEN-04 |
| E. Kernel & cognition | KRN-01 … KRN-08 |
| F. Simulation validity | SIM-01 … SIM-07 |
| G. Digital twins | TWN-01 … TWN-05 |
| H. Debate engine | DBT-01 … DBT-08 |
| I. Job module | JOB-01 … JOB-06 |
| J. Security & operations | OPS-01 … OPS-07 |
| K. Documentation hygiene | DOC-01 … DOC-07 |
| L. Strategy & product | STR-01 … STR-07 |

**Next-iteration P0 set:** INT-01, INT-02, FIN-01, FIN-02, REV-01, REV-02, REV-03, REV-06, OPS-01, DBT-01, DOC-01, STR-01.

---

## A. Integration & plumbing

**INT-01 · S1 · P0 — The loop is closed in tests/adapters, not on live transport.**
*Evidence:* economy `event_adapter` "translates `PaymentSettled` payloads (score_cli proxy pattern, **no external calls**)"; twin `city_adapters` "shaped/static inputs only, no network"; FireFlow scoring is a CLI proxy; PIE→FireFlow pushes are manual HTTP with a 1 h JWT.
*Risk:* PIE may "learn" only from hand-fed payloads; real settlements never reach the kernel; every loop-closure claim is unproven.
*Fix:* define one transport — FireFlow **outbox table** (event id = idempotency key) → PIE poller or webhook → `kernel_bus.publish_event`; at-least-once delivery, dedup on event id, dead-letter queue, replay command. Acceptance: one real test-mode task+payment appears as kernel event → `capital_flow` signal → retrievable by `kernel_retrieve`, and replaying the same event changes nothing.
*Ask:* "Which process, if any, moves FireFlow ledger/task events into `kernel_bus` unattended? What happens if it is down for an hour?"

**INT-02 · S1 · P0 — PIE acts through a shared human-style operator login.**
*Evidence:* economy runbook mints a JWT for `pie_operator` (password file, expires in 1 h) while FireFlow already ships **Agent accounts** (API keys bound to AI Agent units, spend caps) and an RBAC gateway.
*Risk:* audit trail can't distinguish human from agent; unattended jobs fail at expiry; the operator account is over-privileged vs the planned model (`agent → org → role → allowed tools → resource scopes → financial limit → approval policy → time limit → audit`).
*Fix:* create a dedicated `pie_revenue_agent` account/key with scopes `prospects:import, proposals:draft, jobs:import, receipts:write`; **no** `outreach:approve/send`, no ledger, no payout destination change. Log `actor_type` on every mutating call.
*Ask:* "Which principal does `revenue_job` push with? Does every ledger/outreach/approval row store actor type and id?"

**INT-03 · S2 · P1 — Node↔Python coupling by CLI subprocess.**
*Evidence:* `score_cli.py`, `fit_cli.py` invoked by FireFlow ("thin proxy"); `conda run` gotchas documented.
*Risk:* latency, env drift, swallowed errors, no timeout/versioning; a slow CLI can stall request threads.
*Fix:* contract tests on CLI I/O JSON (extend the drift-guard idea to scoring I/O), hard timeouts, explicit `UNSCORED` verdict on failure, version field in responses; later a local HTTP service.
*Ask:* "What does FireFlow return when the PIE CLI times out or the conda env is missing?"

**INT-04 · S2 · P1 — Two stores for overlapping economic objects.**
*Evidence:* PIE `market.db` holds prospects, fiscal_runs, capital books and a ledger ("one store only — no parallel books" is a FireFlow principle); FireFlow also has a Prospect CRM, proposals and an authoritative ledger.
*Risk:* divergent prospect status and money records; ambiguity over which is the book of record.
*Fix:* declare ownership — **FireFlow = system-of-record for money, CRM state, tasks**; `market.db` = PIE working set/advisory/simulation books. Define ID mapping (`pro_<hash>` ↔ FireFlow id) and one sync direction per field.
*Ask:* "After `POST /api/prospects/import`, does PIE store the FireFlow ids? Who updates prospect status after a reply?"

**INT-05 · S2 · P1 — No single compressed economic tool surface for the LLM.**
*Evidence:* PhasePlan chat proposes ≈15 verbs; the project's own dev loop deliberately shrank its tool surface; the gateway exists but a unified toolset isn't documented.
*Fix:* one `economic_*` toolset (≤15 tools) in the agent runtime mapping to gateway calls; deterministic engines enforce transitions (same philosophy as `develop.*`).
*Ask:* "List the tools the agent can call today that touch FireFlow/economy, and which are raw endpoints."

**INT-06 · S2 · P1 — FireFlow findings lack lineage/validity; fee policy is runtime-changeable.**
*Evidence:* per-sim lineage exists for simulators, not for the app; "Fee policy rails … runtime-changeable, no redeploy".
*Risk:* a conversion/margin finding learned under rake 5% stays `ACTIVE` after the policy changes.
*Fix:* treat FireFlow as a *domain source* with `app@commit` + `fee_policy_version` + `offer_template_version` stamped on every economic finding; policy change → concept-level `HISTORICAL` via the existing validity machinery. Kernel tag stays `fireflow_app`.
*Ask:* "Do revenue findings written to the kernel carry fee-policy and template versions?"

**INT-07 · S3 · P2 — Two company-twin implementations.**
*Evidence:* PIE `CompanyTwin` (snapshot→ledger) vs FireFlow *enterprise twin* (derived task/cashflow/workforce/reputation/pipeline + owner-reported feeds).
*Fix:* one versioned twin schema with truth tiers; FireFlow = data plane, PIE = model plane.
*Ask:* "Do both twins use the same truth-tier enum and Unit ids?"

---

## B. Money, ledger, compliance

**FIN-01 · S1 · P0 — Payment-provider reality and a global kill switch are undocumented.**
*Evidence:* settlement pipeline "authorize→provider→settle→reconcile→payout→report"; "provider failures settle nothing" — but no provider, sandbox/live flag, or payout rail is named.
*Fix:* explicit `MONEY_MODE = disabled|test|live`; **global kill switch** and **aggregate daily cap at ledger level** (not only per-agent); provider adapter interface with a recorded sandbox run; payout destination changes require human re-approval.
*Ask:* "Which payment/payout providers are wired, in what mode? Is there a global switch that stops all outbound money?"

**FIN-02 · S1 · P0 — Holding customer funds in escrow may be a regulated activity.**
*Evidence:* escrow = "funds lock on acceptance, release on verified completion"; target pilots are ₹2–10k.
*Fix:* **[verify with counsel/CA]** before live funds. For the first ~10 customers use the *no-escrow path*: fixed price, advance or on-delivery invoice through ordinary bank/UPI, recorded in the ledger by human approval; use a licensed provider's native split/route features later. Keep escrow code, gate it behind `MONEY_MODE=live` + legal sign-off.
*Ask:* "Can a contract run end-to-end with `escrow=off` and manual payment recording?"

**FIN-03 · S2 · P1 — No documented GST invoicing / TDS / tax reporting record.**
*Evidence:* FeatureIdeas lists "tax/reporting record" as a settlement step; the settlement pipeline has a `report` step of unknown depth; `welfare head` exists in fee policy.
*Fix:* invoice object (GSTIN, HSN/SAC, tax lines), tax columns on ledger entries, worker-payout TDS flag, CA export. **[verify rates/applicability]**
*Ask:* "What does the settlement `report` step emit? Is there an invoice or tax line anywhere?"

**FIN-04 · S2 · P1 — SQLite as the financial book of record.**
*Evidence:* "SQLite database (included)"; webhooks + retries + human approvals + jobs write concurrently.
*Fix:* WAL mode + busy timeout + single-writer discipline; nightly encrypted backups with a restore drill; scheduled *ledger self-audit* (Σdebits = Σcredits, no orphan holds); Postgres migration path decided **before** `MONEY_MODE=live`.
*Ask:* "What are the SQLite pragmas, backup schedule, and has a restore ever been tested?"

**FIN-05 · S2 · P1 — Reconciliation target is unclear.**
*Evidence:* pipeline has `reconcile`; commerce pipeline reconciles "estimate versus actuals".
*Fix:* reconcile ledger vs **provider statements** (not only internal estimates); aging report of unreconciled items; alert on any unreconciled > 24 h.
*Ask:* "Against what does `reconcile` compare — provider statements or internal records?"

**FIN-06 · S3 · P2 — Gig/platform-worker welfare obligations are only a "welfare head".**
*Evidence:* Social Security Code in force (planning chat says Nov 2025) — registration, benefits, aggregator contribution.
*Fix:* **[verify statutory rate, thresholds, registration]**; show workers their fee/welfare split per payout; worker classification stored per engagement (already: gig/contract/trial).

**FIN-07 · S3 · P3 — Multi-currency for export orders.**
*Evidence:* export orders carry forex estimates; ledger is paise-only.
*Fix:* explicit `currency` + FX-rate source on ledger rows before first export order.

**FIN-08 · S2 · P1 — State-machine invariants must be database constraints, not agent behavior.**
*Evidence:* planning chat requires "worker cannot claim same task twice", "task cannot be verified and cancelled", "payment cannot settle twice", 8 payment states; FireFlow docs state idempotency and a pending→settled machine but not the full set or where it is enforced.
*Fix:* unique constraints/transitions tables enforced in the DB layer; property tests that attempt every illegal transition; add missing states (authorized, captured, failed, refunded, disputed, reversed).
*Ask:* "List the payment states and which invariants are DB-enforced vs application-enforced."

---

## C. Revenue & go-to-market

**REV-01 · S1 · P0 — No documented paid customer.** *(Instrumented 2026-11-02: funnel exposes every stage with its source. Closes on the first paid pilot.)*
*Evidence:* funnel, pain score, templates, outreach, delivery bridge are all built; no doc records a send, reply, pilot or rupee. The stated benchmark is "10 independently acquired paying customers, positive contribution margin, without manual service".
*Fix:* run a **Revenue Sprint** with fixed targets: 20 qualified prospects/day → 5 personalized offers/day (human-approved) → 1 paid pilot; track `time_to_first_revenue` as *the* metric; no new modules until first rupee.
*Ask:* "Give the current funnel numbers from `GET /api/metrics/funnel` (stage counts, responses by class, revenue/cost/margin)."

**REV-02 · S1 · P0 — Top of funnel is 20 hand-curated seeds; live connectors deferred.** *(GeM CSV import shipped 2026-11-02; Udyam/ONDC stay human-assisted.)*
*Evidence:* `revenue_job.py:SEEDS`; `discovery.collect` honestly states Udyam/GeM/ONDC are deferred.
*Fix:* cheapest real sources first — **GeM public bids as CSV import**, public company/news trigger events, industry-association directories — through the existing import endpoints. Udyam search is human-assisted (respect the portal's terms; no CAPTCHA bypass). Priority order = existing explicit demand (tenders/enquiries) → observable pain (expansion, hiring, new product) → recurring industry pain.
*Ask:* "How many prospects have non-seed provenance? Which collectors are live?"

**REV-03 · S1 · P0 — Delivery capacity for the first paid project is undefined.** *(Planned 2026-11-02: executor assignment, capacity plan and cost per verified record in `delivery.py`; real payouts still zero.)*
*Evidence:* worker pool is empty; micro-work splitting and task marketplace exist; "agents execute" but no named executor.
*Fix:* **agent-first delivery** — worker-agent accounts do research tasks; humans only QC at first; measure cost per verified record; recruit a tiny human pool (5–10) from your own network, not a public launch.
*Ask:* "For `supplier_discovery_100`, which actor performs each task and what is cost per verified record so far?"

**REV-04 · S2 · P1 — QC for research deliverables is not documented.** *(Delivered 2026-11-02: blind duplicates, gold records, sampling, confidence, SLA/refund in `modules/economy/qc.py`.)*
*Evidence:* tasks carry a verification rule; sensor confirmations exist; no mention of redundancy/gold tasks/sampling.
*Fix:* QC primitives — duplicate blind assignment with consensus, golden records, spot-check sampling ratio, per-record confidence column, accuracy SLA + refund rule tied to dispute records.
*Ask:* "How is a delivered batch checked for correctness before the customer sees it?"

**REV-05 · S2 · P1 — Small-N statistics.**
*Evidence:* min-N A/B in `revenue.py`; kernel patterns like "2.5× reply rate" derive from tens of sends.
*Fix:* confirm the min-N value; label any kernel finding from small N as `HYPOTHESIS`; use sequential/Bayesian stopping; don't tune offers on noise.
*Ask:* "What is the min-N and does the kernel store sample size with each revenue finding?"

**REV-06 · S2 · P0 — Outreach transport and compliance before the first send.**
*Evidence:* "draft → human approve → capped send (1/7d) → classified response; unsubscribe auto-opts out"; sender signature from `.sender_identity`; unknown whether `send` is a real transport.
*Fix:* **[verify with counsel]** DPDP applicability to named contacts, TRAI/WhatsApp rules; email only to role/public business addresses; warmed dedicated domain with SPF/DKIM/DMARC; physical postal identity + STOP footer; bounce/complaint handling; no purchased lists.
*Ask:* "Is `send` an actual SMTP/API transport or a state change? Which provider, domain and caps?"

**REV-07 · S2 · P1 — Customer last mile: acceptance and deliverable.** *(Closed 2026-11-03: magic-link `/portal/{token}` accepts a proposal, issues one idempotent invoice, serves the deliverable from the deliverables roots, and an operator payment confirmation writes one ledger tx.)*
*Evidence:* "accept spins up the task + draft contract" (internal action); FeatureIdeas lists "deliverable assembly → customer approval → payment".
*Fix:* a magic-link **customer portal** (view proposal → accept → pay/invoice → download deliverable) + `deliverable_assembly` (XLSX/CSV + methodology note + confidence columns).
*Ask:* "How does an external customer accept a proposal and receive the dataset today?"

**REV-08 · S2 · P1 — Pain score is hand-weighted.**
*Evidence:* geometric mean of six factors with analyst-set inputs; no outcome calibration.
*Fix:* after N outcomes, fit a simple model (logistic) predicting reply/pilot; let the kernel pattern engine propose weight updates; store score-vs-outcome for backtests.

**REV-09 · S3 · P2 — Productize recurring services.**
*Fix:* one-off lists are fragile revenue; monthly *supplier-price watch* / *catalogue refresh* leverage the sensor network + business agent and raise LTV.

**REV-10 · S3 · P2 — Personal (job-search) vs company revenue accounting.**
*Fix:* tag ledger rows with the owning Unit (`person:self` vs `company`) so job EV never inflates company unit economics.

---

## D. Sensor / data trust

**SEN-01 · S2 · P1 — Collusion and Sybil resistance.** Independent confirmation can be satisfied by two cooperating accounts. *Fix:* independence tests — distinct device/geo bucket, account age, **no shared referral chain** (the referral graph already exists), rate limits. *Ask:* "What defines 'independent' in the confirm check?"

**SEN-02 · S2 · P1 — Reliability measures agreement, not truth.** Laplace scores per capability reward consensus. *Fix:* seed **gold observations** and random audits; decay old evidence; minimum-evidence gate before a reporter influences a twin.

**SEN-03 · S3 · P2 — Incentives.** Pay-per-observation invites fabrication. *Fix:* pay on confirmation/verification; clawback via ledger reversal.

**SEN-04 · S3 · P2 — Observation privacy.** Device/geography/evidence are sensitive. *Fix:* coarse geography by default, retention limits, minimization (DPDP).

---

## E. Kernel & cognition

**KRN-01 · S2 · P1 — Activation debt.** Registry at creation: 66 entries, 16/8/42 [INFERRED ACTIVE/PARTIAL/DORMANT]. *Fix:* report the DORMANT count each iteration; mark DEPRECATED any capability with no planned consumer; delete or archive it — dead code misleads agents. *Ask:* "Current registry counts by status?"

**KRN-02 · S2 · P1 — Relation/hierarchy retrievers dormant** *(Closed 2026-11-02: `relation_retriever.py` over typed city-graph edges + `retrieval_engine.retrieve_relations`.)* while the master principle and the city graph need them. *Fix:* activate via the city graph first (factory `requires` electricity, road `serves` cluster, worker `employed_by` firm, ward `contains` neighborhood, policy `affects` industry), then extend the cascade unit → relation.

**KRN-03 · S2 · P2 — Contradiction-gate error rates are unmeasured.** Symbolic Jaccard+negation gate misses paraphrases. *Fix:* measure false-negative rate with the adversarial eval; optional embedding *candidate retrieval* in a sidecar (never the decider).

**KRN-04 · S2 · P1 — `kernel.db` write concurrency.** *(Closed 2026-11-02: `busy_timeout` on RO/RW connections; `doctor` prints journal mode, timeout and a write probe.)* Server, CLI scripts, hot-reload and loops share one SQLite file. *Fix:* WAL + busy timeout + one writer queue; surface "database is locked" in `doctor`.

**KRN-05 · S2 · P1 — Manual stale.** *(Closed 2026-11-02: `usage.md` restamped with the real 14/15 smoke result.)* `usage.md` says *Last verified 2026-08-29*, before the bus/registry/adapters (2026-09-15). *Fix:* re-run smoke (9/9), re-stamp, add bus/registry to the manual.

**KRN-06 · S2 · P1 — Enforce an evidence ladder.** *(Closed 2026-11-02: `hypothesis/claim_strength.py` enforced in `publish_observation`; overstated claims downgrade with reasons.)* Rule today (docs): no finding above `HYPOTHESIS` without multi-seed + falsify. *Fix:* encode `claim_strength ∈ {HYPOTHESIS, REPLICATED, FALSIFICATION_PASSED, VALIDATED_OOS}` in the gate so it cannot be bypassed by prose. *Ask:* "Is the above-HYPOTHESIS rule enforced in code or by convention?"

**KRN-08 · S1 · P0 — Episodic retrieval was process-local (found and fixed 2026-11-01).**
*Evidence:* `episodic_memory.episodes` is an in-memory dict that nothing hydrates on startup; `search_episodic_memory` iterated only that dict, while events themselves *are* persisted in `kernel.db` (`generic_memory`, `memory_type='episodic'`).
*Risk:* a restarted PIE could not retrieve anything it learned in a previous process — the loop looked closed in-process and was open across restarts. This silently defeated G0.
*Fix:* `retrieval_engine._persisted_episodic` reads persisted episodic objects via `memory_engine.list_objects_ro` / `load_object_ro` and scores them alongside in-memory episodes. Verified by `tests/test_loop_proof.py` and a live settlement retrieved from a fresh process.
*Ask:* "Do any other retrievers (pattern/relation/timeline) depend on process-local state the same way?"

**KRN-07 · S3 · P2 — Compression thin support.** *(Closed 2026-11-02: `min_support` config + `n`/`min_support` on consolidated nodes and in search metadata.)* `<2` findings → HISTORICAL, else recomputed `avg_delta`. *Fix:* configurable min support; expose `n` to the LLM with every consolidated node.

---

## F. Simulation validity

**SIM-01 · S1 (for policy claims) · P1 — Scale validity.** *(Closed 2026-11-03: `scale_invariance` holds land per agent constant; 400/2k/10k baselines 1.774/1.773/1.776, policy effect +1.52/+1.58/+1.52%. Direction and level now survive scale-up; domain mismatch is SIM-03.)* Calibration caps (pop 400, skill 1.0) vs real cities with millions of people; planning chat recommended ~10,000 representative agents.
*Fix:* weighted representative agents (each agent = N people, stratified by ward/age/income); **scale-invariance test** (same policy → same direction at 400 / 2k / 10k agents); until then every record stays flagged.
*Ask:* "What is the largest population run that completes, in how long, and does the baseline error hold at that scale?"

**SIM-02 · S2 · P1 — Parameter-set identity.** *(Closed 2026-11-02: `simulation_version.run_key = (sim@commit, param_hash, seed_set)` persisted on `simulation_runs`; contradiction gate compares only within one regime.)* `sim@commit` lineage doesn't change on parameter sweeps; the popula README's own "Problem Restatement" notes two mutation axes (param sweep vs code mutation) writing to one graph.
*Fix:* run key = `(sim@commit, param_hash, seed_set)`; contradiction gate compares only within the same parameter regime. *Ask:* "Is param_hash part of run identity today?"

**SIM-03 · S2 · P1 — Domain mismatch.** *(Phases A–D landed 2026-11-03/05: `domain: agrarian|urban` is a parameter pack on one engine/run-key. Urban pack: workers, manufacturing/service firms, zoned parcels, wage/output labour market, power/water capacity vs demand, congestion-priced transport, municipal budget, and a profit-share channel. Calibration maps real TWN-01 rows to ratios (Kanpur 3 series, Delhi 4); fit on target (firms 1.0%/3.8%, road 1.5%), missing rows null. Promotion gate: 3 seeds × 400/2k/10k + `falsify_policy` (seed shift, ±magnitude, half horizon, placebo) → power capex both cities and Delhi transport are `FALSIFICATION_PASSED` in `popu_sim` (n=37,200). Kanpur transport is `MIXED` (−8.5%…+1.6%) and stays `HYPOTHESIS`: the sign flip is hire-order randomness, not an economic channel. Phase D rejected `eco_sim`.)* popula_dyn was an agricultural ABM; Kanpur/Delhi questions concern manufacturing, transport, water, energy. Water/energy/air remain unmapped.
*Fix:* new mechanisms must clear the same gate; Kanpur transport needs a deterministic hire order before re-testing.

**SIM-04 · S2 · P2 — Capability vector not built.** Contrast lab returns a *null* Pareto verdict (expected with placeholder data — don't over-read). *Fix:* define the City Productive Capability Vector (economic_output, productivity, real_income, employment, industrial_capacity, entrepreneurship, infrastructure_utilization, human_capital, health, education, mobility, housing, water, energy, environment, inequality, fiscal_sustainability, resilience, innovation) and mark which dims are *fed* vs *placeholder*.

**SIM-05 · S3 · P2 — Playable game server may have drifted** from the generic UnitAgent core (the game README still describes farmers/healers/toolmakers/traders and fixed endpoints). *Ask:* "Does `/game` run on the current core? Which behaviors does the UI still assume?"

**SIM-06 · S2 · P2 — Performance path.** Python agent loops won't reach city scale. *Fix:* hybrid — epoch-engine macro layer for scale, ABM for local validation; vectorize hot behaviors.

**SIM-07 · S3 · P3 — Ensemble reporting standard.** Report seeds count, CI width, effect size, falsify pass-rate on every policy finding.

---

## G. Digital twins

**TWN-01 · S1 · P1 — Twin data is mostly placeholder/static.** *(Closed 2026-11-03: 10 `FIELDS` with observed/placeholder/missing coverage, validated ingestion with source+licence+url, and 5 cited rows; Kanpur 3/10 observed, Delhi 4/10, remaining 3 gaps named in `data/twins/series/manifest.json`.)* Placeholders ≤0.35; adapters take shaped static inputs, no network; 2011 census anchors only.
*Fix:* pick ~10 high-value real series per city and feed them first — population by ward, employment by sector, industrial units by district, power supply hours, water (MLD), air quality, road/transport counts, municipal budget lines, master-plan land-use (Delhi DDA MPD-2047, Kanpur KMC pages, smart-city GIS layers are named in the planning chat). **[verify availability/licensing per source]**
*Ask:* "How many CityState fields per city are placeholder vs observed/verified?"

**TWN-02 · S2 · P1 — Use uncertainty to choose what to collect.** Placeholders are already ranges. *Fix:* rank missing fields by the sensitivity grid's effect on policy outcomes (value-of-information) and collect those first.

**TWN-03 · S2 · P2 — Prove "no per-city modules".** *Fix:* acceptance test — add a third small city with config + adapter only, zero code change in `city_twin`.

**TWN-04 · S3 · P2 — Invalidation should queue reruns.** Twin version change retires `v1→HISTORICAL` with changed variables; add `invalidated_simulations` and an auto-rerun queue.

**TWN-05 · S3 · P3 — Split `city_twin.py` (741 lines)** when next touched; deltas only until then.

---

## H. Debate engine

**DBT-01 · S1 · P0 — Doc contradiction that can destroy data.** Debate README: "add new topics in `modules/argu_god/topics/<topic>/graph.json`". Kernel manual: `graph.json` is a **derived view, overwritten on the next mutation; never hand-edit**. *Fix:* debate README must say "add topics with `scripts/topic_ops.py add-node/batch`".

**DBT-02 · S2 · P1 — Path conflict.** Kernel manual: `data/mindmaps/local_user/belief_state.json` and `data/topics/…`; debate README: `modules/argu_god/mindmaps/local_user/…` and `modules/argu_god/topics/…`. If writers and readers disagree, contradiction detection silently never fires. *Ask:* "Print the live path of `belief_state.json`, `interaction_log.json`, and the topic store."

**DBT-03 · S2 · P1 — Relation vocabulary mismatch.** Debate analyzer expects `relation: "refutes"`; kernel CLI vocabulary is `{contradicts, requires, supports, supersedes}` (legacy relations survive only inside backfilled data). *Fix:* alias or migrate; add a test.

**DBT-04 · S2 · P2 — Broken topic compiler with hardcoded absolute paths.** `llm_compiler.py` points at `/home/manigupt/Hello/python/ai_agent/…` and the subprocess pipeline is commented out. *Fix:* rewrite as "LLM proposes nodes/edges → `topic_ops batch` → contradiction gate" (LLM thinks, engine enforces).

**DBT-05 · S2 · P1 — ChromaDB path is CWD-relative (`./chroma_db`).** Different launch directories create different indexes. *Fix:* absolute path from config/env.

**DBT-06 · S3 · P3 — `sys.path` hacks** (`kernel_bridge`, `debate_ops`). *Fix:* install the codebase as a package (editable install).

**DBT-07 · S3 · P3 — Fixed confidence constants** (0.7/0.7/0.5/0.6) and single `local_user`. *Fix:* calibrate or make configurable; per-user stores when a human twin arrives.

**DBT-08 · S2 · P2 — Relationship to opportunity "challenge" is unclear.** The opportunity engine has a debate hook (challenger argues against, scorer defends) implemented in `economy/challenge.py`. *Fix:* decide whether ArguGod's graph/gate is reused for challenge rounds. *Ask:* "Does `challenge.py` use any ArguGod code?"

---

## I. Job module

**JOB-01 · S2 · P1 — ±3 h overlap hard-gate blocks a planned experiment.** Candidate hard-gates include ±3 h timezone overlap; the planning chat's hypothesis H3 is "US-hours overlap materially changes conversion" — impossible to test if those roles are filtered. *Fix:* make overlap a soft score with an explicit experiment arm.

**JOB-02 · S2 · P1 — Employer discovery is the highest-leverage missing piece** (company → hiring team → open jobs → stack → likely decision-maker → contact channel) — plus Workable/Recruitee adapters, interview/offer tracking, contact enrichment (note third-party enrichment adds DPDP/ToS considerations).

**JOB-03 · S2 · P1 — Define what "submit" means.** Public ATS APIs often can't submit for arbitrary postings. *Fix:* **assisted submission** — agent prepares the pack, human clicks submit; never a browser bot. *Ask:* "What does the application 'submit policy gate' actually do when it passes?"

**JOB-04 · S2 · P1 — Enforce evidence-binding by test.** Rule: tailoring may not invent experience. *Fix:* automated check that every claim sentence in a variant maps to an evidence pointer; adversarial JD regression tests.

**JOB-05 · S3 · P2 — EV inputs are priors.** P(interview/offer) have no data yet; label as priors and update from the funnel; keep "unknown comp never rejects".

**JOB-06 · S3 · P3 — Retention/PII** for resume, contacts and outreach history.

---

## J. Security & operations

**OPS-01 · S1 · P0 — No production/monitoring/backup story.** *(Partly closed 2026-11-02: systemd unit, `healthcheck.py`, `backup.py` + restore drill. Off-machine encrypted copy still unset.)* Everything is local conda + localhost + SQLite. *Fix:* runbook — process supervisor, health endpoint, alerting on failed jobs, nightly encrypted backups of `kernel.db`, `market.db`, FireFlow DB and secrets, restore drill, off-machine copy.

**OPS-02 · S2 · P1 — No CI described.** *(Closed 2026-11-02: `.github/workflows/ci.yml` runs secret scan, path check, fast tier and kernel smoke.)* Suites exist (backend jest, kernel smoke 9/9, popula smoke, eval harness, drift tests). *Fix:* run all on every commit; block merges on drift/contract failures; disable hot-reload in prod.

**OPS-03 · S2 · P1 — Secrets handling.** *(Closed 2026-11-02: `scripts/secret_scan.py` + `.env.example`; rotation documented there.)* `.pie_operator`, `.sender_identity`, API keys, JWT secret. *Fix:* env separation dev/prod, secret scanning, rotation policy, no secrets in repo history.

**OPS-04 · S2 · P1 — Tamper-evident audit log.** Approvals, authorizations, `--force` overrides and kill-switch use must be append-only and hash-chained, with approver identity.

**OPS-05 · S2 · P1 — Framework currency.** *(Open: no Node runtime here, so the upgrade cannot be executed or audited.)* README pins Next.js 15.3.3; later security advisories exist for 15.x (including a React Server Components RCE-class issue in late 2025). **[verify]** upgrade to the latest patched release and run `npm audit`; add rate limiting/CORS/input validation review since the app began as a social product.

**OPS-06 · S3 · P2 — Absolute personal paths** *(Runtime code closed 2026-11-02: `codebase/paths.py`; legacy `agent_tools` and old docs still cite paths.)* in runbooks. *Fix:* `$PIE_ROOT`, `$FIREFLOW_ROOT`.

**OPS-07 · S2 · P1 — LLM spend is uncapped and unlogged.** *(Closed 2026-11-02: `agent_core/llm_cost.py` — per-task token/₹ budget + SQLite cost rows, hooked into the loop.)* *Fix:* per-loop token/₹ budget, log model cost per task so unit economics include AI cost; which model/provider is used is not stated in docs ❓.

---

## K. Documentation hygiene

**DOC-01 · S3 · P0 —** FireFlow README: `npm run app` says backend **3001**; elsewhere API at **:5000**; economy runbook uses **:5000**. Pick one.
**DOC-02 · S3 · P1 —** Phase/stage labels violate the project's own rule: FireFlow README "Stage A–E" blocks; popula README "Phase0/Phase3/PhaseA/PhaseB/PhaseC/Adds"; twins README "Phase-3 bypass removed"; old master README "Phase 3". Rename by capability (done in this doc set).
**DOC-03 · S2 · P1 —** Stale rows: kernel README "FireFlow vendoring deferred" vs shipped drift suite; usage.md date (KRN-05).
**DOC-04 · S2 · P1 —** Referenced-but-unsupplied docs (see master §13) — a direction session cannot see them.
**DOC-05 · S3 · P1 —** Line-number citations (`file.py:255`) rot immediately; use file + symbol.
**DOC-06 · S3 · P2 —** `SimDvptPhases.md` is the original game README + an old plan; split into `game UI` notes and roadmap items (done in `populaDyn_simu/README.md` and `02_roadmap_master.md`).
**DOC-07 · S3 · P1 —** No append-only iteration log across docs (only PhasePlan's gate log). Adopt `04_iteration_log.md`.

---

## L. Strategy & product

**STR-01 · S2 · P0 — Make the freeze list explicit and enforced** (see master §14). The FireFlow README still shows a large social surface; new work must justify itself against the revenue loop.
**STR-02 · S2 · P1 — Moonshot unlock criteria.** Keep LOCKED until: ≥ 10 paying customers with positive contribution, ≥ 1 city twin validated out-of-sample with real feeds, and a repeatable recurring workflow. Then open the ladder one rung at a time.
**STR-03 · S2 · P1 — One ICP, three SKUs.** Pick a single customer profile (e.g., engineering/export MSMEs in a reachable cluster near Kanpur for relationship leverage) and three outcome SKUs: *100 verified suppliers*, *competitor/price intelligence*, *catalogue/data cleaning*. Price by experiment (₹2–10k pilots).
**STR-04 · S3 · P2 — Add competitor evidence** (existing supplier directories, data-annotation vendors, freelance platforms) to the opportunity evidence types; differentiation = fixed price + verified + fast.
**STR-05 · S2 · P1 — Approval inbox + risk-tiered approvals + one autonomy charter** (master §10). Founder bandwidth is the real throughput limit.
**STR-06 · S2 · P2 — Marketplace unlock criteria:** ≥ 3 recurring workflows, ≥ 20 workers earning monthly, ≥ 10 customers; data/compute remain demand-first internal capabilities until then.
**STR-07 · S3 · P2 — Vision-engine guardrails.** Behavioral maps are sensitive personal data; astrology/soft-science layers must stay *labeled hypotheses* and out of customer-facing claims; corruption/public-flow analysis must output *anomalies with evidence*, never accusations naming individuals.
