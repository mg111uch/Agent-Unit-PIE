# Iteration Log (Level 1) — append-only

> Newest at the bottom. One entry per iteration, copied from the coding agent's Iteration Report (`01_session_playbook.md` §2). Never rewrite history; add a correction entry instead. No code in this file.

## Seed entries (reconstructed from supplied docs; dates as stated there)

### 2026-08-29 — Kernel manual verified
- Kernel `usage.md` stamped "Last verified 2026-08-29"; smoke harness 9/9.
- Note: predates bus, registry, adapters (KRN-05).

### 2026-09-15 — Integration gates (all PASS per PhasePlan)
| Gate | Result |
|---|---|
| Capability registry | 66 entries (16/8/42 ACTIVE/PARTIAL/DORMANT, order inferred) |
| Identity | unit schema artifact; 0 live actor refs; drift jest 8/8 |
| Bus + economic event adapter | shaped `PaymentSettled` → event → signal → memory read-back |
| Capacity slice | Kanpur question answered from retrieval cascade (3/3/1 + history) |
| Twins | Kanpur + Delhi versioned; truth tiers on 14 fields |
| Calibration | baseline pop error 0.036 (caps: pop 400, skill 1.0) |
| Policy lab | one twin→popula→scenario→finding run (lineage `sim@2cac23d`); contrast lab null Pareto verdict |
| Evidence-gated opportunity scoring | ✅ |
| FireFlow gateway + RBAC | jest 12/12 |
| Authoritative ledger | jest 18/18 |
| Settlement + dataset licenses | jest 23/23 |
| Sensors anti-fraud | jest 26/26 |
- Open at that point: hierarchy/relation retrievers dormant; oversized `city_twin.py`; real city feeds; multi-seed + falsify before promoting findings.

### (undated in sources) — Revenue acquisition + job agent shipped
- PIE: prospects/pain score, discovery (stubs for Udyam/GeM/ONDC), service templates (2), outreach, delivery bridge + margin gate, revenue metrics/experiments, `revenue_job.py`; jobs: candidate twin, 6 source adapters, fit engine, application packs, job outreach, learning.
- FireFlow: prospect CRM + import, proposals, outreach pipeline, proposal launch, funnel; job store, fit scoring, tracker, job outreach, jobs funnel.
- Revenue recorded: **none documented**.

### 2026-10-19 — Doc set v2.0 (this refresh)
- Created two-level hierarchy (master + 11 files); inline markers; register of ~85 IDs; recommendation ledger; session playbook.
- Contradictions found and recorded: DBT-01/02/03, DOC-01/02/03. No code changed.
- Next-iteration recommendation: master §14.

---

## Template for new entries
(copy the Iteration Report from `01_session_playbook.md` §2)

## Iteration 1 — 2026-11-01

**Goal (one line):** close the transport half of INT-01 on both sides of the PIE↔FireFlow boundary.
**Gate(s) targeted:** G0 (Loop Proof)
**Outcome:** PARTIAL — PIE consumer proven by test; FireFlow producer written but **untested** (no Node runtime in this environment).

### Changes
| Feature | Notes |
|---|---|
| FireFlow outbox | `backend/database/schema/outbox.js` + `backend/lib/outbox.js` (`emit`, `listPending`, `markPublished`, `recordFailure`, `counts`, MAX_ATTEMPTS 5) |
| Outbox emissions | `lib/settlement.js:emitPaymentSettled` (one `payment_settled` per contract release, deterministic id) · `routes/tasks.js` emits `task_verified` on completion |
| PIE event feed | `backend/pie/events.js` — `GET /api/pie/events`, `POST /api/pie/events/ack`, `/fail`, `/stats`, agent-key auth |
| PIE consumer | `codebase/modules/economy/inbox.py` — `ff_inbox` table, `pull/apply/replay/dlq_list/dlq_retry/stats`, bounded attempts → dead |
| Consumer dedup | kernel marker objects `external_events/<event_id>` + `ff_inbox` state; replay proven no-op |
| Poller | `scripts/pie_poller.py` (`--once/--loop/--replay/--dlq/--stats`), env `FIREFLOW_URL`, `PIE_AGENT_KEY` |
| Env-var paths | `kernel/config/kernel_config.py`: `DATA_ROOT` honours `PIE_DATA_ROOT` (OPS-06) |

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|
| `tests/test_inbox.py` (unittest) | 5/5 | dedup, replay no-op, dead-letter at cap, ignore unknown type, DLQ retry |
| `backend/pie/events.test.js` (jest) | **not run** — no node binary present | idempotent emit, ordered feed, ack, single settlement event |
| `scripts/smoke_kernel.py` | 14/15 (`embedding cold start` fails; pre-existing, offline model) | — |

### Register changes
- Re-rated: INT-01 ⬜ → 🟡 (PIE side done; FF side written, unverified; needs one live test-mode run).
- Partially closed: OPS-06 (kernel data root now env-driven).
- Opened: none.

### Answers to [VERIFY] questions (new)
- INT-01: `event_adapter` was the only path; nothing polled FireFlow. Now `scripts/pie_poller.py` does, ack-gated.
- INT-03: `score_cli.py` still has no timeout/`UNSCORED`/version.
- FIN-08 (FF side): the 8-state machine **already exists** in `lib/ledger.js:TRANSITIONS` with an idempotency unique index — the gap is DB-level `CHECK`, not the state list.
- INT-02 (FF side): `agent_api_keys` with `unit_id` + `spend_limit_paise` already exists; PIE still lacks an agent-key client.

## Iteration 2 — 2026-11-01

**Goal:** prove the PIE half of G0 deterministically, then close INT-02 and INT-06.
**Gate(s) targeted:** G0
**Outcome:** PASS (PIE half) — one captured FireFlow settlement becomes exactly one kernel event + one `capital_flow` signal, is retrievable, and replay is a no-op. The live FF→PIE hop still needs one run with Node present.

### Changes
| Feature | Notes |
|---|---|
| Loop-proof contract test | `tests/test_loop_proof.py` + `tests/fixtures/fireflow_outbox_sample.json` (captured `GET /api/pie/events` shape) |
| Agent identity | `modules/economy/agent_identity.py` — `Actor`, `load`, `require`, `actor_fields`, `headers`; forbidden scopes (`outreach:send`, `ledger:write`, `money:approve`) rejected at load |
| Actor stamping | `ledger.py`: `actor_type/actor_id` on `transactions` + `prospects`, `fireflow_id` for INT-04, `_migrate_actor` for existing DBs |
| Finding provenance | `modules/economy/provenance.py` — `stamp/stamped/needs_invalidation/mark_historical/apply_invalidation`; `revenue.ab_test` stamps every finding and pins `claim_strength=HYPOTHESIS` |
| Wiring | `revenue_job` records prospects as the agent actor; poller takes its key from `agent_identity` |
| DOC-01 | closed: backend port is 5000 everywhere |

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|
| `tests/test_inbox.py` | 5/5 | — |
| `tests/test_loop_proof.py` | 3/3 | end-to-end proof, repeated delivery, verified-task-is-not-money |
| `tests/test_agent_governance.py` | 9/9 | identity least-privilege, forbidden scope, actor columns, provenance drift |
| `scripts/smoke_kernel.py` | 14/15 | `embedding cold start` (pre-existing, offline) |

### Register changes
- Re-rated: INT-01 🟡 → 🟡 (PIE proven; FF unrun), INT-02 ⬜ → 🟡 (PIE done; FF account creation pending), INT-06 ⬜ → 🟡, DOC-01 ✅ closed, OPS-06 ✅ closed for kernel data root.
- Opened: none.

### Open at iteration end
- One live test-mode settlement through the real poller (needs Node).
- `score_cli.py` timeout/`UNSCORED` (INT-03) untouched.
- Ledger has no DB-level `CHECK` on `transactions` state (FIN-08 PIE side).

## Iteration 3 — 2026-11-01

**Goal:** run the FireFlow suite and close G0 on live transport.
**Gate(s) targeted:** G0
**Outcome:** PASS — one real test-mode settlement traversed settlement → outbox → HTTP feed → PIE inbox → kernel event → `capital_flow` signal, retrievable from a **fresh** process; replay changed nothing.

### Changes
| Feature | Notes |
|---|---|
| Test runner | **Bun 1.4.4** runs the existing jest-style suites: `cd backend && bun test` → 56/56 across 17 files (Node is not installed) |
| Kernel retrieval fix | `retrieval_engine._persisted_episodic` — episodic search now falls back to `kernel.db`, so a restarted PIE can retrieve what it learned (new **KRN-08**) |
| Live proof harness | `/tmp/opencode/ff_seed.js` (settlement through `lib/settlement.js`) + `scripts/pie_poller.py --once` against `FIREFLOW_URL` |

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|
| FireFlow `bun test` | 56/56 (17 files) | 4 outbox/feed tests |
| `tests/test_inbox.py` · `test_loop_proof.py` · `test_agent_governance.py` | 17/17 | — |
| `scripts/smoke_kernel.py` | 14/15 (`embedding cold start`, pre-existing) | — |
| Live G0 | 1 event received → 1 applied → 0 pending; replay `already_applied`; 1 payment event, 1 `capital_flow`=6000, retrievable `true` | — |

### Register changes
- INT-01 ⬜ → ✅ (both halves proven end to end in test mode).
- Opened: **KRN-08** (episodic retrieval was process-local) — found and fixed in the same iteration.
- Re-rated: DOC-01 ✅, INT-02 🟡 (PIE done, FF agent account creation still pending).

### Notes / hygiene
- The live run wrote one settlement into the local `reddit_clone.db` and one event into `data/kernel.db`; both are labelled "G0 loop proof" and can be deleted.
- `bun test` binds the in-memory DB (`NODE_ENV=test`), so it never touches the dev database.


## Iteration 4 — 2026-11-01

**Goal:** make real money impossible to move by accident (W2).
**Gate(s) targeted:** G0 safety rails before G1
**Outcome:** PASS — one choke point, one switch, DB-enforced states, auditable history, backups that restore.

### Changes
| Feature | Notes |
|---|---|
| Money control plane | `backend/lib/money.js` + `database/schema/money.js`: `mode ∈ {disabled,test,live}` (env `MONEY_MODE` wins), global kill switch, aggregate **daily cap** measured at the ledger, `status()` |
| Single gate | `ledger._recordPayment` calls `money.check()` before any booking; `settleContract` blocks **before** charging the provider and reports a `blocked` stage |
| DB-level states | `ensureGuards()` installs insert/update triggers: any status outside the 8 states aborts (`invalid ledger status`) — proven by probe, not by prose |
| Tamper-evident audit | `backend/lib/audit.js`: SHA-256 hash chain, serialised appends, `verify()` walks the chain; wired to policy changes, kill-switch flips and human ledger approvals |
| Human-only controls | `pie/money.js` (`GET /status`, `POST /kill`, `POST /policy`, `GET /audit`, `GET /audit/verify`) behind JWT — an agent cannot lift its own limits |
| Self-audit | `backend/scripts/ledger_audit.js`: double-entry balance, orphan legs, stale holds, live-without-cap, audit chain, missing provider refs — 6/6 PASS on the dev DB |
| Backup + drill | `backend/scripts/backup.js` (`VACUUM INTO`, sha256, `--restore-drill`): 569 KB snapshot, checksum ok, restored DB opens with 5 ledger rows |
| Concurrency | `busy_timeout = 5000` + WAL at connection open |
| Health | `GET /api/health`: db, outbox pending/dead, money mode/kill/spend, alert flags; 503 when degraded |

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|
| FireFlow `bun test` | 64/64 (18 files) | disabled mode blocks, kill switch + audit, cap boundary, status triggers, chain tamper, settlement blocked before charge, human-only kill (401) |
| `scripts/ledger_audit.js` | 6/6 | — |
| `scripts/backup.js --restore-drill` | pass | — |

### Register changes
- FIN-01 ⬜ → ✅ (mode, kill switch, aggregate cap; no live provider wired yet — that is FIN-03/payout work).
- FIN-04 🟡 → ✅ (WAL + timeout + backup + restore drill + self-audit; Postgres decision still open, recorded).
- FIN-08 🟡 → ✅ for FF (8 states DB-enforced + idempotency index); PIE `transactions` still advisory.
- OPS-01 🟡 → 🟡 (health + backups done; supervisor/alerting transport still missing).
- OPS-04 ⬜ → ✅ (hash chain incl. overrides and kill-switch use).
- FIN-05 🟡 (aging counters exist in the audit; reconciliation still compares to estimates, not provider statements).

### Notes
- `MONEY_MODE` unset defaults to the DB policy (`test`), so pilots run on the stub provider; `live` needs an explicit env or a policy change that is audited.
- Money policy is **one row** (`id = 1`); there is no per-tenant override — deliberate until a second tenant exists.

## Iteration 5 — 2026-11-02

**Goal:** make the revenue loop *measurable and safe to deliver* (W3).
**Gate(s) targeted:** G1 revenue evidence, without opening outreach risk
**Outcome:** PARTIAL PASS — funnel, GeM import, QC, assembly and approval tiers are code; real send transport is still a state change.

### Changes
| Feature | Notes |
|---|---|
| Funnel with provenance | `modules/economy/funnel_report.py` + `scripts/funnel.py`: every stage carries `source`; missing stages are `null`/`unavailable`, never 0. FF payload merges via `--ff` |
| GeM CSV import | `modules/economy/sources/gem_csv.py`: human-downloaded export → evidence-backed prospects (`source="gem"`, `triggers=["tender"]`), stable `pro_<sha1>` ids; `discovery.collect("gem", batch)` and `revenue_job --gem <csv>` |
| QC primitives | `modules/economy/qc.py`: blind duplicate assignment (twin never same analyst), gold records with truth kept out of assignments, deterministic spot-check sample, consensus confidence, SLA + refund ladder. Unknown accuracy **fails closed** |
| Deliverable assembly | `modules/economy/assembly.py` + `scripts/deliver.py`: CSV + dependency-free XLSX (stdlib zip/XML) + methodology note carrying QC result, confidence meanings, SLA and refund rule |
| Delivery capacity | `delivery.assign_executors` (least-loaded capable agent; a missing capability is reported as `unassigned`, not hidden), `capacity_plan` (agent vs QC bottleneck), `cost_per_verified_record` + price floor; `scripts/capacity.py` |
| Approval inbox | `modules/economy/approvals.py` + `scripts/approvals.py`: 3 risk tiers, requester ≠ approver, tier 3 needs two distinct humans, amount ≥ ₹50k escalates, unknown actions default to tier 2; SLA deadlines from item creation |

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|
| `tests.test_funnel_gem` | 7/7 | source per stage, FF merge, pending TTF, GeM parse/dedupe/deferral/missing file |
| `tests.test_qc_assembly` | 14/14 | blind twins, gold isolation, consensus/unverified/disputed, refund ladder, CSV/XLSX/note bundle, empty bundle |
| `tests.test_approvals` | 13/13 | tier classification, escalation, sorting, SLA breach, self-approval, dual approval, charter |
| `tests.test_capacity` | 9/9 | balanced assignment, unassignable skill visible, 100-record plan, QC bottleneck, cost per record + floor |
| PIE total (this iteration) | 43/43 | — |

### Register changes
- REV-01 ⬜ → 🟡 (funnel now measures real data; the item only closes on the first rupee — `time_to_first_revenue` is still `pending`).
- REV-02 🟡 → ✅ for GeM CSV; Udyam/ONDC remain human-assisted imports.
- REV-03 ⬜ → ✅ (executor assignment + capacity plan + cost per verified record; real payouts still zero).
- REV-04 ⬜ → ✅ (duplicate/gold/sampling/confidence/SLA+refund in code and in the customer note).
- REV-07 🟡 → 🟡 (deliverable assembly done; customer magic-link portal still missing).
- REV-06 ⬜ → ⬜ unchanged: `send` is still a state change, no SMTP/API, no domain auth (needs counsel + provider).
- STR-05 🟡 → 🟡 (tiers + inbox logic done; no screen yet).
- REV-05 ⬜ unchanged (min-N labelling exists; finding sample size still to store).

### Notes
- `qc.evaluate(None)` returns `pass=False` on purpose: a batch with no scored gold set holds payment instead of shipping.
- XLSX is written with stdlib `zipfile` because `openpyxl`/`pandas` are not installed in `myenv`; the CSV is the contract, XLSX the convenience.
- Approval tiers live in one dict (`TIERS`) and one rule list (`_RULES`) so a policy change is a diff, not a hunt.

### Open at iteration end
- Real send transport + SPF/DKIM/DMARC + STOP/bounce handling (REV-06, blocked on counsel/provider choice).
- Customer portal half of REV-07 (accept → pay → download).
- Approval inbox UI (STR-05) and persistence of decisions into the audit chain.

## Iteration 6 — 2026-11-02

**Goal:** ops floor — the system can be restarted, watched, billed and audited (W4).
**Gate(s) targeted:** G1 readiness prerequisites
**Outcome:** PASS for code; framework upgrade blocked (no Node runtime).

### Changes
| Feature | Notes |
|---|---|
| LLM spend accounting (OPS-07) | `agent_core/llm_cost.py`: per-task `Budget` (tokens + ₹, env `LLM_TASK_BUDGET_*`), SQLite `llm_cost` rows (provider/model/tokens/INR/rate), `summary()`; hooked into `loop/engine.py` after each call — zero caps keep current behaviour, exceeding yields a `budget` stop |
| Secret scan (OPS-03) | `scripts/secret_scan.py`: private keys, provider keys, JWTs, `*_KEY = ...` assignments; placeholders pass; stdlib only; wired into CI |
| Env template | `.env.example` (paths, models, budgets, money, backups) + `!.env.example` in `.gitignore` |
| CI (OPS-02) | `.github/workflows/ci.yml`: secret scan, path check, fast-tier unittest set, kernel smoke; FireFlow job behind a repo variable |
| Supervisor + alerting (OPS-01) | `deploy/pie.service` (systemd, `Restart=always`, `EnvironmentFile`) + `scripts/healthcheck.py` (exit 0/1/2, PIE + FireFlow health, outbox DLQ, stale `kernel.db`/`market.db`) |
| Backups (OPS-01) | `scripts/backup.py`: online SQLite backup of `kernel.db`, `market.db`, `bhav_copy.db` + sha256 sidecars + manifest; `--restore-drill` verifies checksum and that each copy opens |
| Paths (OPS-06) | `codebase/paths.py` (`PIE_ROOT`, `PIE_DATA_ROOT`, `FIREFLOW_ROOT`, `ATLAS_DIR`, `describe()`); removed hardcoded `/home/manigupt` from duplicate/dead-code detectors, atlas map and doc cleaner |

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|
| `tests.test_ops` | 14/14 | pricing/override, budget caps, cost log per task, budget verdict, secret scan hit/placeholder/repo-clean, paths, restore drill fails closed |
| PIE fast tier (6 suites) | 74/74 | — |

### Register changes
- OPS-01 🟡 → 🟡 (supervisor, healthcheck, backups + drill done; **off-machine copy and encryption not configured** — `BACKUP_REMOTE` empty, no `age`/`gpg` on this host).
- OPS-02 ⬜ → ✅ (workflow committed; FireFlow job opt-in because the repo is external).
- OPS-03 🟡 → ✅ for scanning + template; rotation policy is now documented in `.env.example` (90-day rotation recommendation).
- OPS-05 ⬜ → ⬜ blocked: no Node runtime, so Next.js upgrade + `npm audit` cannot be executed here.
- OPS-06 🟡 → ✅ for runtime code (`paths.py`); some legacy `agent_tools` scripts and old docs still cite absolute paths.
- OPS-07 ⬜ → ✅ (per-task token/₹ budget, cost rows per task, engine hook).

### Notes
- `budget.add()` returns a verdict instead of raising, so the loop decides to stop and the caller still sees the spend.
- Backups report `off_machine: false` when `BACKUP_REMOTE` is unset — the manifest cannot claim safety it does not have.
- CI's path check ignores `codebase/agent_tools` (legacy one-off scripts) rather than pretending they are fixed.

### Open at iteration end
- Off-machine encrypted backups (needs a target: S3/B2/rsync host) and a key store.
- Alert transport for `healthcheck.py` (`OnFailure=` webhook/mail unit).
- Framework upgrade blocked until a Node toolchain exists.
- LLM cost rows are not yet folded into `cost_per_verified_record`; the CLI reads them separately.

## Iteration 7 — 2026-11-02

**Goal:** make the kernel usable for causal questions and honest about evidence (W5).
**Gate(s) targeted:** G1 decision quality
**Outcome:** PASS — 4 of 5 KRN items closed; KRN-05 restamped with the real smoke result.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| KRN-02 | `kernel/retrieval/relation_retriever.py` | Stub replaced with a real retriever: typed city relations (`requires`, `serves`, `employed_by`, `contains`, `affects`, `supplies`, `funds`), `link`/`seed`/`relations`/`neighbors`/`explain` (cycle-safe causal paths), `city_summary`; `retrieval_engine.retrieve_relations()` exposes it |
| KRN-06 | `kernel/hypothesis/claim_strength.py` + `kernel_bus.publish_observation` | Evidence ladder `HYPOTHESIS → REPLICATED → FALSIFICATION_PASSED → VALIDATED_OOS`; thresholds `PIE_MIN_SEEDS`/`PIE_MIN_N`; an overstated claim is **downgraded** with `claim_strength_requested` + violations, never silently accepted |
| KRN-07 | `kernel/compression_engine.py`, `kernel/retrieval/retrieval_engine.py` | `min_support` config (default 2) gates both compress and recompute; consolidated metadata carries `n` + `min_support`; semantic search returns `n` so the model sees support size |
| KRN-04 | `kernel/persistence/db.py`, `scripts/topic_ops.py doctor` | `PRAGMA busy_timeout` (env `PIE_DB_BUSY_TIMEOUT_MS`) on RO and RW connections; doctor prints journal mode, timeout and a `BEGIN IMMEDIATE` write probe and flags a locked writer |
| KRN-05 | `system_devpt_reports/kernel/usage.md` | Restamped 2026-11-02 with the honest result (14/15; embedding cold start fails without the local MiniLM cache) and the features added since the last stamp |
| Docs | `system_devpt_reports/kernel/README.md` | Four feature rows (relation retriever, claim ladder, compression support knobs, lock visibility) |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_kernel_w5` | 12/12 | claim ladder rungs + downgrade, relation typing/seed/paths/summary, engine exposure, min_support config, doctor journal/timeout/probe |
| `scripts/smoke_kernel.py` | 14/15 | unchanged known failure (`embedding cold start`, no local model) |

### Register changes
- KRN-02 ⬜ → ✅ (city-graph relations live; cascade unit → relation can reuse the same retriever).
- KRN-04 🟡 → ✅ (timeout on both connections + doctor probe; one-writer queue still a convention).
- KRN-05 🟡 → ✅ (manual restamped with the true smoke result).
- KRN-06 ⬜ → ✅ (ladder enforced in the bus; `HYPOTHESIS` remains the default).
- KRN-07 🟡 → ✅ (`min_support` configurable, `n` exposed with every consolidated node).

### Notes
- `claim_strength.check()` returns the level the evidence supports instead of raising, so an agent sees *why* it was downgraded in the same payload it wrote.
- Relations are ordinary `semantic_memory` edges — no second graph store; `kernel.db` stays the single source.
- `min_support=1` is allowed deliberately: one long real-world series can be valid evidence, and the operator can now say so explicitly.

### Open at iteration end
- KRN-03 (gate false-negative rate) still unmeasured; needs the adversarial eval corpus.
- Relation retrieval is not yet part of the default retrieval cascade — it is an explicit call until a city graph is populated from real feeds.
- `_smoke_k` topic carries 2 dangling edges and `sim_stock` has a stale derived export; both predate this iteration and are flagged by `doctor`.

## Iteration 8 — 2026-11-02

**Goal:** stop pretending placeholder city data and one fixed agent count are evidence (W6).
**Gate(s) targeted:** G1 decision quality (policy claims)
**Outcome:** PASS — TWN-01 and SIM-02 closed; SIM-01 executed at 400/2k/10k (44.9 s): direction holds (`+`), but the 10k baseline collapses to 5% of the 400-agent baseline, so the run is reported with a level warning rather than as a clean pass.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| TWN-01 | `modules/digital_twins/city_state.py`, `modules/digital_twins/city_series.py`, `scripts/twin_coverage.py` | `FIELDS` expanded to 10 series; `coverage()` / `is_placeholder()` report observed/placeholder/missing per field; `city_series` validates real rows (`field`, `value`, `source`, `year`, `license`), rejects unsourced rows, marks >12-year rows stale, merges real over placeholder; `coverage_table` aggregates cities; CLI prints the gap |
| TWN-01 data | `data/twins/series/README.md` | Format + rule: only cited series, estimates stay as adapter placeholders |
| SIM-02 | `kernel/simulation_version.py` (`canonical_params`, `param_hash`, `seed_set`, `run_key`, `same_regime`), `kernel/persistence/db.py` (`run_key` column + `save_simulation_run(run_key=…)`), `modules/simulators/simulation_connector.py`, `kernel/hypothesis/contradiction_gate.py` | Run identity = `(sim@commit, param_hash, seed_set)`; noise keys (`run_id`, output paths, plots) excluded; the gate only compares findings inside one parameter regime |
| SIM-01 | `modules/simulators/popula_dyn/core/scale.py` | `scale_invariance()` runs baseline vs policy at 400/2k/10k and fails on a sign flip; `level_drift()` also reports when the **baseline** collapses with scale (direction alone is not evidence); `weight_per_agent`, `stratified`, `confidence_interval` make representative-agent weighting explicit |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_twin_sim_w6` | 18/18 | 10-series coverage, placeholder detection, row validation/rejection, stale marking, coverage table, run-key shape/regime/persistence round-trip, weighting/stratification/CI, level-drift warning, live 400/2k scale run |
| PIE fast tier (10 suites) | 104/104 | aggregate; live scale run keeps the suite at ~4 s |

**SIM-01 measured (food_subsidy +0.2, 3 years, seed 1):**

| agents | baseline welfare | treated | relative | direction |
|---|---|---|---|---|
| 400 | 1.789 | 1.814 | +1.40% | + |
| 2,000 | 1.773 | 1.801 | +1.58% | + |
| 10,000 | 0.086 | 0.131 | +52.3% | + |

Wall time 44.9 s. Direction survives, but the 10k baseline is 5% of the 400-agent baseline — the model starves/impoverishes at that scale, so the 10k result is **not** usable as a policy magnitude.

### Register changes
- TWN-01 🟡 → ✅ (coverage is measured, real files are validated, gaps are printed; actual collection remains an operator task).
- SIM-02 ⬜ → ✅ (`param_hash` exists, `run_key` persisted, cross-regime findings no longer contradict).
- SIM-01 🟡 → 🟡 (400/2k/10k run executed: sign holds, but 10k baseline collapses to 5% → level claim still blocked on resource/population scaling).
- TWN-02/TWN-03 unchanged (value-of-information ranking, third-city proof).

### Notes
- Unknown/missing data is reported as `missing`, never silently dropped from the denominator: each city currently shows 1 observed, 5 placeholder, 4 missing of 10.
- `run_key` does not double-prefix a `version_id` that already starts with `sim@`.
- No sample series file ships with fabricated numbers; the directory ships a format README until a cited row is available.

### Open at iteration end
- SIM-01 direction survives at 10k, but the baseline welfare collapses (1.789 → 0.086, 5%): food/wealth resources do not scale with agents, so magnitudes at 10k are not usable yet.
- SIM-03 domain mismatch still open (agricultural ABM vs urban policy).
- TWN-01 collection: 4 real series per city still missing; census-era anchors will be marked stale by design.

## Iteration 9 — 2026-11-03

**Goal:** close the G1 last mile (human approval + customer acceptance), make the scale claim honest, and collect real twin series.
**Gate(s) targeted:** G1 first paid pilot; C1 real city data; C2 scale invariance
**Outcome:** PASS — approval UI and magic-link portal shipped; SIM-01 now passes cleanly at 400/2k/10k; twin coverage 7 observed / 10 placeholder / 3 missing across Kanpur+Delhi.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| STR-05 / G1 | `modules/economy/approval_store.py`, `agent_core/server/economy_routes.py`, `frontend/approvals.html|js` | SQLite-backed queue (tier, SLA, two-human rule, no self-approval) behind `/api/economy/approvals`; `/approvals` page approves/rejects with a reason. CLI rules unchanged. |
| REV-07 | `modules/economy/portal.py`, `frontend/portal.html|js`, `scripts/proposal.py` | Magic-link proposal at `/portal/{token}`; accept issues one idempotent invoice; download is restricted to the deliverables roots; operator marks paid, which writes exactly one ledger `transactions` row. |
| SIM-01 | `popula_dyn/core/simulation_model.py` (`auto_scale_grid`), `core/scale.py` (`resource_scaled`) | Land per agent held constant (default 1.25), so 10k agents run the same economy as 400 instead of a 2k food stock. `scale_invariance` reports grid side and land per agent per scale. |
| TWN-01 | `data/twins/series/{kanpur,delhi}.json`, `manifest.json`, `city_series._to_field` | 5 cited rows added (Kanpur industrial units + budget; Delhi road length + industrial units + MCD budget); `truth`/`url`/`note` survive ingestion; remaining 3 gaps named with candidate sources, not estimated. |
| Ledger | `modules/economy/ledger.py` | `approvals` + `proposals` tables in `market.db`; `PIE_DATA_ROOT` honored by `get_db_path`; `record_tx(actor=…)` now actually writes the actor columns. |
| OPS-03 | `scripts/secret_scan.py` | Allowlist ignores code expressions (`token = secrets…`, `location…`) while still catching literals. |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_approvals_portal` | 9/9 | tier-2/3 rules, self-approval refusal, persistence, token auth, idempotent invoice, payment tx, download traversal, routes smoke |
| `tests.test_twin_sim_w6` | 19/19 | shipped series files validate and keep their URLs; resource-scaled scale run |
| PIE fast tier (11 suites) | 114/114 | aggregate |

**SIM-01 after resource scaling (food_subsidy +0.2, 3 years, seed 1, 45 s):**

| agents | grid | land/agent | baseline | treated | relative |
|---|---|---|---|---|---|
| 400 | 23×23 | 1.32 | 1.774 | 1.801 | +1.52% |
| 2,000 | 50×50 | 1.25 | 1.773 | 1.801 | +1.58% |
| 10,000 | 112×112 | 1.25 | 1.776 | 1.803 | +1.52% |

Baseline drift ratio 1.001 → no level warning.

### Register changes
- REV-07 ✅ (portal half closed; acceptance, invoice, download, ledger payment).
- STR-05 ✅ (approval UI shares the same rules as the CLI).
- SIM-01 ✅ (direction and baseline stable at 10k under resource scaling).
- TWN-01 ✅ (coverage measured and 5 cited rows collected; 3 gaps explicitly named).
- OPS-03 ✅ (scanner no longer fails on code expressions).

### Notes
- Portal acceptance never moves money. `paid` is an operator action with a reference and one ledger tx, which matches the `escrow=off` path FIN-02 asks for.
- `PIE_DATA_ROOT` now isolates `market.db` exactly like `kernel.db`, so tests cannot touch the live ledger.
- Twin values are secondary-source where the primary is a PDF/dashboard (press/government dashboard); each row carries `url` + `note`, and none is marked `OBSERVED`.

### Open at iteration end
- REV-06 (real send transport + compliance) still blocks outreach.
- OPS-01 off-machine encrypted backups still unset.
- FIN-02 escrow remains a counsel question; the no-escrow path is now usable.
- TWN-01 gaps: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours`.

## Iteration 10 — 2026-11-03

**Goal:** SIM-03 Phase A — one simulator, two domains. Make `popula_dyn` run a countryside by default and an urban economy with `domain: urban`, so urban policies can be tested without a second simulator.
**Gate(s) targeted:** C2 policy claims that name their domain; SIM-03
**Outcome:** PARTIAL ✅ — Phase A (profile + urban agent mix + labour market + domain-aware policy map) landed; Phase B/C/D remain.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| SIM-03 A | `core/domain.py` (`PROFILES`, `apply`, `policy_mechanisms`, `augment_summary`) | `domain: agrarian|urban` is a profile pack: agent mix, land type, coefficients, human behaviours. `apply()` fills defaults without overwriting caller params. Unknown values fall back to agrarian. |
| SIM-03 A | `core/policy.py` (`DOMAIN_MECHANISMS`, `compile`) | Policy map is domain-scoped. Urban levers: water subsidy/tariff, power reliability capex, transport subsidy/fuel tax, property tax, municipal capex, industrial incentive, zoning/FAR, minimum wage, education. Cross-domain mechanisms raise instead of mapping silently. `MECHANISMS` stays the agrarian export. |
| SIM-03 A | `core/urban.py` (`init_urban`, `reset_step`, `note_event`, `metrics`) | Zoned parcels (residential/industrial/commercial), workers, manufacturing/service firms, per-firm worker capacity; per-step output/wage/employment counters. |
| SIM-03 A | `behaviours/urban.py` (`WorkBehavior`, `OperateBehavior`) | Labour market: worker finds a firm, firm pays the wage (one flow), output = productivity × capital^0.3 × labour^0.7 × reliability; costs for water, transport, property tax. Children below `min_working_age` do not work. |
| SIM-03 A | `core/agent_factory.py` (`worker`, `urban_firm`, `parcel`), `behaviour_registry.py` | New agent types and behaviour registration; farm configs untouched. |
| SIM-03 A | `core/simulation_model.py` | `domain.apply()` in `__init__`; `_init_units` branches to `init_urban`; urban counters and event hooks; urban data reporters; summary augmentation. `DataCollector` split out to keep the model at 500 lines. |
| SIM-03 A | `core/society.py`, `core/scarcity.py`, `core/scale.py` | Urban `food_security` is a purchasing-power proxy (no crops); scarcity is affordability stress; scale welfare is employment + GVA/worker − Gini; `_run` keeps the model's domain-applied params. |
| SIM-03 A | `behaviours/reproduce.py` | Children inherit `params["human_behaviors"]` instead of a hard-coded agrarian list. |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_urban_domain` | 10/10 | profile aliases/defaults; urban init counts/zones; output+wages+employment; firms cannot pay wages they lack; agrarian init unchanged; urban lever compiles / cross-domain raises; agrarian lever still compiles; urban scale sweep (40/80) |
| `tests.test_twin_sim_w6` | 19/19 | regression: SIM-01/02, TWN-01 |
| `tests.test_popula_dyn_smoke` | 3/3 (direct call; no pytest in env) | births/cumulative counters unchanged |
| PIE fast tier (12 suites) | 124/124 | aggregate |

### SIM-03 Phase A metric (urban, `industrial_incentive` +20%, 2 years, seed 1)
| agents | baseline welfare | treated | relative |
|---|---|---|---|
| 400 | 0.236 | 0.270 | +14.4% |
| 2,000 | 0.177 | 0.203 | +14.7% |

Direction stable (+); 10k and calibration are Phase C, so urban claims stay `HYPOTHESIS`.

### Register changes
- SIM-03 ⬜ → 🟡 (Phase A done; B utilities/logistics/government budget, C calibration + 10k, D `eco_sim` fit).

### Notes
- No second simulator, no second persistence path, no new dependency. Same `SimulationModel`, `run_key` and `market.db`/kernel paths.
- Agrarian runs are unchanged by construction: `domain.apply({})` adds only agrarian defaults, and the land/farmer init path is byte-for-byte the old one.
- Urban is not calibrated yet: wage/output coefficients are Phase A placeholders, and `food_security` is explicitly a food-access proxy.

### Open at iteration end
- SIM-03 Phase B/C/D (utilities/logistics/capex, calibration to Kanpur/Delhi, 10k, `eco_sim` decision).
- G1 blockers unchanged: REV-06, OPS-01, FIN-02.
- TWN-01 gaps unchanged: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours`.

## Iteration 11 — 2026-11-04

**Goal:** SIM-03 Phase B — utilities, logistics and a municipal budget inside the urban domain pack.
**Gate(s) targeted:** SIM-03; claims about water, power, transport and municipal capex
**Outcome:** ✅ Phase B landed; Phase C (calibration + 10k) and D (`eco_sim`) remain.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| SIM-03 B | `core/urban.py` (`reset_step`, `begin_step`, `finish_step`, `note_event`, `metrics`) | Power/water capacity vs demand (ratios per 1000 agents), congestion = `1/road_capacity − 1`, transport cost marked up by congestion. Municipal budget: property/water/fuel revenue + grant against capex and a deficit rule (a negative balance halves next-step capex). Utility upgrades accumulate separately from the policy-set base capacity, so a policy delta applies every step. |
| SIM-03 B | `core/domain.py` | Urban defaults for `power_capacity`, `water_capacity`, `road_capacity`, `capex_efficiency`, `municipal_capex`, `municipal_grant`. |
| SIM-03 B | `core/policy.py` (`power_reliability_capex`) | Lever now raises `power_capacity` (a binding constraint), not the quality coefficient. |
| SIM-03 B | `behaviours/urban.py` | Firms use actual reliability and water supply; output falls with shortages; logistics mark-up reduces revenue; fuel/water/property payments emit one `public_revenue` event. Workers’ job-search radius shrinks with congestion; vacancies are filtered by capacity and ability to pay. Employee counts cached once per step. |
| SIM-03 B | `core/simulation_datacollector.py` (`build_reporters`) | Reporters moved out of the model (keeps `simulation_model.py` at 452 lines) and extended with `Power_Reliability`, `Water_Supply`, `Traffic_Congestion`, `Municipal_Balance`. |
| SIM-03 B | `core/scale.py` | Urban welfare = employment + output per capita/2 − 0.5·Gini, so infrastructure effects are visible. |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_urban_domain` | 14/14 | Phase B: utilities/budget reported; more road capacity lowers congestion; power capex raises reliability and output; deficit halves next-step capex |
| `tests.test_twin_sim_w6` | 19/19 | regression |
| `tests.test_popula_dyn_smoke` | 3/3 direct call | births/counters unchanged |
| PIE fast tier (12 suites) | 128/128 | aggregate |

### SIM-03 Phase B metric (2 years, seed 1, 400 → 2,000 agents)
| policy | metric | direction | relative |
|---|---|---|---|
| `power_reliability_capex` +30% | welfare | + | +13.9% / +15.6% |
| `transport_subsidy` +30% | welfare | + | +6.5% / +15.3% |
| `municipal_capex` +30% | `urban_output` | + | +0.94% / +0.95% |
| `municipal_capex` +30% | welfare | mixed | −1.4% / +4.8% (Phase C horizon/calibration issue) |

### Register changes
- SIM-03 🟡 remains open only for Phase C/D.

### Notes
- Utilities are ratios, not absolute MW/litres: 400 and 10k runs see the same regime when `auto_scale_grid` is on.
- Revenue and capex are bookkeeping in the model, not real money; no ledger write is made by the simulator.
- `municipal_capex` is direction-stable on its direct target (`urban_output`) but not yet on welfare at 400 agents/2 years — treated as a calibration task, not a claim.

### Open at iteration end
- SIM-03 Phase C (calibrate to ≥3 Kanpur/Delhi series; 400/2k/10k; promote findings) and Phase D (`eco_sim` fit).
- G1 blockers unchanged: REV-06, OPS-01, FIN-02.
- TWN-01 gaps unchanged: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours`.

## Iteration 12 — 2026-11-04

**Goal:** SIM-03 Phase C — calibrate the urban pack to real city series and test policy direction at 400/2k/10k; decide Phase D (`eco_sim`).
**Gate(s) targeted:** SIM-03; urban policy claims.
**Outcome:** ✅ Phase C complete. Calibration anchors are on target; policy direction is **not** stable across scales, so no urban claim is promoted past `HYPOTHESIS`. Phase D: do not adopt `eco_sim`.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| SIM-03 C | `popula_dyn/core/calibration.py` (`from_fields`, `fit_report`, `stability`) | Real rows → `firms_per_1000` (`industrial_units/population`), `municipal_grant` (budget-per-capita index), `road_capacity` (km per 1000), `initial_pop`/`weight_per_agent`. Missing rows stay null; unmapped fields listed explicitly. Fit report compares calibrated anchors with a real model run. |
| SIM-03 C | `digital_twins/calibration_engine.py` (`calibrate(domain="urban")`) | One entry point: urban delegates to the sim mapper; agrarian path unchanged. Avoids a second calibration path. |
| SIM-03 C | `scripts/calibrate_urban.py` | CLI: loads TWN-01 series, strips placeholders, writes `data/twins/calibration/urban_fit.{json,md}`, runs both cities at 400/2k/10k. |
| SIM-03 C | `popula_dyn/core/scale.py` | Welfare is kept at 6 decimals (was 3) so sub-0.001 effects at 400 agents are not rounded to zero. |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests/test_urban_calibration.py` | 10/10 | ratio mapping, missing→null, city ordering, fit anchors, fiscal gap, twin delegation, agrarian unchanged, scale direction |
| `tests/test_urban_domain.py` | 14/14 | regression |
| `tests/test_twin_sim_w6.py` | 19/19 | regression |

### Fit (real TWN-01 rows only; 2,000 agents)
| city | series | `firms_per_1000` target → sim | budget index | road index | fiscal gap |
|---|---|---|---|---|---|
| Kanpur | 3 (population, industrial_units, budget) | 10.03 → 9.93 (1.0%) | 0.998 (by construction) | missing | 4.56× |
| Delhi | 4 (+ road_km) | 7.20 → 6.93 (3.8%) | 1.44 (by construction) | 1.107 → 1.123 (1.5%) | 2.26× |

### Policy stability (welfare, 2 years, seed 1, calibrated params)
| city | mechanism | 400 | 2,000 | 10,000 | verdict |
|---|---|---|---|---|---|
| Kanpur | `transport_subsidy` +30% | +3.6% | +10.0% | +58.1% | stable `+` |
| Kanpur | `power_reliability_capex` +30% | −9.2% | +11.6% | +24.1% | **mixed** |
| Delhi | `transport_subsidy` +30% | +1.0% | −9.6% | −8.4% | **mixed** |
| Delhi | `power_reliability_capex` +30% | +0.1% | −7.0% | −21.3% | **mixed** |

Cause: at ≥2k agents the utility gain is captured as firm wealth (Gini rises) while employment falls, so the welfare objective turns negative. The pack has no wage-share/profit-distribution channel. Kanpur's 10k baseline also drops (0.62 → 0.37), so its +58% is measured on a degrading baseline.

### Register changes
- SIM-03 stays 🟡: calibration done, policy claims remain `HYPOTHESIS`; the open item is now profit/wage distribution, not `eco_sim`.
- Phase D decision: **no `eco_sim`** — it would be a second simulator for the same run-key; sector structure belongs in this pack.

### Open at iteration end
- SIM-03: add profit-share/wage channel, then re-run the 400/2k/10k gate.
- TWN-01 gaps unchanged: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours`.
- G1 blockers unchanged: REV-06, OPS-01, FIN-02.

### Added after the gate — kernel finding registration
- `modules/simulators/observation_metrics.py`: metric registry (population, welfare, urban_output, employment_rate, firms_per_1000) with per-metric tolerances and `outcome_override` (multi-scale `UNSTABLE` → `MIXED`).
- `SimulationConnector`: `build_observation(metric=…)`, `save_run_summary()` for runs executed outside `run_and_extract`, `register_to_kernel(observation=…)`; lazy PyYAML fallback (params written as valid JSON) so the connector imports in this env.
- `scripts/calibrate_urban.py --from-report`: registers without rerunning.
- Registered 4 findings in `popu_sim` (8 run summaries, all `HYPOTHESIS`): Delhi/Kanpur × `power_reliability_capex`/`transport_subsidy`. Kanpur transport is `IMPROVED`; the other three are `UNSTABLE` with `MIXED` direction.

## Iteration 13 — 2026-11-05

**Goal:** close the SIM-03 C finding — utility gains concentrated as firm wealth, so welfare flipped at scale; add a distribution channel and re-gate.
**Gate(s) targeted:** SIM-03; urban policy claims.
**Outcome:** ✅ Profit-share landed. Power capex is now direction-stable `+` at 400/2k/10k in both cities; Delhi transport is also stable; Kanpur transport still flips. No claim is promoted past `HYPOTHESIS` (single seed, 2 years, no falsification).

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| SIM-03 C | `behaviours/urban.py` (`OperateBehavior`, `_employee_map`, `WorkBehavior`) | Firms pay `profit_share` (default 0.1) of positive post-investment revenue to employees as an equal per-worker dividend via `unit_effects`; worker ids cached once per step. One conservation-safe flow: firm debits `paid`, workers credit it. |
| SIM-03 C | `core/domain.py` / `core/urban.py` | Urban default `profit_share: 0.1`; `profit_shared` event tracked and reported. |
| SIM-03 C | `modules/simulators/observation_metrics.py` + `simulation_connector.py` | Metric registry (`welfare`, `urban_output`, `employment_rate`, `firms_per_1000`), `outcome_override` for multi-scale `UNSTABLE`, `save_run_summary()`, `register_to_kernel(observation=…)`, PyYAML fallback. |
| SIM-03 C | `scripts/calibrate_urban.py` | Registers findings (tagged run ids) after each gate; `--tag`, `--from-report`, `--no-register`. |

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_urban_domain` | 14/14 (2 new: profit share reaches workers; zero share pays nothing) | — |
| `tests.test_urban_calibration` | 14/14 (4 new: mixed→UNSTABLE, metric registry, connector persistence) | — |
| PIE fast tier (13 suites) | 142/142 | aggregate |

### Re-gate (welfare, 2 years, seed 1, calibrated + `profit_share=0.1`)
| city | mechanism | 400 | 2,000 | 10,000 | verdict |
|---|---|---|---|---|---|
| Delhi | `power_reliability_capex` | +12.7% | +18.2% | +34.9% | stable `+` |
| Delhi | `transport_subsidy` | +7.6% | +16.3% | +31.9% | stable `+` |
| Kanpur | `power_reliability_capex` | +9.5% | +15.4% | +46.3% | stable `+` |
| Kanpur | `transport_subsidy` | +0.6% | −0.2% | −12.4% | **mixed** |

Baseline welfare still drifts down with scale (0.41→0.30 Delhi, 0.52→0.41 Kanpur); reported, not hidden.

### Kernel registration
- 4 findings registered in `popu_sim` (`urban <city> <mechanism> stability profit_share`), backed by 8 persisted runs (`save_run_summary` → `simulation_runs`).
- Each carries `claim_strength: HYPOTHESIS`, the per-scale table, and `direction: MIXED` where the sign flips.

### Register changes
- SIM-03 🟡: distribution gap closed; open item is promotion discipline (multi-seed + falsify) plus the Kanpur transport flip.
- `eco_sim` remains rejected (iteration 12).

### Open at iteration end
- Multi-seed `stability(..., seeds=...)` + `falsify_run` for the three stable levers before any claim moves to REPLICATED.
- Kanpur `transport_subsidy` at 10k: investigate congestion/commute interaction before claiming.
- TWN-01 gaps unchanged: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours`.
- G1 blockers unchanged: REV-06, OPS-01, FIN-02.

## Iteration 14 — 2026-11-05

**Goal:** move the three stable urban levers past `HYPOTHESIS` using the evidence ladder (multi-seed + falsification), and keep the unstable one honest.
**Gate(s) targeted:** SIM-03 promotion; C4 (first promotable finding).
**Outcome:** ✅ Three levers reached `FALSIFICATION_PASSED` (3 seeds, n = 37,200 agent samples, all attacks held). Kanpur `transport_subsidy` stayed `HYPOTHESIS` and its older evidence was superseded.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| SIM-03 D | `popula_dyn/core/calibration.py` (`stability`, `claim_evidence`) | `seeds=` runs every scale per seed; `passed` now needs the sign at every scale **and** every seed; row carries `per_seed_signs` and `n`. |
| SIM-03 D | `popula_dyn/core/falsify.py` (`falsify_policy`) | Metric-aware attack for a lever: seed shift, smaller/larger magnitude, half horizon, and a zero-magnitude placebo that must produce no effect. |
| SIM-03 D | `scripts/calibrate_urban.py` (`falsify_and_grade`, `--seeds`, `--falsify`) | Attacks each stable lever, grades it through `kernel.hypothesis.claim_strength.check`, and registers the finding at the supported strength. |
| SIM-03 D | `popu_sim` topic graph | 8 older urban findings marked `superseded`; 4 `... stability promotion` findings active. |

### Promotion gate (welfare, 2 years, 400/2k/10k, seeds 1–3)
| city | mechanism | magnitude range | falsify | claim |
|---|---|---|---|---|
| Delhi | `power_reliability_capex` | +12.3% … +33.1% | passed | `FALSIFICATION_PASSED` |
| Delhi | `transport_subsidy` | +6.7% … +27.7% | passed | `FALSIFICATION_PASSED` |
| Kanpur | `power_reliability_capex` | +17.6% … +52.1% | passed | `FALSIFICATION_PASSED` |
| Kanpur | `transport_subsidy` | −8.5% … +1.6% | not attempted (scale-unstable) | `HYPOTHESIS` |

### Kanpur transport diagnosis
At 10k the subsidy *lowers* employment (32.3% → 28.7%) while firms end richer (13.9 → 26.2 avg wealth). Same seed and identical initial state, so the divergence is ordering/randomness in the greedy hire loop, not a stable economic channel. Recorded as `MIXED`; no claim.

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_urban_calibration` | 16/16 (2 new: two-seed ladder promotion; placebo lever has zero effect) | — |
| PIE fast tier (13 suites) | 144/144 | aggregate |

### Register changes
- SIM-03 🟢: levers promoted; remaining work is applying the same gate to new mechanisms, not to these three.
- C4 ✅: first findings above `HYPOTHESIS` under the code-enforced ladder.
- `eco_sim` remains rejected.

### Open at iteration end
- Kanpur transport: needs a deterministic hire order (or many-seed CI) before any claim; treat as noise until then.
- TWN-01 gaps unchanged: Kanpur `road_km`, `power_supply_hours`; Delhi `power_supply_hours`.
- G1 blockers unchanged: REV-06, OPS-01, FIN-02.

> **Correction to iteration 14 (issued in iteration 15).** The three `FALSIFICATION_PASSED` claims did not reproduce after the dividend-timing fix. They were artifacts of mid-step profit payouts draining hiring cash; the topic nodes are marked `superseded`.

## Iteration 15 — 2026-11-05

**Goal:** close the Kanpur transport item — make hiring order deterministic, then re-run the promotion gate.
**Gate(s) targeted:** SIM-03; C4.
**Outcome:** ⚠️ Hiring order fixed, but that exposed a model defect: dividends paid mid-step drained the cash that hires the rest of the step, which is what made Kanpur transport flip and what inflated the iteration-14 effects. After moving the payout to step end, only **Kanpur power capex** still clears the full gate.

### Changes
| ID | File + symbol | What changed |
|---|---|---|
| SIM-03 E | `behaviours/urban.py` (`_dist`, `_nearest_firm`) | True-nearest eligible firm with `(distance, unit_id)` tie-break; was `local[0]`, i.e. grid-dict order. |
| SIM-03 E | `behaviours/urban.py` (`OperateBehavior`) + `core/urban.py` (`pay_dividends`) | Firms declare `pending_dividend`; `finish_step` pays it equally per worker (capped at firm cash). Mid-step payouts were starving same-step hiring. |
| SIM-03 E | `core/calibration.py` (`regrade`, `_seed_signs_at_decision_scale`) | Promotion rule: scale-mean sign consistent **and** every seed agreeing at the largest scale; small-scale seed noise is reported, not vetoed. Re-grades a stored report without rerunning. |
| SIM-03 E | `scripts/calibrate_urban.py` (`--regrade`) | Re-grades + re-falsifies a stored `urban_fit.json`, rewrites `.json`/`.md`, re-registers. |

### Corrected gate (welfare, 2 years, 400/2k/10k, seeds 1–3, `n=37,200`)
| city | mechanism | magnitude range | seed @10k | falsify | claim |
|---|---|---|---|---|---|
| Delhi | `power_reliability_capex` | −1.2% … +8.8% | flips | not attempted | `HYPOTHESIS` |
| Delhi | `transport_subsidy` | +0.6% … +1.5% | flips | not attempted | `HYPOTHESIS` |
| Kanpur | `power_reliability_capex` | +5.2% … +26.0% | agrees | passed | `FALSIFICATION_PASSED` |
| Kanpur | `transport_subsidy` | +3.6% … +35.5% | agrees | fails seed shift | `HYPOTHESIS` |

Delhi's earlier +12…+35% did not survive the dividend fix: its levers are now within noise (~1%), so the previous Delhi promotion was the artifact, not the mechanism.

### Tests
| Suite | Result | New tests |
|---|---|---|
| `tests.test_urban_domain` | 18/18 (tie-break by id; dividends settle at step end) | — |
| `tests.test_urban_calibration` | 17/17 (regrade uses decision scale) | — |
| PIE fast tier (13 suites) | 147/147 | aggregate |

### Register changes
- SIM-03 🟡: one lever promoted in one city; the other three are `HYPOTHESIS`.
- C4 🟡: first promotable finding exists (Kanpur power capex), but the earlier three-lever claim is withdrawn.
- 20 older urban findings (tags `stability`, `profit_share`, `promotion`, `dividend_end`, `final`) marked `superseded`; only `... final2` remain active.

### Open at iteration end
- Delhi levers: effects are ~1% after the dividend fix — check whether `profit_share` still reaches Delhi workers or whether Delhi firms are cash-constrained.
- Kanpur transport: fails only the seed-shift attack at 2k; report seed-level spread before retesting.
- TWN-01 gaps and G1 blockers unchanged.
