# Implementation Plan (Level 1) — turning 02 + 03 into code

> **Purpose:** `02_roadmap_master.md` says *what* is unbuilt; `03_loopholes_and_suggestions.md` says *why it is dangerous* and carries the IDs. This file is the bridge: every ID becomes a work item with a file, a symbol, an acceptance test and a register delta. Compiled 2026-10-31 against the code in `$PIE_ROOT`.

## 0.5 Status (compact state, update each iteration)

| Wave | State | Evidence |
|---|---|---|
| W0 docs | ✅ DOC-01, DBT-01 fixed; KRN-05 pending | `04_iteration_log.md` |
| W1 loop proof | ✅ G0 proven live (settlement → outbox → poller → kernel event + `capital_flow`, replay no-op) | it. 1–3; `tests/test_loop_proof.py`; `backend/pie/events.test.js` |
| W1 identity/provenance | ✅ INT-02 PIE, INT-06 | it. 2; `agent_identity.py`, `provenance.py` |
| KRN-08 | ✅ fixed (episodic retrieval was process-local) | `retrieval_engine._persisted_episodic` |
| W2 money safety | ✅ FIN-01/04/08 FF, OPS-04; 🟡 OPS-01, FIN-05 | it. 4; `lib/money.js`, `scripts/ledger_audit.js` |
| W3 revenue | 🟡 funnel ✅, GeM import ✅, QC ✅, assembly ✅, approvals ✅; send transport ✝ | it. 5 |
| W4 ops | ✅ secret scan, CI, budgets/cost log, paths, supervisor, backups; 🟡 OPS-01 off-machine, OPS-05 blocked | it. 6 |
| W5 cognition | ✅ KRN-02/04/05/06/07; ⬜ KRN-03 (needs eval corpus) | it. 7 |
| W6 twin/sim | ✅ TWN-01, SIM-01, SIM-02 | it. 8–9 |
| W7 G1 last mile | ✅ approval UI + magic-link portal + ledger payment; 🟡 REV-06 send, OPS-01 off-machine | it. 9 |
| Remaining before G1 | real send transport (REV-06), off-machine backups (OPS-01), escrow decision (FIN-02, no-escrow path ready) — full list in §5 | `03` |

Runners: PIE `conda run -n myenv python -m unittest tests.<name>`; FireFlow `cd backend && bun test`.

## 0. Ground truth verified from code (answers the ❓/VERIFY items)

> Snapshot taken 2026-10-31. Rows below record the *pre-fix* state; §0.5 and `04_iteration_log.md` are authoritative once an ID is closed.

| ID | Verified state | Evidence |
|---|---|---|
| INT-01 | **Nothing** moves FireFlow events into `kernel_bus` unattended. Only `economy/event_adapter.py` translates shaped payloads. No outbox, poller, DLQ or replay exists. | no `poller`/`outbox` symbol anywhere; `event_adapter` docstring: "No external calls" |
| INT-02 | **FF side exists**: `agent_api_keys` (unit_id, spend_limit_paise) + `authenticateAgentApiKey`. PIE side missing: no key client, no `actor_type`, no scope check. | `backend/middleware/agentAuth.js`; `grep actor_type` → 0 hits in PIE |
| INT-03 | `score_cli.py` has **no** timeout, **no** `UNSCORED` verdict, **no** version field. | file is pure stdin→stdout |
| INT-04 | `market.db` has no FireFlow ID column; `prospects` keys on local `prospect_id` only. No sync direction declared in code. | `ledger.SCHEMA` |
| INT-05 | **No** economic tools in the agent runtime — `agent_core/tools/` has kernel/sim/file/git tools only. | directory listing |
| INT-06 | Findings carry no `app@commit`, `fee_policy_version`, `offer_template_version`. | `grep fee_policy` → 0 |
| FIN-01 | No `MONEY_MODE`, no global kill switch, no aggregate cap. | `grep MONEY_MODE` → 0 |
| FIN-02 | No escrow code in PIE at all (escrow exists only in FireFlow docs, repo absent here). | `grep escrow` → 0 |
| FIN-04 | WAL is on (`journal_mode=WAL`) in `market.db` **and** `kernel.db`; **no** `busy_timeout`, **no** backup script, **no** restore drill, **no** self-audit. | `ledger.connect`, `kernel/persistence/db.py` |
| FIN-08 | **FF side exists**: 8-state machine `TRANSITIONS` + unique idempotency index + `status` column. Gap = no DB `CHECK`/transition table, and PIE `transactions` has none of it. | `backend/lib/ledger.js:TRANSITIONS`; `ledger.SCHEMA` |
| REV-06 | `outreach.py` = draft + `approval_gate` + `can_contact` + `classify_response`. **`send` does not exist** — no SMTP/API transport anywhere. | file contents |
| REV-04/07 | No QC primitives (no duplicate/gold/sampling), no `deliverable_assembly`, no customer portal. | `delivery.py` = project tree + margin only |
| KRN-06 | Claim ladder is **convention only**; `kernel/hypothesis/` has no `claim_strength` enum. | `grep claim_strength` → 0 |
| SIM-02 | `param_hash` appears **nowhere** in code. | `grep param_hash` → 0 |
| OPS-01/02 | No `.github/`, no health endpoint, no supervisor config, no backup script. | repo root |
| OPS-07 | Token *context* budgets exist; **spend** logging does not. | `agent_core/config.py` |

**FireFlow lives at `/home/manigupt/Hello/reddit-clone`** (run its tests with `cd backend && bun test` — Node is absent but Bun 1.4 is installed and runs the jest-style suites unchanged). (Node/Express/SQLite). Items marked *(FF)* are implemented there; each ID needs **two** acceptance tests (PIE half, FF half). No Node runtime is installed on this machine, so jest suites must be run where Node exists.

## 1. Conversion rule (apply to every ID)

```
ID → work item → (owner repo, file, symbol) → acceptance test → register delta
```
Rules: one ID per task · ≤3 tasks per iteration (`01_session_playbook.md` §4.6) · every task names a gate (G0–G5, C1–C4, J1–J2) or a defect class · no task is "done" until its test is green in the fast tier and its ID is re-rated in `03`.

## 2. Sequenced waves

Order is gate-first: **safety and proof before revenue, revenue before breadth.**

### W0 — Doc/contract correctness (≈1 day, unblocks everything)
| Task | IDs | Change | Acceptance |
|---|---|---|---|
| W0.1 | DOC-01 | ✅ closed 2026-11-01: docs say 5000 (`server.js`) | `grep -rn ":3001"` → 0 in docs |
| W0.2 | DBT-01 | debate README: "add nodes via `scripts/topic_ops.py add-node/batch`; never hand-edit `graph.json`" | README states it; `graph.json` described as derived |
| W0.3 | DBT-02/03/05 | print live paths; alias `refutes`→`contradicts`; absolute chroma path from config | path fixture test; vocab alias test |
| W0.4 | DOC-03/KRN-05 | re-run `smoke_kernel.py` (9/9), re-stamp `usage.md`, add bus/registry sections | stamp ≥ last kernel commit |
| W0.5 | STR-01 | freeze list as a checked file (`data/workflows/freeze.json`) + doc-health grep in CI | check fails when a frozen module is registered |

### W1 — Loop Proof (gate **G0**) — the single most valuable iteration
| Task | IDs | Change |
|---|---|---|
| W1.1 *(FF)* | INT-01 | `outbox` table in FireFlow: `(event_id PK, type, payload, created_at, published_at, attempts, state)`. Written in the same transaction as the ledger/task mutation. |
| W1.2 | INT-01 | PIE `modules/economy/inbox.py`: `pull()`, `apply(event_id)`, `replay(event_id)`, `dlq_list()`, `dlq_retry()`; table `ff_inbox(event_id PK, payload, state∈{new,applied,dead}, attempts, last_error, received_at, applied_at)`; dedup on `event_id`; at-least-once; bounded retries → dead. |
| W1.3 | INT-01 | `scripts/pie_poller.py` (long-running, 60 s tick) + wired into `server.py` startup; `/health` reports `last_poll_at`, `dlq_depth`. |
| W1.4 *(FF)* | INT-02 | agent account `pie_revenue_agent` with scopes `prospects:import, proposals:draft, jobs:import, receipts:write`; **no** `outreach:approve/send`, no ledger, no payout edit. |
| W1.5 | INT-02 | PIE `modules/economy/agent_identity.py`: `load()` → `{actor_type, actor_id, scopes}`; `require(scope)`; every `ledger.record_*` takes `actor`; column `actor_type, actor_id` on `transactions`/`prospects`. |
| W1.6 | INT-06 | `modules/economy/provenance.py`: `stamp()` → `{app_commit, fee_policy_version, offer_template_version}` attached to every economic finding; policy bump → concept `HISTORICAL` via `kernel/validity.py`. |

**G0 acceptance (one command, one test):** test-mode task + payment → **exactly 1** kernel event and 1 `capital_flow` signal, retrievable by the retrieval cascade; replaying the same `event_id` yields 0 new rows; DLQ path proven by injecting a malformed row; actor on every row is the agent account.

### W2 — Money safety (FIN-01/02/04/05/08, OPS-01/03/04)
| Task | Change | Acceptance |
|---|---|---|
| W2.1 ✅ | `lib/money.js` + `schema/money.js`: mode/kill/cap; `ledger._recordPayment` gate | disabled mode blocks every booking |
| W2.2 ✅ | kill switch row + aggregate daily cap at the ledger; env `MONEY_MODE` overrides | kill switch blocks with `MONEY_KILL_SWITCH` |
| W2.3 ✅ | 8 states: `TRANSITIONS` + DB triggers (`ensureGuards`); illegal status aborts | probe: `SQLITE_CONSTRAINT: invalid ledger status` |
| W2.4 🟡 | WAL + `busy_timeout`; `scripts/backup.js` (VACUUM INTO + sha256 + `--restore-drill`). **Not encrypted**, no off-machine copy | drill restores and opens |
| W2.5 ✅ | `scripts/ledger_audit.js` (6 invariants) + `/api/health` | exit 1 on failure; 6/6 on dev DB |
| W2.6 ✅ | `lib/audit.js` chain; wired to policy, kill switch, approvals; `GET /api/pie/money/audit/verify` | tamper test fails at the edited row |
| W2.7 | escrow behind `MONEY_MODE=live` + recorded legal sign-off flag; manual-payment record path (fixed price, invoice, human approver) | contract completes with `escrow=off` |

### W3 — Revenue sprint (REV-01/02/03/04/06/07, STR-03/05)
| Task | Change | Acceptance |
|---|---|---|
| W3.1 ✅ | `scripts/funnel.py` (`modules/economy/funnel_report.py`): stage counts, responses by class, revenue/cost/margin, `time_to_first_revenue` from `transactions` | returns real numbers from `market.db`, no placeholders |
| W3.2 ✅ | GeM **CSV import** (`modules/economy/sources/gem_csv.py`) → `discovery.normalize_raw(source="gem")`; remove the "deferred" stub only when a real file parses | 20 rows → 20 prospects with `source="gem"`, provenance non-seed |
| W3.3 ✅ | `modules/economy/qc.py`: blind duplicate assignment, gold records, sampling ratio, per-record confidence, SLA/refund rule | duplicate pair disagreement is flagged; gold record mismatch blocks delivery |
| W3.4 ✅ | `modules/economy/assembly.py`: XLSX/CSV + methodology note + confidence columns | one artifact reproducible from a template run |
| W3.5 *(FF)* | real `send` transport (SMTP/API) behind `approval_gate` + domain SPF/DKIM/DMARC + STOP footer + bounce handling | dry-run default; one approved send recorded with provider id |
| W3.7 ✅ | `delivery.assign_executors` / `capacity_plan` / `cost_per_verified_record` + `scripts/capacity.py` (REV-03) | 100 records → 1 agent-day, QC 0.5 h, cost/record 12.5, floor 13.89 |
| W3.6 ✅ (logic) | `modules/economy/approvals.py` + `scripts/approvals.py`; UI not built — the only frontend work permitted | money + external contact stay manual |

**Parallel, operational (no code):** 20 qualified prospects/day → 5 approved offers/day → 1 paid pilot. Metric: `time_to_first_revenue`. No new module until gate **G1**.

### W4 — Ops (OPS-01/02/03/05/06/07)
| OPS-01 ✅/🟡 | `deploy/pie.service`, `scripts/healthcheck.py`, `scripts/backup.py` + `--restore-drill` | drill opens 3 DBs; off-machine still unset |
| OPS-02 ✅ | `.github/workflows/ci.yml` (secret scan, path check, fast tier, kernel smoke) | workflow committed |
| OPS-03 ✅ | `scripts/secret_scan.py` + `.env.example` | 0 hits on repo; fake key fails |
| OPS-05 ⬜ | blocked: no Node runtime for Next.js upgrade/`npm audit` | — |
| OPS-06 ✅ | `codebase/paths.py` + env overrides | `describe()` prints roots |
| OPS-07 ✅ | `agent_core/llm_cost.py` + engine hook | budget stop + per-task INR rows |

CI workflow (fast tier + kernel smoke + drift/contract), `.env.example` + secret scan + rotation, env-var paths (`$PIE_ROOT`), LLM per-loop token/₹ budget + cost log per task so `unit_economics` includes AI cost, Next.js upgrade + `npm audit`.

### W5 — Cognition — ✅ closed in iteration 7
| KRN-02 ✅ | `relation_retriever.py` (city relations, `explain` paths) + `retrieval_engine.retrieve_relations` | seed → factory `requires` grid path |
| KRN-06 ✅ | `hypothesis/claim_strength.py`, enforced in `kernel_bus.publish_observation` | overstated `VALIDATED_OOS` downgrades to `HYPOTHESIS` |
| KRN-04 ✅ | `PRAGMA busy_timeout` (RO+RW) + doctor journal/timeout/write probe | doctor shows 2500 ms when env set |
| KRN-07 ✅ | `min_support` config + `n` in consolidated metadata and search results | single-run support allowed explicitly |
| KRN-05 ✅ | `kernel/usage.md` restamped with 14/15 | — |
| KRN-03 ⬜ | gate false-negative rate still unmeasured | needs adversarial corpus |

### W6 — Twin/sim validity — ✅ closed in iteration 8–9
| TWN-01 ✅ | `city_state.coverage`/`is_placeholder` over 10 `FIELDS`; `city_series` validation + merge; `scripts/twin_coverage.py`; 5 cited rows + gap manifest | Kanpur 3 observed / 5 placeholder / 2 missing; Delhi 4 / 5 / 1 |
| SIM-01 ✅ | `popula_dyn/core/scale.py` (`scale_invariance`, `level_drift`, `weight_per_agent`, `stratified`, `confidence_interval`); `auto_scale_grid` keeps land/agent constant | 400/2k/10k: baseline 1.774/1.773/1.776, effect +1.52/+1.58/+1.52% |
| SIM-02 ✅ | `simulation_version.run_key/param_hash/seed_set/same_regime`; `simulation_runs.run_key`; gate filters cross-regime | SQLite round-trip; sweep = new regime |
| SIM-03 🟡 | Phases A–E ∈ iterations 10–15 (domain pack, utilities, calibration, profit-share, hire determinism, dividend timing, promotion gate) | fit on target; Kanpur power capex `FALSIFICATION_PASSED`; Delhi levers ~1% (noise) and Kanpur transport fails seed shift → `HYPOTHESIS` |

### W7 — G1 last mile — ✅ closed in iteration 9 (REV-06 remains)
| STR-05 ✅ | `approval_store.py` + `/approvals` page; same tier/self-approval rules as the CLI | tier 3 needs two distinct humans |
| REV-07 ✅ | `economy/portal.py` + `/portal/{token}` page; accept → invoice → download; operator `paid` writes one ledger tx | magic link, idempotent invoice, traversal-safe download |
| REV-06 🟡 | real send transport + DPDP/TRAI/SPF-DKIM sign-off | needs provider + counsel |
| OPS-01 🟡 | local backup/restore done; encrypted off-machine copy unset | needs `BACKUP_REMOTE` + `age`/`gpg` |

## 3. What "done" looks like per ID

Every closed ID must produce, in `04_iteration_log.md`: ID · file+symbol · test name · gate moved · metric before/after. An ID may only move to ✅ when a **test** (not a doc) proves it, and `02`/`03` are updated in the same commit. S1 items that slip twice must be reported to the advisor as a blocker (`01_session_playbook.md` §8).

## 4. Explicit non-goals (STR-01, master §4)

No new social/UI surface, no marketplace launch, no compute/data marketplace productisation, no industrial flywheel, no moonshot ladder, no `eco_sim` build, no second persistence path, no second "brain" in FireFlow.

## 5. Remaining work (open at iteration 15)

### Blocks G1 (first paid pilot)
| ID | State | What is missing | Unblocked by |
|---|---|---|---|
| REV-06 | 🟡 | Real send transport; DPDP/TRAI applicability; SPF/DKIM/DMARC; STOP + bounce handling | Provider choice + counsel sign-off |
| OPS-01 | 🟡 | Encrypted off-machine copy of `kernel.db`, `market.db`, FireFlow DB, secrets | `BACKUP_REMOTE` target + `age`/`gpg` |
| FIN-02 | 🟡 | Escrow is a regulated-activity question; no-escrow path is implemented and usable | Counsel/CA decision (or stay `escrow=off`) |
| REV-01/02 | 🟡 | A real paying customer, not code: 20 qualified prospects → 5 approved offers → 1 paid pilot | Founder execution |

### Quality / evidence (not G1 blockers)
| ID | State | What is missing |
|---|---|---|
| TWN-01 | ✅ 7/20 observed | 3 cited rows: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours` (candidates in `data/twins/series/manifest.json`) |
| SIM-03 | 🟡 Phases A–E done | One lever promoted (Kanpur power capex); Delhi levers are noise after the dividend fix; Kanpur transport fails seed shift |
| KRN-03 | ⬜ | Gate false-negative rate needs the adversarial eval corpus |
| C3 OOS forecast | 🟡 | Held-out historical indicators reproduced within tolerance (baseline pop err 0.036 at cap 400) |
| C4 promotable finding | 🟡 | Kanpur power capex `FALSIFICATION_PASSED`; iteration-14 three-lever claim withdrawn (dividend-timing artifact) |
| TWN-02/03 | ⬜ | Value-of-information ranking; third-city adapter-only proof |

### Operational / deferred
| ID | State | Note |
|---|---|---|
| OPS-05 | ⬜ | Next.js upgrade needs Node (absent on this host) |
| KRN-05 follow-up | ✅ | Manual restamped; re-stamp only when the smoke result changes |
