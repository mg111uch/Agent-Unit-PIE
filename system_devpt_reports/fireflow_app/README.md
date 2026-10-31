# FireFlow App (Level 1) — the economic operating system, as PIE sees it

> Repo: `$FIREFLOW_ROOT` (directory currently named `reddit-clone`). Origin: a social/community app; now the **economic execution + sensor layer** feeding the PIE brain.
> Agent rule: shipped features → §3 tables; unimplemented → `02_roadmap_master.md` + `roadmap.md` (same dir); **no phase/stage labels** in feature tables.
> Kernel tag for FireFlow findings: `fireflow_app`. Master doc: `00_README_master.md` (Level 0).

## 1. Role & architecture

```
RESEARCH ──┐
           ├──► ECONOMIC TWIN (kernel) ──► opportunity ──► SIMULATE/EXECUTE ──► MEASURE ──► LEARN/SCALE
FIREFLOW ──┘
```
FireFlow owns: identity, markets, contracts, payments, workforce, compute, data, evidence. PIE owns cognition. **PIE says what should happen; FireFlow determines whether and how.** FireFlow must never grow a second brain.

**Objective** (shared): maximize sustainable real-world productive capability subject to cash/risk/capital/skills/technology/regulation/time/energy/demand/reliability. **Bootstrap operating mode:** FireFlow is *infrastructure behind an AI-operated B2B intelligence service*, not yet a public marketplace.

**Loop:** observe → twin → simulate → execute → measure → learn → scale or pivot.

**Code layout (`fireflow/` + `economy/`):** `units/` (identity + profiles) · `opportunities/` (scored demand) · `contracts/` (agreements + escrow states) · `tasks/` (paid work) · `reputation/` (verification + ratings) · `payments/` (cash books + approval gates) · `markets/` (task / data / compute / B2B surfaces) · `agent_accounts/` (business_agent + worker-agent credentials bound to AI Agent units).

## 2. Stack, run & test

| Item | Detail |
|---|---|
| Prerequisites | Next.js 15.3.3 (pinned — OPS-05), Node.js (v18+), npm, SQLite (included) |
| Frontend | Next.js 15.3.3, React, TypeScript; Jest, Playwright (E2E), Cypress |
| Backend | Node.js (v18+) API, SQLite (included), jest; `backend/pie/` = PIE gateway |
| Run both | `npm run app` (backend + frontend). **Port docs conflict:** backend 3001 vs 5000 (DOC-01); frontend 3000 |
| Backend only / frontend only | `cd backend && npm start` (API at `http://localhost:5000`) · `cd frontend && npm run dev` (app at `http://localhost:3000`) |
| Tests | backend `npm test [-- file] [-t name]` (e.g. `npm test -- forms.test.js -t "should submit form successfully"`); frontend `npm test`, `npm run test:watch` (e.g. `npm test -- payment-modal.test.tsx`); E2E `npx playwright install chromium` first, then `npm run test:e2e`, `npm run test:e2e:ui`, or `npm run test:e2e -- payment-flow.spec.ts` (app must be running); Cypress `npm run test:cypress:open` |
| Integration suites (counts at last gate) | drift+contract 8 · gateway 12 · ledger 18 · settlement 23 · sensors 26 (cumulative-looking numbers [INFERRED]) |
| Local secrets | `backend/.pie_operator` (shared operator password, chmod 600), `backend/.sender_identity` (outreach signature) — never in docs |
| Frontend surface | social shell, forms, generative UI, services ✅; **economic modules (CRM, outreach, ledger approvals, funnel) have no documented UI** — operated by API/curl [INFERRED] (STR-05) |

## 3. Feature inventory (shipped)

### 3.1 Social / product shell (frozen — STR-01)
| Capability | Description |
|---|---|
| Auth | Login, register, forgot/reset password |
| Main feed | General + community posts: like, dislike, save, share, comment, views, options; create-post, filter, stats (total + online users) |
| Create posts | 280-word general, community, form posts (General/Service), voting post — tabs |
| Chats | chat list, user chat |
| Communities | list/page; create, edit, delete |
| Generative-UI | custom forms with LLM-generated components; 16 px editable grid for placement/property editing |
| Markets | post detail with live voting trends and bets (prediction-market type) |
| Profile | header card (name, email, pic, followers/following, total posts); user communities, posts, forms; followers/following lists |
| Notifications / Options / Search / Posts | in-app notifications; settings, saved posts, about, logout; post showcase + user search; comment threads |
| Payments (forms) | service forms carry a cost to make |
| Services | services with subservices, post lists/creation forms; premium feature |
| Global context / Shared lib / UI components | Auth/Notification/Post/Socket providers; config, icons, service-data, types, utils; BottomAppBar, FormCard, MarketCard, PostCard, TopAppBar |

### 3.2 Economic substrate
| Capability | Description |
|---|---|
| Economic identity | one identity per productive entity as Units: Person, Business, Organization, AI Agent, Service, Product, Vehicle, Machine, Facility, Compute Node, Dataset; credential-gated minting |
| Task marketplace | posters publish objective + budget + deadline + verification rule; workers (human/agent) claim, execute, get paid on verification; disputes resolve against the contract record, not chat logs |
| Task record fields (`agent_tasks`) | every task carries objective / budget / deadline / inputs / required capabilities / verification rule / reward / risk flag |
| Supply offers | spare capacity (vehicle, space, skills, compute) listed as offers; buyers book, complete, pay suppliers (buyer→supplier) |
| Micro-work splitting | projects → micro-tasks with progress; parents complete only when children are done |
| Referrals | workers mint invite codes; one redemption per invitee; growth signal per inviter |
| Engagement records | work classified at publish (gig/contract/trial) with terms reference; portable per-worker history (earnings, ratings) |
| Opportunity scoring | scored demand (demand × fit × margin × speed × cost × scalability × adjacency) with debate hook; **single-source scorer in PIE, FireFlow is a thin proxy** |
| Contract escrow | funds lock on acceptance, release on verified completion; milestone splits; kill-fee; dispute records |
| Reputation | ratings per completed task/contract; portable aggregates; capability attestations; **verification gate before first payout** |
| Verified gig payouts | gig drivers must own a verified unit before payout (closes task-only verification gap) |

**Interface target (adopted):** a shared Economic Object Model + Opportunity/Task/Transaction API — one language so FireFlow and PIE interoperate from day one.

### 3.3 Money
| Capability | Description |
|---|---|
| Single ledger | every rupee movement as income/expense/staged/approved rows in **one book — no parallel books**; agents propose, humans approve |
| Authoritative ledger | double-entry accounts; idempotency keys (webhooks pay once); pending→settled state machine; releases reference paid tasks instead of re-booking |
| Settlement pipeline | contract authorize→provider→settle→reconcile→payout→report, idempotent at every step; provider failures settle nothing |
| Revenue rails | marketplace rake recorded per payout (runtime-changeable); platform revenue view |
| Fee policy rails | runtime-changeable task/gig/contract rake, data/compute fees, welfare head; splits computed at settle time, no redeploy |
| Data & compute settlement | dataset grants book flat access fee with license issue; compute completions book node-rate fee; double grants/jobs pay once |
[LOOPHOLE FIN-01 · S1] Provider/payout rail and a global kill switch are undocumented. [/LOOPHOLE]
[LOOPHOLE FIN-02 · S1] Escrow-holding may be regulated; start customers on a no-escrow invoice path. [/LOOPHOLE]
[SUGGESTION INT-06 · P1] Stamp `fee_policy_version` on every economic event so findings expire when rake changes. [/SUGGESTION]

### 3.4 Businesses & intelligence
| Capability | Description |
|---|---|
| Business profiles (`industrial_b2b`) | capability profile; structured capacity (headcount, shifts, offerings with quantity & lead time); order book; compliance docs; quantity & lead-time filters |
| Capability search | supplier search by capability + region, most capable first (e.g., "who within 300 km can CNC aluminium ±0.05 mm?") |
| Commerce pipeline | opportunity→cash: score, challenge, stage, human approve, execute via task, reconcile estimate vs actuals; **same pipeline for a ₹500 task and a ₹50 lakh order — only the gates scale** |
| Enterprise twin | live business model: derived task/cashflow/workforce/reputation/pipeline measures + owner-reported metric feeds (truth tiers apply) |
| Business agent | per-business duties (inventory watch, supplier discovery, market intel, quotation, analysis); event-driven runs with history |
| Agent accounts | API keys bound to AI Agent units; supervised spend caps enforced on proposals |
| Loop decisions | every loop closes scaled / abandoned / pivoted + reason; kill reasons surfaced in twins |
| Market signals | weekly industry inputs (trends, demand, policy, tech costs) with staleness flags; feed market intel; **`future_industry_engine`** refreshes these weekly into the opportunity engine |
| Capability ladder | rung-by-rung path from a business's capabilities to a target industry with local supplier counts per rung |
| Industry scanner | market signals auto-drafted into scored opportunities; drafts accepted with edited economics |
| Ventures | research commercialization in gated rungs (lab, pilot, product, graduated, killed); evidence per gate; kill reasons |
| Export orders | quote → compliance-gated confirm → ship → deliver; forex estimates; policy incentive on delivery |

### 3.5 Data, compute, sensors
| Capability | Description |
|---|---|
| Data marketplace | consent-first datasets bound to Dataset units; purpose-bound access requests with logged grant/deny/revoke; provenance lineage (DPDP compliance first-class, not a banner) |
| Dataset licenses | first-class grant records with terms, purpose, revocation; revoked licenses block future grants server-side |
| Compute exchange | benchmarked nodes bound to Compute Node units serving **published workloads only** (render, inference, simulation, annotation QA); code blobs rejected; queued→done lifecycle; no arbitrary customer code on hosts |
| Sensor network | structured human observations feeding business twins; reporter-only escalation into measured tasks; humans are the highest-resolution sensors (observe → twin → simulate → execute → measure → learn) |
| Trusted observations | source, device, geography, evidence, confidence on every observation; independent confirmations (self/double-confirm rejected); per-capability reporter reliability |
[SUGGESTION SEN-01 · P1] Count a confirmation as independent only if devices/geo buckets differ and the two accounts share no referral chain. [/SUGGESTION]
[SUGGESTION STR-06 · P2] Compute node attestation/heartbeat/isolation/result-verification/failure-handling status is undocumented; keep the exchange internal until demand exists. [/SUGGESTION]

### 3.6 PIE gateway
| Capability | Description |
|---|---|
| Agent proposal gateway | strict envelopes (objective, action, budget, risk, capabilities, expected outcome, authorization); server-side authorize / deny / needs-approval; RBAC |
| Execution receipts | idempotent execution evidence ingested as observations; invalid envelopes rejected; over-cap proposals denied |
| Drift + contract tests | schema drift guards (adapter built from the kernel artifact, no shadowed keys); escrow lifecycle, rake math, verification-gate jest suites; single-source rule = kernel owns `codebase/kernel/schemas/`, FireFlow vendors the artifact + drift-tests |

### 3.7 Revenue acquisition (customer pipeline)
| Capability | Description |
|---|---|
| Prospect CRM | evidence-backed prospects (company, problem, triggers, value, contactability, confidence); dedup on company+problem; opt-out blocks outreach/pilot |
| Prospect bulk import | `POST /api/prospects/import` — PIE discovery batches, within-batch dedup, per-row errors, created/deduplicated counts |
| Proposals | offer bridge: prospect + template + price → proposal; **accept** spins up the executing task + draft contract and marks prospect *pilot* |
| Outreach pipeline | draft → human approve → capped send (1 per 7 days) → classified response; unsubscribe auto-opts-out |
| Proposal launch | accepted proposals split into budgeted microtask children under the delivery task; payouts bounded by the pilot price |
| Revenue funnel | `GET /api/metrics/funnel`: stage counts, responses by class, released wins, revenue/cost/margin in paise |

### 3.8 Job search (specialized economic agent)
| Capability | Description |
|---|---|
| Job ingestion store | `POST /api/jobs/import` bulk-push normalized roles (dedup by `job_id`); `GET /api/jobs` |
| Job fit scoring | `POST /api/jobs/:id/score` fits role vs candidate twin via PIE; caches score + APPLY/TAILOR/OUTREACH/SKIP |
| Application tracker | packs per job; status follows hiring pipeline; **illegal jumps rejected server-side** |
| Job outreach | network-first notes: draft → approve → capped send (5/day) → classified response |
| Jobs funnel | `GET /api/metrics/jobs`: verdict mix, application pipeline, outreach counts, responses by class |

## 4. State machines (the invariants a direction session should rely on)

| Object | States / rule |
|---|---|
| Task | published → claimed → executing → verified → paid; cannot be verified and cancelled together; a worker can't claim twice [VERIFY FIN-08: DB-level?] |
| Contract/escrow | accepted (lock) → milestones → verified (release) / cancelled (kill-fee) / disputed |
| Ledger entry | pending → settled (+ failed/refunded/disputed/reversed planned [VERIFY]); idempotency key per external event |
| Settlement | authorize → provider → settle → reconcile → payout → report |
| Outreach | draft → approved → sent → response classified (interested / later / wrong person / not relevant / unsubscribe); 1 per 7 days per prospect |
| Job outreach | draft → approved → sent (≤5/day) → classified |
| Proposal | drafted → accepted → launched (microtasks) ; accept marks prospect `pilot` |
| Application | discovered → qualified → ready → applied → outreach → screen → interview → technical → offer → accepted; rejected/withdrawn/expired [INFERRED from plan] |
| Export order | quote → confirmed (compliance-gated) → shipped → delivered |
| Compute job | queued → … → done |
| Dataset access | request → grant/deny → revoke; license carries purpose + terms |
| Venture | lab → pilot → product → graduated / killed (evidence per gate) |
| Loop | → scaled / abandoned / pivoted (+ reason) |

## 5. Human gates & authorization

| Gate | Who | Where |
|---|---|---|
| Real-money movement | human approves staged ledger rows | ledger |
| Agent proposal over cap / risky | human (needs-approval) | gateway |
| Outreach send | human approves each draft | `/api/outreach` approve→send |
| Proposal price/confidence gate | human | proposals |
| Job outreach send | human approves every send | jobs |
| Application submit | policy gate (what passes is ❓ JOB-03) | tracker |

## 6. Design intent by domain (retained from the old README; no stage labels)

- **Economic loop stages:** observe → discover → estimate → simulate → rank → task → execute → collect → reconcile → twin → learn → scale / abandon / pivot. Every rupee tracked; every loop either scales or gets killed with a reason.
- **Opportunity engine:** cheap gate first (capital-heavy ideas rejected before deep scoring); debate hook — challenger argues against, scorer defends, only survivors run.
- **Reputation:** identity verification before first payout; ratings portable across marketplaces; attestations (tests, trial tasks) unlock higher-value work.
- **Workers & compliance:** classification, records and social protection built in from day one (Social Security Code in force per planning chat; DPDP Rules notified Nov 2025, phased) — design inputs, not afterthoughts [verify].
- **Spare-capacity monetization:** idle vehicle hours → logistics/delivery slots; rooftop/spare room → storage/solar/micro-warehousing; skills after hours → review/tutoring/annotation/audit; idle devices → benchmarked compute.
- **Micro-work flywheel:** AI demand → micro-tasks → workers earn → invite others → supply grows → bigger projects.
- **Business agent duties:** sales outreach, procurement, inventory watch, customer support, market intel, quotation, supplier discovery, hiring screens, analysis — should run as *event → duty → PIE reasoning → proposal → authorization → action → result → event*.
- **Enterprise twin feeds:** orders, inventory, costs, capacity, machines, workers, suppliers, customers, energy, cashflow, defects, delivery times; twin → simulate → execute → measure back into twin.
- **Interoperate, don't rebuild:** plug into open commerce networks for discovery/settlement; build only twin, scoring, execution.
- **Ride-hailing:** later, only as a logistics capability — never a standalone consumer bet.
- **Revenue priority (in order):** B2B services (agent-built, agent-delivered) → task-marketplace rake → data fees → compute margin → enterprise-twin SaaS → procurement/supply-chain services → export facilitation → industrial intel reports → skilling-to-earning → consumer ads (last, never the engine).
- **Geography:** Kanpur = operations base; India = the market; win at home first.
- **Industrial leap (locked ladder, `industrial_pathfinder`):** industrial graph (who makes what, where, at what capacity/cost), technology graph (which capabilities unlock which industries), `future_industry_engine` scanner, pathfinder (services→components→systems→industries, each rung funds the next), research commercialization (lab→pilot→product), India-wide supplier graph, export engine (domestic capability → global orders).

## 7. Known gaps (see register)

[LOOPHOLE INT-04 · S2] PIE `market.db` and FireFlow both hold prospect/ledger-like data — declare FireFlow system-of-record. [/LOOPHOLE]
[SUGGESTION REV-07 · P1] Add a magic-link customer portal (view → accept → pay/invoice → download deliverable) and a `deliverable_assembly` step. [/SUGGESTION]
[SUGGESTION FIN-04 · P1] Treat SQLite durability (WAL, backups, restore drill, Postgres path) as a precondition for `MONEY_MODE=live`. [/SUGGESTION]
[VERIFY FIN-01] Which payment/payout providers are wired and in what mode? [/VERIFY]
[VERIFY REV-07] How does an external customer accept a proposal and receive a deliverable today? [/VERIFY]

**Carried from `roadmap.md` (same dir) — still open unless marked shipped.** `roadmap.md` remains the single plan of record for FireFlow; this table is the direction-session summary. Unbuilt detail (e.g. the current job-agent slice, funnel snapshot) stays there.

| Item | Status | Note |
|---|---|---|
| Welfare contribution rails (bps on payouts into a welfare head) | ⬜ | needs a policy rate (FIN-06) |
| Scale the reads: `GET /businesses` + search load the whole table | ⬜ | pagination + region indexing before national-scale data (supplier graph at scale is otherwise indexing + seed tooling) |
| Timestamps + admin | ⬜ | most tables lack `updated_at` (delivery-time metrics impossible); admin hardcoded to user id 1 — replace with a role |
| Sandbox honesty | ⬜ | node benchmarks are self-reported; job execution is lifecycle-only — integrate a real runner or label mock surfaces (STR-06) |
| Frontend for economic surfaces | ⬜ | tasks, escrow, ledger, twins, pipelines are API-only (STR-05) |
| Secrets + observability | ⬜ | JWT falls back to a default secret; no request logging or error tracking in production paths (OPS-03) |
| Contract/drift tests · data+compute settlement · ledger double-counting · gig verification gap | ✅ | shipped 2026-09-15/17 (see `roadmap.md` shipped log); older roadmap wording is stale |
| **Stage F — Moon (deferred)** | ⛔ | cislunar economy, lunar twin + Earth–Moon supply chain, ISRU (water/oxygen/regolith), autonomous factories (terrestrial rehearsal first) — no Moon work before industrial autonomy |
