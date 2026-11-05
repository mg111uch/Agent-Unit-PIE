# 🧠 Agent_Unit_PIE — Master Agent Doc (Level 0)

> **Doc set version:** 2.1 · **Compiled:** 2026-10-19 · **Consolidated:** 2026-10-25 · **Latest dated evidence in sources:** 2026-09-15 (all integration gates PASS)
> **Sources:** old master README (now `vision.md`), all module READMEs + kernel `usage.md` + `SimDvptPhases.md`, FireFlow app README, and 4 planning chats (`PlanFixes2`, `FeatureIdeas`, `FixesIssues`, `PhasePlan`).
> **Purpose:** let an LLM (or a new human) understand **PIE (agent) and FireFlow (app) from docs alone**, and advise on *development direction after each iteration* without being shown code.

---

## 0. Brief (read this if nothing else)

| | |
|---|---|
| **What it is** | **PIE** = persistent cognition (kernel + simulators + digital twins + debate engine + dev loop). **FireFlow** = economic execution + sensor layer (identity, tasks, contracts, ledger, workforce, data, compute, CRM). PIE decides *what should happen*; FireFlow decides *whether and how it actually happens*. |
| **Objective** | MAXIMIZE SUSTAINABLE REAL-WORLD PRODUCTIVE CAPABILITY under cash / risk / capital / skills / technology / regulation / time / energy / demand / reliability constraints. **Bootstrap overlay:** maximize *validated contribution per unit of agent effort* until revenue is repeatable. |
| **Where it stands** | Breadth is large and tested (kernel, simulators, twins, economy, ~60 FireFlow capabilities, jest/smoke suites green at the 2026-09-15 gates). **No document records a paid customer yet.** City twins exist as versioned skeletons fed mostly by placeholders (conf ≤ 0.35). Kernel is only partly activated. |
| **Biggest risks** | (1) the PIE↔FireFlow loop is *closed in adapters and tests*, not proven on live transport; (2) real money rails + Indian compliance are undocumented; (3) delivery capacity/QC for the first paid projects is undocumented; (4) simulator-to-city validity (agent cap 400, placeholder data); (5) several doc contradictions that can cause silent failures. See `03_loopholes_and_suggestions.md`. |
| **Direction** | **Stop adding modules. Prove the loop, earn the first rupee, keep the city/sim track as a small parallel slice, keep the Moonshot ladder LOCKED.** See `02_roadmap_master.md` §1. |

---

## 1. How this doc set works

### 1.1 Hierarchy (max two levels — do not nest deeper)

All files now live flat in `system_devpt_reports/`; module docs keep their own directory and `README.md`.

| Path | Level | Purpose | Read when |
|---|---|---|---|
| `00_README_master.md` | 0 | This file: vision index, system map, loops, contract, invariants, snapshot | Always first |
| `01_session_playbook.md` | 1 | How to run a *direction session* with no code; iteration-report template; question bank | Starting/ending any session |
| `02_roadmap_master.md` | 1 | Cross-module unimplemented work, gates, horizons, **recommendation ledger** (every idea from the planning chats with status) | Choosing next work |
| `03_loopholes_and_suggestions.md` | 1 | Register of loopholes/suggestions with IDs, severity, fix, and a *verify question* for the coding agent | Prioritising, auditing |
| `04_iteration_log.md` | 1 | Append-only log of iterations & gates | After each iteration |
| `05_implementation_plan.md` | 1 | ID → file/symbol → acceptance test, sequenced in waves; verified code state | Starting an iteration |
| `agent_runtime/README.md` | 1 | Agent loop, tools, commands, workflows, autonomy gate, scripts | Questions about *how the agent works* |
| `kernel/README.md` | 1 | Memory, lineage, validity, contradiction gate, bus, registry | Cognition questions |
| `populaDyn_simu/README.md` | 1 | General civilization simulator, policy stack, epoch engine | Simulation/policy questions |
| `digital_twins/README.md` | 1 | City twins (Kanpur, Delhi), provenance, calibration, contrast lab | City/twin questions |
| `economy/README.md` | 1 | Opportunity engine, revenue loop, job module, PIE-side economic code | Revenue/jobs questions |
| `debate_argu/README.md` | 1 | ArguGod debate/belief engine | Debate/belief questions |
| `fireflow_app/README.md` | 1 | FireFlow app from PIE's perspective: features, endpoints, state machines, human gates | App questions |
| `codebase_atlas/README.md`, `stock_analyser/README.md`, `virtual_silicon/README.md` | 1 | Codebase atlas, stock research precedent, silicon/simulator module | When those modules are in scope |
| `vision.md` | 2 | Original vision manifesto: universal unit schema, engine catalog, storage architecture, self-evolution mechanisms, stated limitations | When you need *intent* rather than state |

Module-level `roadmap.md` / `status.md` / `usage.md` files are supplied and live beside their README; they remain the plan-of-record for their module. This master doc consolidates cross-module status. See §13 "Known unknowns" for what is still genuinely missing.

### 1.2 Doc rules (inherited from the project, kept)

- **R1** Shipped features → module README feature tables. Unimplemented → roadmap. Next task → status/iteration log.
- **R2** **No phase / stage / step labels** in feature tables. Name features by what they *are* (`Capital books`, not `Phase 4`). Stage labels belong to session history only. *(The old docs violate this in places — see DOC-02.)*
- **R3** **Code is the ultimate source of truth.** Docs describe capabilities by *file + symbol*; **no line numbers** (they rot).
- **R4** Never put secrets in docs. Never use absolute personal paths — use `$PIE_ROOT` (the `Agentic_Unit_PIE` repo) and `$FIREFLOW_ROOT` (the FireFlow app repo, currently the directory named `reddit-clone`).
- **R5** Every claim carries a status (legend below). Inferred claims carry `[INFERRED]`.

### 1.3 Status legend

| Mark | Meaning |
|---|---|
| ✅ | Shipped and described by a supplied doc |
| 🟡 | Partial (some of the idea shipped, or shipped only on shaped/static data) |
| ⬜ | Not built |
| ⛔ | Deliberately frozen / locked |
| ❓ | Unknown from supplied docs — must be answered by the coding agent |

### 1.4 Marker legend (greppable; `grep -rn "\[LOOPHOLE\|\[SUGGESTION\|\[VERIFY\|\[INFERRED"`)

```
[LOOPHOLE ID · S1|S2|S3] … [/LOOPHOLE]      a defect/risk found by analysis (S1 = can lose money/data or block revenue)
[SUGGESTION ID · P0|P1|P2|P3] … [/SUGGESTION]   a proposed improvement (P0 = do in the next iteration)
[VERIFY ID] … [/VERIFY]                     a question only the coding agent can answer from code
[INFERRED] …                                a statement deduced from docs, not stated by them
```
Inline markers are short; the full entry (evidence, fix, verify question) lives in `03_loopholes_and_suggestions.md` under the same ID.

---

## 2. Vision & principles (condensed from the original README)

Agent_Unit_PIE builds **persistent machine cognition**: a recursive world-modeling infrastructure that observes reality, extracts signals, compresses knowledge, finds patterns, models systems, simulates futures, generates strategies, and improves itself — across humans, codebases, organizations, companies, cities, states, markets, ecosystems, civilizations and AI societies — while keeping temporal awareness, causal humility, hierarchical memory and multi-domain reasoning.

```
Traditional AI:   query → retrieve → answer
PIE:              observation → signal extraction → pattern formation → world modeling
                  → simulation → prediction → refinement
```

**Signal-centric and pattern-centric, not document-centric** — documents are evidence sources.

**Key principles:** (1) signals, not documents; (2) schema/ontology-first; (3) self-compressing memory; (4) modular core kernel + independent domain modules; (5) evolutionary KB (LLM prior → evidence-grounded model); (6) every claim carries evidence, source, confidence, counter-arguments; (7) temporal awareness; (8) human-in-the-loop — augment human judgment, never replace it.

**Intentionally avoided:** giant monolithic memory files, vector-only cognition, hardcoded domain assumptions, static knowledge, *fully autonomous uncontrolled agents*.

**Agent orchestrator design:** tool-driven loop `Observe → Execute → Learn → Store → Evolve`; persistent structured memory via markdown/JSON; deterministic actions; file-size limits; path traversal (`..`) blocked.

**Full vision (Level 2):** `vision.md` keeps the original manifesto — the complete universal-unit schema, the engine catalog (ingestion, behavioral + soft-science, spatial, economic, stock, pattern), the storage-architecture table, the self-evolution mechanisms and the project's own stated limitations. Use it for **intent**; use §6 below for **what is actually built**. Its ArguGod paragraph is corrected to the current code (compiler working, `graph.json` derived — DBT-01).

---

## 3. System map

```
                         ┌───────────────────────────── PIE (cognition) ───────────────────────────────┐
                         │  agent runtime (LLM loop, tools, slash commands, workflows, autonomy gate)  │
                         │  KERNEL: ontology · unit registry · memory · retrieval · signals · events   │
                         │          patterns · hypotheses · validity · lineage · bus · registry        │
                         │  SIMULATORS: popula_dyn (general civilizatn ABM) · eco_sim · virtual_silicon│
                         │  DIGITAL TWINS: city (Kanpur, Delhi) · company · (human/country: vision)    │
                         │  DEBATE (ArguGod): belief tracking · contradiction detection                │
                         │  ECONOMY (PIE side): opportunity scoring · revenue loop · job module        │
                         └──────────────────────────────┬──────────────────────────────────────────────┘
                                          PIE ↔ FIREFLOW GATEWAY (proposal envelopes · receipts · events)
                         ┌──────────────────────────────┴──────────────────────────────────────────────┐
                         │ FIREFLOW (execution + sensors): identity · task marketplace · contracts/    │
                         │ escrow · authoritative ledger · settlement · reputation · business profiles │
                         │ enterprise twin · business agents · data/compute markets · sensor network · │
                         │ prospect CRM · proposals · outreach · funnel · job store/tracker            │
                         └──────────────────────────────┬──────────────────────────────────────────────┘
                                                      REAL WORLD
```

**Ownership rule (hard):** FireFlow must never grow its own "brain". PIE proposes; FireFlow authorizes server-side and executes; FireFlow returns evidence + economic delta; PIE learns. `popula_dyn` is the *hypothetical* world; digital twins are the *current-state estimate*; kernel is *memory of what happened*; FireFlow is *the reality where hypotheses get tested*.

### 3.1 Repo & data layout (logical)

```
$PIE_ROOT/                        (repo: Agentic_Unit_PIE)
  codebase/
    kernel/                       cognition substrate (+ capability_registry.yaml, schemas/, retrieval/, hypothesis/, validity, bus)
    development/                  dev-loop orchestrator: workflow_engine, contracts, development_state, develop_tools, validation_gate, eval_harness
    modules/
      argu_god/                   debate engine (+ engine/topic_store.py = single topic writer/reader)
      digital_twins/              city_twin, city_state, adapters, calibration, policy_experiments, contrast_lab, flywheel, …
      economy/                    scoring, challenge, capital, execution, industrial, fiscal, prospects, discovery, outreach, delivery, revenue, jobs/
      simulators/                 popula_dyn/, eco_sim/, virtual_silicon/, simulation_connector.py
    agent_core/                   agent loop, tools (debate_ops, question_ops, …), engine, ws_handler
    prompt_fragments/             kernel_playbook.md, onboarding.md (injected into server-assembled prompts)
  data/                           kernel.db, market.db, workflows/, topics/, mindmaps/, memory/episodic/, units/simulations/
  scripts/                        topic_ops.py, backfill_topics.py, record_removal.py, render_status.py, smoke_kernel.py, …
  system_devpt_reports/           THIS DOC SET (+ AGENTS.md operating rules, PhasePlan.md, FeatureIdeas.md, FixesIssues.md, PlanFixes2.md)
  generated_reports/INDEX.md      project health badge

$FIREFLOW_ROOT/                   (repo: reddit-clone → FireFlow)
  backend/                        Node API (SQLite, jest) · pie/ gateway · .pie_operator, .sender_identity (local secrets)
  frontend/                       Next.js 15.3.3 app (+ Jest, Playwright, Cypress)
  README.md · roadmap.md
```

### 3.2 Data stores (one row per store — know which is authoritative)

| Store | Location | Owner | Authoritative for | Notes |
|---|---|---|---|---|
| Kernel DB | `data/kernel.db` (SQLite) | kernel | cognition: semantic/generic memory, episodic memory, hypotheses, simulation_versions/runs, citation_cache, logs | cognition-only by design |
| Episodic raw | `data/memory/episodic/{sim}_{run}.json` | kernel | immutable raw findings | never rewritten |
| Sim runs | `data/units/simulations/{sim}/{run}/` (`params.yaml`, `signals.json`, `data.csv`, `summary.json`) | simulators | run artifacts | legacy `codebase/units/simulations` fallback |
| Topic views | `data/topics/<topic>/graph.json` | derived | **nothing** — regenerated view | never hand-edit |
| Belief state | `…/mindmaps/local_user/belief_state.json` | debate | user stances | **path conflict between docs** — DBT-02 |
| Vector index | `./chroma_db` (CWD-relative) | debate | semantic dedup/counter-args | **launch-dir dependent** — DBT-05 |
| Domain DB | `data/market.db` (SQLite) | economy (PIE side) | prospects, fiscal_runs, capital books, PIE-side ledger | "domain store; kernel.db stays cognition-only" |
| FireFlow DB | SQLite inside `backend/` (path ❓) | FireFlow | **system-of-record for money, tasks, CRM state** | see INT-04 for ownership overlap with market.db |
| Twin stores | per-city JSON/SQLite, versioned (path ❓) | digital_twins | city state w/ provenance | v1 of Kanpur retired HISTORICAL by design |
| Workflows | `data/workflows/*.json` + `.md` + `workflow_graph.html` | dev loop | allowed transitions | engine-enforced |
| Local secrets | `backend/.pie_operator`, `backend/.sender_identity`, candidate `resume.md` | operator | credentials / signature / master resume | never in docs; chmod 600 |

---

## 4. Universal Unit model

Everything is a **Unit**: an entity with state, signals, behaviors, relations, patterns and a timeline. Unit families: Human, Organization, Geographic (city/state/country), Digital (codebase/server), Abstract (stock/market/policy), Society (ideology/movement), Simulated (population agents, digital twins), and — via FireFlow — Person / Business / Organization / AI Agent / Service / Product / Vehicle / Machine / Facility / Compute Node / Dataset.

```python
{ "unit_id": "...", "unit_type": "human|organization|city|codebase|stock|sim_agent|…", "subtype": "...",
  "created_at": "ISO-8601", "identity": {}, "state": {}, "traits": {},
  "resources": {"food":0,"money":0,"energy":0,"knowledge":0,"cpu":0,"trust":0},
  "signals": [], "events": [], "patterns": [], "relations": [], "behaviors": [],
  "beliefs": [], "hypotheses": [], "metrics": {}, "subunits": [], "timeline": [], "memory": {},
  "digital_twin": {}, "simulations": [], "predictions": [], "risks": [], "strategies": [],
  "health_score": 0.0, "improvement_suggestions": [] }
```

**Single identity rule:** FireFlow and the twins *reuse* the PIE Unit ontology via the versioned artifact `unit_schema.v1.json` (single source; vendored into FireFlow with drift tests). No competing identity systems.

---

## 5. Cognitive stack

### 5.1 Seven-layer self-compressing memory

| # | Layer | Size | LLM access |
|---|---|---|---|
| 1 | Raw observation (docs, reports, transcripts) | unlimited | never direct |
| 2 | Signal memory (structured observations) | large | rare |
| 3 | Event memory (important events) | medium | selective |
| 4 | Pattern memory | small | frequent |
| 5 | Abstract knowledge (compressed mental models) | tiny | regular |
| 6 | Hypothesis memory | very small | when testing |
| 7 | Working memory (5–50 KB active context) | — | always |

Compilation pipeline: `raw observations → signals → events → relations → patterns → abstractions → compressed world models → working-memory packets`. Self-evolution: summarize (1000 obs → 100 signals → 20 patterns → 5 models), reorganize, generate hypotheses, detect own contradictions, self-prioritize.

### 5.2 Retrieval philosophy — and reality

Intended order: **unit → relation → temporal → pattern → semantic (vector is secondary)**. *Reality today:* the retrieval cascade is **unit / timeline / pattern**; **hierarchy and relation retrievers are DORMANT**; per-simulator, version-aware retrieval is ✅. Vector (ChromaDB, `all-MiniLM-L6-v2`) is used only by the debate engine and dedup, **not** by the autonomous contradiction gate.
[SUGGESTION KRN-02 · P1] Activate relation/hierarchy retrievers first for the *city graph* (factory requires electricity, road serves cluster, …) — it is the one place the principle has an immediate consumer. [/SUGGESTION]

### 5.3 Signal & pattern formats

Universal signal: `{signal_id, unit_id, signal_type, category, location, intensity 0–10, timestamp, metadata, source, confidence 0–1, trend}`. Pattern types: temporal, trend, correlation, contradiction, structural, recursive. Epistemic rule for causality: the causal engine emits **candidate causes with confidence, evidence and alternative explanations — never "CAUSE = X"**; simulations show "under model assumptions", not real-world causation.

---

## 6. Engine maturity map

| Engine | Role | Maturity | Detail |
|---|---|---|---|
| Kernel: schema/ontology/unit registry/versioned unit schema | identity substrate | ✅ | `kernel/` |
| Kernel: semantic + episodic memory, retrieval (per-sim, version-aware), compression, validity, lineage | persistence & knowledge | ✅ | `kernel/` |
| Kernel: hypothesis engine + symbolic contradiction gate | autonomous research discipline | ✅ | `kernel/` |
| Kernel: bus, signal router, event extractor, activation registry | nervous system | 🟡 (revived; thin; registry = 66 entries at creation, **16/8/42** = ACTIVE/PARTIAL/DORMANT [INFERRED order]) | `kernel/` |
| Kernel: relation/hierarchy retrievers | graph reasoning | ⬜ DORMANT | KRN-02 |
| Ingestion engine (document/pdf/web/news/transcript/observation extractors) | raw → observations | ❓ vision; city adapters take **shaped/static inputs only, no network** | TWN-01 |
| Behavioral Intelligence + Soft-Sciences-as-hypotheses | human behavior maps | ❓ vision-only in supplied docs | STR-07 |
| Spatial Intelligence | GIS, infra graphs | ❓ vision-only; no GIS ingestion documented | TWN-01 |
| popula_dyn | general civilization ABM + policy/epoch stack | ✅ | `populaDyn_simu/` |
| `virtual_silicon` | silicon/simulator module | ❓ docs supplied (`virtual_silicon/`); build state unverified | `virtual_silicon/` |
| `eco_sim` | second simulator (planning name only) | ⛔ **no code** — nothing under `codebase/modules/simulators/`; do not describe it as registered | SIM-03 |
| City twins (Kanpur, Delhi) | replica of real cities | 🟡 versioned, provenance-tagged, placeholder-heavy | `digital_twins/` |
| Company twin | snapshot→ledger | ✅ (PIE) · FireFlow has its own *enterprise twin* | INT-07 |
| Human / Country twins | — | ❓ vision | — |
| Economy (PIE side): opportunity, revenue loop, jobs | earn | ✅ code · ❓ traction | `economy/` |
| Economic Intelligence: capital_flow ✅(signal), opportunity ✅, corruption/gdp/investment engines ❓ | — | mixed | `economy/` |
| Stock intelligence (separate module; OOS discipline; "hole closed at 51/0") | research precedent | ✅ exists | `stock_analyser/` |
| Debate (ArguGod) | belief tracking | ✅ with path/vocab issues | `debate_argu/` |
| Dev loop (12-node workflow, autonomy gate, eval harness) | self-development | ✅ | `agent_runtime/` |
| FireFlow backend | execution + sensors | ✅ | `fireflow_app/` |
| FireFlow frontend | UI | ✅ social/forms/services · ⬜ economic modules appear **API-only** [INFERRED] | `fireflow_app/` |

---

## 7. The master loops

| # | Loop | Shape | Closed in tests | Closed live |
|---|---|---|---|---|
| L1 | Research/dev loop | `start→orient→version_sync→hypothesis→decide_branch→{experiment│modify_code}→update_knowledge→evaluate→validate→loop→stop` (12-node `research_development`; subgraphs `kernel_ops`, `popu_sim_dev`, `economic_loop`) | ✅ | ✅ (runs in agent) |
| L2 | Economic loop | `observe→discover→estimate→simulate→rank→task→execute→collect→reconcile→twin→learn→scale/abandon/pivot` (12-node `economic_loop` subgraph; every loop ends in a verdict + reason) | ✅ | ❓ |
| L3 | Revenue acquisition | evidence → prospect → pain score → decision (IGNORE/RESEARCH/OUTREACH/PILOT) → offer (template+quote) → draft → **human approve** → capped send → response class → proposal → accept → task+contract → microtask launch → verify → settle → funnel → kernel finding | ✅ | ❓ (no paid customer documented) |
| L4 | City twin | ingest → normalize → unit resolve → observation → event → signal → pattern → twin update → calibration → baseline validation → policy hypothesis → simulate → falsify → knowledge → PIE decision → (approval → FireFlow execution → measure → twin update) | 🟡 one slice (Kanpur capacity) | ⬜ |
| L5 | Sensor loop | human observation (trust fields) → independent confirmation → reporter reliability → twin → simulate → measured task | ✅ | ❓ |
| L6 | Job loop (first specialized economic agent; personal revenue experiment) | `resume.md → candidate twin → ingestion → normalize → fit/verdict → application pack → policy gate → outreach/apply (human) → tracker → learning → kernel` | ✅ | ❓ |

[LOOPHOLE INT-01 · S1] "Closed in tests" ≠ "closed live": the FireFlow→kernel adapter translates *shaped payloads* and makes no external calls; no supplied doc describes a poller/webhook/outbox that moves real FireFlow events into `kernel_bus`. [/LOOPHOLE]
[VERIFY INT-01] Name the process (if any) that moves a FireFlow ledger/task event into the kernel without a human running a script. [/VERIFY]

---

## 8. PIE ↔ FireFlow contract

| Direction | Mechanism | Payload / purpose | Status |
|---|---|---|---|
| FireFlow → PIE | CLI proxy (`economy/score_cli.py`) | opportunity scoring — **single-source scorer**, FireFlow is a thin proxy | ✅ |
| FireFlow → PIE | CLI proxy (`jobs/fit_cli.py`) via `POST /api/jobs/:id/score` | job fit vs candidate twin; caches score + verdict | ✅ |
| PIE → FireFlow | HTTP `POST /api/prospects/import` | PIE discovery batches; within-batch dedup; per-row errors; created/deduplicated counts | ✅ |
| PIE → FireFlow | HTTP `POST /api/jobs/import` | normalized roles; dedup by `job_id` | ✅ |
| PIE → FireFlow | Gateway `backend/pie/` + `economy/pie_protocol.py` | strict **proposal envelope** `{proposal_id, objective, action, budget, risk, required_capabilities, expected_outcome, authorization}`; server-side decision **authorize / deny / needs-approval**; RBAC | ✅ |
| FireFlow → PIE | Execution receipts | idempotent evidence ingested as observations; invalid envelopes rejected; over-cap proposals denied | ✅ (inbound to FireFlow) |
| FireFlow → kernel | `economy/event_adapter.py` → `kernel_bus` | `PaymentSettled` etc. → kernel event + `capital_flow` signal | 🟡 **shape-only** |
| Both | `unit_schema.v1.json` vendored + drift jest; `pie_protocol` parity builders | one identity vocabulary | ✅ |
| Auth (PIE→FireFlow pushes) | `POST /api/auth/login` as shared local operator `pie_operator` (password file, JWT **expires in 1 h**) | manual token refresh each session | 🟡 see INT-02 |
| Auth (agents) | Agent accounts: API keys bound to AI Agent units; supervised spend caps enforced on proposals | scoped, server-side | ✅ |

[LOOPHOLE INT-02 · S1] PIE's own pushes use a shared *human-style* operator login instead of an **agent account** with scoped key — audit trail conflates operator and agent, and unattended jobs break at JWT expiry. [/LOOPHOLE]
[SUGGESTION INT-05 · P1] Expose PIE to FireFlow through a **compressed economic API** of ≈15 verbs (`discover_prospects, get_prospect, create_opportunity, score_opportunity, create_offer, create_outreach, record_response, create_proposal, create_contract, create_project, create_task, verify_result, get_settlement, get_unit_economics, record_learning`) rather than ~100 endpoints. [/SUGGESTION]

---

## 9. System-wide feature index (shipped; detail lives in module docs)

| Domain | Capabilities (one line each) | Doc |
|---|---|---|
| Kernel fabric | per-simulator registry · Git-backed lineage (`sim@commit`) · concept-level validity (ACTIVE→HISTORICAL) · version-aware retrieval · per-sim compression (materialized view) · declarative simulation ontology · symbolic contradiction gate · hypothesis→semantic-memory export · kernel bus · activation registry · versioned unit schema · citation cache · capability-regression signal · tool-bypass detection · generated status/index | `kernel/` |
| Dev loop | 12-node unified workflow · DevelopmentState (<1.9 KB) · `develop.*` primitives (9) · graduated autonomy gate L0–L6 · agent eval harness · hot-reload · onboarding fragment · removal-rationale log | `agent_runtime/`, `kernel/` |
| Simulation | generic UnitAgent + pluggable behaviors · agent factory · firm hire/invest · toroidal spatial engine · reproduction/inheritance/individual variation/environment/supply-demand · return-intent behaviors & independent RNG (deterministic) · policy DSL · scenario branching & scoring · robustness (effect chains, sensitivity) · falsification · epoch engine (5 regimes, 6 macro vars) · policy screen/registry · twin-driven scenarios | `populaDyn_simu/` |
| Twins | generic CityTwin (`city_id`) · CityState with provenance · truth tiers · reporter reliability · adapters · 2011→2025 snapshots · twin versioning · capacity slice · calibration · policy experiments · contrast lab · flywheel | `digital_twins/` |
| Economy (PIE) | economic object model · opportunity engine (+ evidence/EV) · twin bridge · capital books · execution pipeline · economic loop · industrial graph lite · fiscal ledger · barter kernel · event adapter · prospects/pain score · discovery · service templates · outreach · delivery bridge/margin gate · revenue metrics/experiments · live discovery job · candidate twin · job ingestion/fit/apply/outreach/learning | `economy/` |
| FireFlow | see `fireflow_app/` §3 (≈60 capabilities incl. economic identity, task marketplace, supply offers, micro-work, escrow, authoritative ledger, settlement pipeline, reputation, business profiles, capability search, enterprise twin, business agent, data marketplace + licenses, compute exchange, sensor network, prospect CRM, proposals, outreach, funnel, jobs store/tracker, agent gateway) | `fireflow_app/` |
| Debate | `/argu explore` via agent loop · 3 options + custom · belief tracking · contradiction detection · kernel signals · hypotheses · vector counter-arguments | `debate_argu/` |

---

## 10. Autonomy, safety & human gates

**Two autonomy systems exist and should be unified under one charter (SUGGESTION STR-05):**

| System | Scope | Levels |
|---|---|---|
| Dev autonomy gate (`validation_gate`) | changes to PIE code | L0 suggest · L1 edit+test · L2 +commit · L3 sim_modify · L4 workflow_modify · L5 kernel_propose · L6 kernel_modify. `DEFAULT_CEILING=3` (sim autonomous); L4+ gated; L5–L6 need human approval; `L3 kernel`, `L1 workflow`, L6-without-approval blocked |
| Economic authorization (FireFlow gateway) | real-world actions | authorize / deny / needs-approval; agent spend caps; ledger approve gate |

**What always needs a human (documented):** real-money movement (ledger approval) · outreach send (approve → capped send) · proposal over price/confidence gate · every job-outreach send · kernel L5–L6 changes · contradiction-gate `--force` · agent proposals over cap · external-contact policy changes. Planned but unconfirmed: `require_human_for = salary_negotiation, legal_attestation, demographic_questions, employment_contract` (jobs) ❓.

[SUGGESTION STR-05 · P1] The human gate is a **bottleneck and currently curl-grade UX** (economic modules appear to have no UI). Build one *approval inbox* screen (the only frontend work worth doing now), and tier approvals by risk (batch-approve low-risk internal actions; keep money and external contact manual). [/SUGGESTION]

---

## 11. Global invariants (non-negotiable)

1. **One persistence path per concern**: topics through `topic_store` (SQLite canonical, `graph.json` derived); money through the authoritative ledger; cognition in `kernel.db`.
2. **Server-side authorization**: the LLM never decides whether it has permission.
3. **Idempotency everywhere money or state moves** (webhooks, retries, claims, grants, jobs pay once); state transitions are database invariants, not agent reasoning.
4. **Money in integer paise**; every rupee movement is a ledger row; agents propose, humans approve.
5. **Evidence pointers**: every claim → source/evidence; resume tailoring may never invent experience; outreach drafts evidence-only with STOP footer; never invent companies/case studies.
6. **Truth tiers** on every twin field: OBSERVED / TRANSACTION_DERIVED / THIRD_PARTY_VERIFIED / OWNER_REPORTED / AI_INFERRED / SIMULATED — assumptions never silently become facts.
7. **Per-simulator isolation**: findings, versions, topics, lineage never cross simulators; cross-sim never contradicts; `HISTORICAL` excluded by default.
8. **Candidates-only causality**; simulation findings stay `HYPOTHESIS` until multi-seed + falsify.
9. **No arbitrary customer code on compute hosts** (published workloads only; code blobs rejected). **Consent-first, purpose-bound data**; revoked licenses block grants.
10. **No LinkedIn/portal scraping or automation**; official APIs, public ATS feeds, RSS, email, permitted integrations; hand off otherwise. Opt-out is absolute.
11. **Demand first, supply second** for data and compute; FireFlow is infrastructure behind an AI-operated B2B service before it is a marketplace.
12. **No phase labels in feature docs**; kernel tag for FireFlow findings: `fireflow_app`.
13. **Placeholders are labeled** (conf ≤ 0.35); census anchors 0.8–0.85.

---

## 12. Environment & operations quick reference

| Task | Command / note |
|---|---|
| Python env | `conda run -n myenv python …` from `$PIE_ROOT`. **Gotcha:** `conda run` does not forward stdin — heredocs print nothing; use `-c` or a script file |
| Agent server | `conda run -n myenv python server.py` → frontend `/agent` page; slash commands `/argu explore <topic>`, `/auto "<question>"` |
| Simulation game | `python server.py` in the sim dir → `http://localhost:8000/game` (docs: `/docs`) [VERIFY SIM-05 still in sync with generic core] |
| Kernel CLI | `scripts/topic_ops.py` (`add-node, add-edge, neighbors, batch, set-stance, check, signals, list, topics, doctor`; global `--dry-run --json -q`) |
| Revenue job | `revenue_job.py --no-persist` (dry run) → without flag persists to `market.db`, **sends nothing** |
| FireFlow | `npm run app` starts backend + frontend. **Port conflict in docs:** "3001 backend" vs "API at :5000" (DOC-01). Tests: backend `npm test` (jest), frontend `npm test`, Playwright `npm run test:e2e`, Cypress `npm run test:cypress:open` |
| Auth for PIE→FireFlow | mint fresh JWT each session via `/api/auth/login` as `pie_operator` (see INT-02 for the fix) |

---

## 13. State snapshot (as of the docs)

**Gates passed 2026-09-15:** registry (66 entries) · identity (unit schema artifact; 0 live actor refs) · bus + adapter (shaped `PaymentSettled` → event → signal → memory read-back) · capacity slice (Kanpur question answered from cascade) · two versioned twins · calibration (baseline pop error **0.036**; one twin→popula→scenario→finding run, lineage `sim@2cac23d`) · contrast lab (null Pareto verdict) · truth tiers on 14 fields · evidence-gated opportunity scoring · drift/contract jest (8/8) · gateway + RBAC (12/12) · authoritative ledger (18/18) · settlement + dataset licenses (23/23) · sensors anti-fraud (26/26).

**Open items recorded by the project itself:** hierarchy/relation retrievers dormant · `city_twin.py` oversized (741 lines) · `promote --keep` for parallel ACTIVE trees · real city feeds for conf ≤ 0.35 placeholders + water/energy/air dims · multi-seed + falsify for policy experiments before any finding above HYPOTHESIS; calibration caps (pop 400, skill 1.0) on every record · stock: no new sweep without a new idea.

### Known unknowns (still genuinely missing)

FireFlow DB path/schema ❓ · candidate `resume.md` location ❓ · `eco_sim` has **no code** at all (a scope gap, not a doc gap) · the stock "hole closed at 51/0" claim conflicts with the stock closure memo — needs one authoritative statement.
Everything the old doc set called "not supplied" now exists in this directory or the repo: `AGENTS.md`, per-module `roadmap.md`/`status.md`, `kernel_playbook.md`/`onboarding.md` (`codebase/prompt_fragments/`), the `project_history` topic (`data/topics/`), stock + `virtual_silicon` docs, and FireFlow `roadmap.md`.
[SUGGESTION DOC-04 · P1] ~~Digest each missing doc~~ — **mostly resolved 2026-10-25**: every module doc now sits beside its README. Remaining: FireFlow DB schema, resume path, one stock-number reconciliation. [/SUGGESTION]

---

## 14. Top risks & recommended next iteration

**Top risks (full register: `03_loopholes_and_suggestions.md`):** INT-01 live transport · INT-02 agent identity · FIN-01/02 money rails & escrow legality · REV-01/02/03 no recorded revenue, manual funnel top, undefined delivery capacity · OPS-01 no backup/monitoring story · SIM-01/TWN-01 city validity · DBT-01/02 doc contradictions that can silently break contradiction detection.

**Recommended next iteration (order):**
1. **Doc/contract fixes (≈1 day):** DOC-01, DOC-02, DOC-03, DBT-01/02/03.
2. **Loop Proof:** one real FireFlow task + test-mode payment → kernel event/signal retrievable by PIE, using an agent account, with idempotent replay (INT-01/02/06).
3. **Money safety:** global kill switch + daily cap, backups, CI, manual-invoice path for first customers (FIN-01/02, OPS-01/02/03).
4. **Revenue sprint (runs in parallel, mostly operational):** 5 approved offers → first paid pilot → deliverable assembly + customer acceptance link (REV-01..07).
5. **City track (small, parallel):** real data for ~10 series per city + scale-invariance test (TWN-01, SIM-01). Keep Moonshot ladder **LOCKED** (STR-02 unlock criteria).

**Freeze list (do not build now — STR-01):** more social features, elaborate frontend, generic communities, complex prediction markets, ride-hailing, full e-commerce, Moon simulator, public compute marketplace, public marketplace launch.

---

## 15. Glossary

**Unit** universal entity · **Signal/Pattern/Hypothesis** kernel cognition objects · **Twin** live model of a real entity (city/company) · **Truth tier** provenance class of a value · **Lineage `sim@commit`** Git-scoped version of one simulator · **Validity ACTIVE/HISTORICAL** whether a finding still applies to current lineage · **Gate** deterministic check that blocks/permits an action · **Proposal envelope** strict PIE→FireFlow action request · **Receipt** idempotent execution evidence · **Rake** platform fee at settle time (runtime-changeable) · **Paise** 1/100 rupee, the only money unit · **Rung** step on the capability ladder (services→components→systems→industries) · **Loop decision** scaled / abandoned / pivoted + reason · **Placeholder** twin value with conf ≤ 0.35 · **Pain score** geometric mean of evidence × value × fit × access × urgency × pilot_prob · **Funnel** `GET /api/metrics/funnel` canonical revenue dashboard · **Moonshot ladder** city twin → industrial capability → India twin → industry/tech graph → space industry → cislunar → lunar (⛔ LOCKED).
