# FireFlow Roadmap

## Now

- Current slice: personal job agent COMPLETE JF-1..JF-6 (funnel live: 8 scored, 1 READY, 2 drafts); next: better feeds.
- Single-source rule: kernel owns the unit schema (`codebase/kernel/schemas/`); FireFlow vendors the artifact + drift-tests (no second source).
- Maintained per session: exactly one active slice lives here; shipped slices
  move into the stages below as done.

---

## Future Work (session review 2026-09-09 — ordered by leverage)

- Contract tests + backend coverage. Drift-tests for PIE proxies (scoring,
  industrial), gate tests (verification, escrow, rake math), mount checks.
  All economic surfaces shipped without jest tests; e2e was ad-hoc.
- Settlement for data/compute. Access grants and completed jobs move no
  money — wire both into the ledger once fee policy is set (rake pattern).
- Welfare contribution rails (deferred). Bps on payouts into a welfare head;
  needs a policy rate.
- Ledger double-counting. Task pay + contract release record the same rupees
  twice; release against an already-paid task should reference, not re-book.
- Verification gap on gigs. The A5 payout gate covers tasks/contracts only;
  gig workers still get paid unverified.
- Scale the reads. `GET /businesses` and search load the whole table;
  pagination + region indexing before national-scale data arrives.
- Timestamps + admin. Most tables lack `updated_at` (delivery-time metrics
  impossible); admin is hardcoded user id 1 — replace with a role.
-sandbox honesty. Node benchmarks are self-reported; job execution is
  lifecycle-only. Either integrate a real runner or label mock surfaces.
- Frontend for economic surfaces. Everything shipped is API-only; no UI
  exists for tasks, escrow, ledger, twins, or pipelines.
- Secrets + observability. JWT falls back to a default secret; no request
  logging or error tracking in production paths.

---

## Stage F — Moon (deferred)

Out of scope until Stage E funds it:

- Cislunar economy modeling
- Lunar twin + Earth–Moon supply chain
- ISRU (in-situ resource utilization): water, oxygen, regolith
- Autonomous factories (terrestrial rehearsal first)

No Moon work before industrial autonomy. The ladder is the strategy.

---

## Remaining

Roadmap now holds only uncompleted work. What's actually left, ranked by value:

1. **Contract tests + backend coverage (unbuilt quality gate).** The single-source rule demands drift-tests — they were never written. Our ~15 new economic surfaces have zero jest tests; every e2e ran ad-hoc. Highest leverage: parity tests (PIE scorer vs proxy outputs), gate tests (verification, escrow, rake math), and mount checks in CI. Unsexy, load-bearing.
2. **Data/compute settlement.** Datasets grant access and compute jobs complete, but no money moves — wire both into the ledger (access fee on grant, job cost on complete using node rates). Needs your fee policy like rake did.
3. **Welfare contribution rails** (deferred B4.3). Same shape: a bps on payouts into a welfare head. Needs your rate.
4. **Supplier graph at scale** (the listed slice). Honest assessment: without real business data this is indexing + pagination + seed tooling — real but low urgency.
5. **Stage F.** Deferred by your own rule until E funds it. No.

My recommendation: **1, then 2.** Tests lock in everything shipped; settlement completes C4's money loop. Want me to start with the contract-test suite, or set fee policies for settlement first?

## Footer / Scope

- This roadmap is the single plan of record for FireFlow; stage sections grow
  one-liner "done" markers as slices ship.
- Agent rule: when a slice ships, move it to `README.md` `## Features Overview`
  by capability name — NEVER with a stage/phase tag (`Stage A3`, `Phase X`).
  Unimplemented work lives here; shipped capabilities live in the README table.
- Scope boundary: `ToDo.md` is a personal file — out of scope, never read or
  edited by workers.

## Shipped (session log, append-only)

- 2026-09-15: contract + drift jest suites (`backend/lib/*.test.js`) — escrow lifecycle, rake math, verification gate, schema drift.
- 2026-09-15: agent proposal gateway (`backend/pie/` propose/receipt envelopes + server-side RBAC) with jest suite; in-repo parity builders in PIE `economy/pie_protocol.py`.
- 2026-09-15: authoritative ledger (double-entry fields, idempotency, state machine, pay-vs-release reference fix, fee-policy splits, gig verification gate) with jest suite.
- 2026-09-15: settlement engine + dataset licenses (pipeline with reconcile/report, data/compute fee booking, license grant gate) with jest suite.
- 2026-09-15: trusted observations (anti-fraud fields, confirm flow, per-capability reliability) with jest suite.
- 2026-09-17: prospect CRM (`prospects` table + `/api/prospects` with dedup, opt-out, status gates) with jest suite (3/3).
- 2026-09-17: prospect bulk import (`POST /api/prospects/import` via pure `lib/prospects.js`) with jest suite (2/2).
- 2026-09-17: proposals (`proposals` table + `/api/proposals` with accept→task+contract bridge) with jest suite (2/2).
- 2026-09-17: outreach (`outreach` table + `/api/outreach` draft→approve→capped send→classified respond) with jest suite (7/7).
- 2026-09-17: proposal launch (`POST /api/proposals/:id/launch` splits delivery into microtask children) with jest suite (2/2).
- 2026-09-17: revenue funnel (`GET /api/metrics/funnel` via `lib/metrics.js`) with jest suite (1/1).
- 2026-09-17: candidates table (JF-1 twin storage; revenue loop parked awaiting replies — see `REPLY_HANDOFF.md`).
- 2026-09-17: jobs ingestion store (`jobs` table + `/api/jobs/import`) with jest suite (3/3).
- 2026-09-17: job fit scoring (`POST /api/jobs/:id/score` via `fit_cli.py`, caches verdict).
- 2026-09-17: application tracker (`applications` table + `/api/applications` with enforced state machine) with jest suite (3/3).
- 2026-09-17: job outreach (`job_outreach` table + `/api/job-outreach` draft→approve→capped send→classified) with jest suite (2/2).
- 2026-09-17: jobs funnel (`GET /api/metrics/jobs` via `lib/metrics.js`) with jest suite (1/1).
- 2026-09-17: boot heals legacy partial DBs (missing tables created before migrations; fixes `no such table` on old `reddit_clone.db`).
