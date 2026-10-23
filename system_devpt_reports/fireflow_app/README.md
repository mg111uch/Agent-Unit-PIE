# FireFlow App - Development Guide

> FireFlow = the economic operating system: real-world sensor + marketplace +
> transaction + workforce + compute + data layer feeding the PIE brain.
> PIE thinks; FireFlow earns, executes, and closes the loop in the real world.

## Architecture

```
RESEARCH ──┐
           ├──► ECONOMIC TWIN ──► opportunity ──► SIMULATE / EXECUTE ──► MEASURE ──► LEARN / SCALE
FIRE FLOW ─┘        (KERNEL)
```

- RESEARCH/KERNEL: cognition, simulation, policy scoring (PIE side).
- FIRE FLOW: identity, markets, contracts, payments, workforce, compute, data.
- ECONOMIC TWIN: live model of every actor — people, businesses, machines.
- Loop: observe → twin → simulate → execute → measure → learn → scale or pivot.

## Guiding Objective

MAXIMIZE SUSTAINABLE REAL-WORLD PRODUCTIVE CAPABILITY subject to:

cash / risk / capital / skills / technology / regulation / time / energy /
demand / reliability.

Kernel tag for future FireFlow findings: `fireflow_app`.

## Prerequisites

- Next.js 15.3.3
- Node.js (v18+) and npm 
- SQLite database (included)

## Running the Application

### Option 1: Run Both (Recommended)

```bash
cd project-dir
npm run app
```

This starts both backend (port 3001) and frontend (port 3000).

### Option 2: Run Separately

#### Backend Only

```bash
cd project-dir/backend
npm start
```

- API runs at: http://localhost:5000

#### Frontend Only

```bash
cd project-dir/frontend
npm run dev
```

- App runs at: http://localhost:3000

---

## Testing

### Backend Tests (Jest)

```bash
# Run all backend tests
cd project-dir/backend
npm test

# Run specific test file
npm test -- forms.test.js

# Run specific test
npm test -- forms.test.js -t "should submit form successfully"
```

### Frontend Tests

#### Unit Tests (Jest)

```bash
cd project-dir/frontend
npm test

# Watch mode
npm run test:watch

# Run specific test file
npm test -- payment-modal.test.tsx
```

#### E2E Tests (Playwright)

```bash
cd project-dir/frontend

# Install browsers (first time only)
npx playwright install chromium

# Run E2E tests
npm run test:e2e

# To run only this specific test file
npm run test:e2e -- payment-flow.spec.ts

# Run E2E tests with UI
npm run test:e2e:ui

# Note: E2E tests require the app to be running.

# Cypress E2E test in watch mode
npm run test:cypress:open
```

---

## Features Overview

> Agent rule: shipped features → this table; unimplemented work → `roadmap.md`.
> NEVER use phase/stage labels (`Phase X`, `Stage A`, or any build-step tag) in
> this table — list features by what they ARE (e.g. `Task marketplace`, not
> `Stage A3`). Stage labels belong to session history only, never to feature docs.

| Capability | Description |
|------------|-------------|
| **Auth** | Login, Register, forgot-password, reset-password. |
| **Main feed** | General and community posts with like, dislike, save, share, comment, views, options per post; create-post button, post filter, stats (total + online users). 
| **Create posts** | General 280-word post, community post, form post (General and Service type), voting post arranged in tabs. 
| **Chats** | Chats list, user chat. 
| **Communities** | Community list and page with community posts; create, edit, delete community. 
| **Generative-UI** | Custom forms with LLM generated components; 16px editable grid for placement and property editing. 
| **Markets** | Post detail page with live voting trends and bets (prediction-market type). 
| **Notifications** | All in-app notifications. 
| **Options** | Account settings, saved posts, About app, logout. 
| **Payments** | Service forms have a cost to make. 
| **Posts** | Post with comment threads. 
| **Profile** | Header card (name, email, pic, followers/following, total posts); user communities, posts, forms; followers/following lists. 
| **Search** | Showcase of posts and a search bar to find users. 
| **Services** | Services with subservices; subservice post lists and creation forms; premium feature. 
| **Global context** | Auth, Notification, Post, Socket providers. 
| **Shared lib** | Config, icons, service-data, types, utils. 
| **UI components** | BottomAppBar, FormCard, MarketCard, PostCard, TopAppBar. 
| **Economic identity** | One identity per productive entity (people, businesses, agents, machines) as Units; credential-gated minting. 
| **Task marketplace** | Posters publish objective + budget + deadline + verification rule; workers claim, execute, get paid on verification. |
| **Supply offers** | Spare capacity listed as offers (vehicle, space, skills, compute); buyers book, complete, and pay suppliers; money flows buyer → supplier. |
| **Micro-work splitting** | Projects split into micro-tasks with progress tracking; parents complete only when children are done. |
| **Referrals** | Workers mint invite codes; one redemption per invitee; growth signal per inviter. |
| **Engagement records** | Work classified at publish (gig, contract, trial) with terms reference; portable per-worker history with earnings and ratings. |
| **Opportunity scoring** | Scored demand (demand × fit × margin × speed × cost × scalability × adjacency) with debate hook; single-source scorer, thin proxy. 
| **Contract escrow** | Funds lock on acceptance, release on verified completion; milestone splits, kill-fee, dispute records. 
| **Reputation** | Ratings per completed task/contract, portable per-user aggregates; capability attestations; verification gate before first payout. 
| **Single ledger** | Every rupee movement as income/expense/staged/approved rows in one book; agents propose, humans approve. 
| **Business profiles** | Capability profile, structured capacity (headcount, shifts, offerings with quantity and lead time), order book, compliance docs; quantity and lead-time filters. |
| **Capability search** | Supplier search by capability and region, most capable first, over business profiles. |
| **Commerce pipeline** | Opportunity to cash: score, challenge, stage, human approve, execute via task, reconcile estimate versus actuals. |
| **Enterprise twin** | Live business model: derived task, cashflow, workforce, reputation, and pipeline measures plus owner-reported metrics feeds. |
| **Business agent** | Per-business duties (inventory watch, supplier discovery, market intel, quotation, analysis); event-driven runs with history. |
| **Data marketplace** | Consent-first datasets bound to Dataset units; purpose-bound access requests with logged grant, deny, and revoke; provenance lineage. |
| **Compute exchange** | Benchmarked nodes bound to Compute Node units serving published workloads only; code blobs rejected; queued to done lifecycle. |
| **Sensor network** | Structured human observations feeding business twins; reporter-only escalation into measured tasks. |
| **Drift + contract tests** | Schema drift guards (adapter built from kernel artifact, no shadowed keys); escrow lifecycle, rake math, verification gate jest suites. |
| **Trusted observations** | Source, device, geography, evidence, confidence on every observation; independent confirmations with self/double-confirm rejected; per-capability reporter reliability scores. |
| **Revenue rails** | Marketplace rake recorded per payout (runtime-changeable rate); platform revenue view. |
| **Loop decisions** | Every loop closes with scaled, abandoned, or pivoted verdict plus reason; kill reasons surfaced in twins. |
| **Market signals** | Weekly industry inputs (trends, demand, policy, tech costs) with staleness flags; carried into market intel. |
| **Capability ladder** | Rung-by-rung path from a business's capabilities to a target industry, with local supplier counts per rung. |
| **Industry scanner** | Market signals auto-drafted into scored opportunities; drafts accepted with edited economics. |
| **Ventures** | Research commercialization in gated rungs (lab, pilot, product, graduated, killed); evidence per gate, reasons for kills. |
| **Export orders** | Global orders with quote, compliance-gated confirm, ship, deliver lifecycle; forex estimates and policy incentive on delivery. |
| **Agent accounts** | API keys bound to AI Agent units; supervised spend caps enforced on proposals. 
| **Authoritative ledger** | Double-entry accounts, idempotency keys (webhooks pay once), pending→settled state machine, releases reference paid tasks instead of re-booking. |
| **Fee policy rails** | Runtime-changeable task/gig/contract rake, data/compute fees, and welfare head; splits computed at settle time, no redeploy. |
| **Verified gig payouts** | Gig drivers must own a verified unit before payout, closing the task-only verification gap. |
| **Settlement pipeline** | Contract authorize→provider→settle→reconcile→payout→report with idempotency at every step; provider failures settle nothing. |
| **Data and compute settlement** | Dataset grants book the flat access fee with license issue; compute completions book the node-rate fee; double grants and double jobs pay once. |
| **Dataset licenses** | First-class grant records with terms, purpose, and revocation; revoked licenses block future grants server-side. |
| **Agent proposal gateway** | Strict proposal envelopes (objective, action, budget, risk, capabilities, expected outcome, authorization); server-side authorize, deny, or needs-approval decisions. |
| **Execution receipts** | Idempotent execution evidence ingested as observations; invalid envelopes rejected, over-cap proposals denied. |
| **Prospect CRM** | Evidence-backed prospects (company, problem, triggers, value, contactability, confidence); dedup on company+problem; opt-out blocks outreach/pilot. |
| **Prospect bulk import** | `POST /api/prospects/import` pushes PIE discovery batches with within-batch dedup, per-row errors, created/deduplicated counts. |
| **Proposals** | Offer bridge: prospect + template + price → proposal; accept spins up the executing task + draft contract and marks the prospect pilot. |
| **Outreach pipeline** | Draft → human approve → capped send (1/7d) → classified response; unsubscribe auto-opts the prospect out. |
| **Proposal launch** | Accepted proposals split into budgeted microtask children under the delivery task; payouts bounded by the pilot price. |
| **Revenue funnel** | `GET /api/metrics/funnel` canonical dashboard: stage counts, responses by class, released wins, revenue/cost/margin in paise. |
| **Job ingestion store** | `POST /api/jobs/import` bulk-pushes normalized roles (dedup by job_id); `GET /api/jobs` lists. |
| **Job fit scoring** | `POST /api/jobs/:id/score` fits the role against your candidate twin via PIE; caches score + APPLY/TAILOR/OUTREACH/SKIP. |
| **Application tracker** | Packs stored per job; status follows the hiring pipeline with illegal jumps rejected server-side. |
| **Job outreach** | Network-first notes per role: draft → approve → capped send (5/day) → classified response. |
| **Jobs funnel** | `GET /api/metrics/jobs`: verdict mix, application pipeline, outreach counts, responses by class. |


## Stage A — Economic Substrate

No markets without identity; no transactions without trust. Substrate first.

### A1. Economic identity

Every productive entity gets one identity:

- Person / Business / Organization
- AI Agent / Service / Product
- Vehicle / Machine / Facility
- Compute Node / Dataset

### A2. Module layout (`fireflow/` + `economy/`)

- `units/` — identity + profiles (people, businesses, agents, machines)
- `opportunities/` — scored demand (see A4)
- `contracts/` — agreements + escrow states
- `tasks/` — units of paid work (see Stage B)
- `reputation/` — verification + ratings (see A5)
- `payments/` — cash books + approval gates
- `markets/` — task / data / compute / B2B exchange surfaces
- `agent_accounts/` — business_agent + worker agent accounts (credentials bound to AI Agent units)

### A3. Task marketplace

- Posters publish objective + budget + deadline + verification rule.
- Workers (human or agent) claim, execute, get paid on verification.
- Disputes resolve against the contract record, not chat logs.

### A4. Opportunity engine

Score every opportunity on:

demand × capability-fit × cost × margin × speed × scalability × adjacency

- Cheap gate first: capital-heavy ideas rejected before deep scoring.
- Debate hook: challenger argues against, scorer defends — only survivors run.

### A5. Reputation / verification

- Identity verification before first payout.
- Ratings per completed task/contract; portable across marketplaces.
- Capability attestations (tests, trial tasks) unlock higher-value work.

### A6. Contract / escrow

- Funds lock on acceptance, release on verified completion.
- Milestone splits for large work; kill-fee for cancelled work.

### A7. Universal transaction ledger

- Every rupee movement: income / expense / staged / approved.
- Human-approval gate on real money movement (agents propose, humans approve).
- One store only — no parallel books.

### A8. Business profiles + agent accounts

- Businesses: capability profile, capacity, order book, compliance docs.
- Agents: own accounts, own reputation, supervised spending limits.

### First coding target

Shared Economic Object Model + Opportunity/Task/Transaction API — one
language so FireFlow and PIE interoperate from day one.

---

## Stage B — People Earn

Turn spare human capacity into income.

### B1. `agent_tasks` schema

Every task carries:

objective / budget / deadline / inputs / required capabilities /
verification rule / reward / risk flag.

### B2. Spare-capacity monetization

- Vehicle idle hours → logistics / delivery slots.
- Rooftop / spare room → storage, solar, micro-warehousing.
- Skills after hours → review, tutoring, annotation, audit tasks.
- Devices idle → benchmarked compute contributions (see C4).

### B3. Micro-work flywheel

AI demand → distribute micro-tasks → workers earn → workers invite others →
supply grows → bigger projects become feasible → repeat.

### B4. Compliance from day one

- Worker classification, records, and social protection built in, not bolted on.
- Social Security Code in force (Nov 2025): gig/platform worker welfare,
  registration, and benefit rails are design inputs, not afterthoughts.

---

## Stage C — Businesses Earn

### C1. `industrial_b2b` profiles + capability search

- Every business: what it can make, capacity, lead time, quality record.
- Capability search queries: "who within 300 km can CNC aluminium ±0.05 mm?"
- Industrial capability graph of India — the map businesses buy into.

### C2. `business_agent`

Always-on agent per business doing:

sales outreach / procurement / inventory watch / customer support /
market intel / quotation drafting / supplier discovery / hiring screens /
business analysis.

### C3. `enterprise_twin` feeds

Live sync of: orders / inventory / costs / capacity / machines / workers /
suppliers / customers / energy / cashflow / defects / delivery times.

Twin → simulate decisions → execute → measure back into twin.

### C4. Data marketplace + compute exchange

- Data marketplace: consent-first, provenance-tracked datasets; DPDP
  compliance as a first-class feature, not a banner.
- Compute exchange: benchmarked, sandboxed nodes; published workload list
  (render, inference, simulation, annotation QA). No arbitrary customer code
  ever runs directly on hosts.

### C5. Agent-mediated commerce pipeline

score → challenge → stage → approve → execute → reconcile → twin-update.
Same pipeline for a ₹500 task and a ₹50 lakh order — only the gates scale.

### C6. Interoperate, don't rebuild

Plug into open commerce networks for discovery and settlement; build only
the twin, scoring, and execution layers that are ours.

### C7. Human sensor network (closed loop)

People observe → twin updates → simulate → execute in the world →
measure → learn. Humans are the highest-resolution sensors.

### C8. Ride-hailing: LATER

Only as a logistics capability (move goods/people for other jobs), never as
a standalone consumer app bet.

---

## Stage D — Economic Autonomy

### D1. Revenue priority (in order)

1. B2B services (agent-built, agent-delivered)
2. Task marketplace rake
3. Data marketplace fees
4. Compute exchange margin
5. Enterprise twins (SaaS)
6. Procurement / supply-chain services
7. Export facilitation
8. Industrial intel reports
9. Skilling-to-earning pipelines
10. Consumer ads (last — never the engine)

### D2. Economic loop stages

observe → discover → estimate → simulate → rank → task → execute →
collect → reconcile → twin → learn → scale / abandon / pivot.

Every rupee tracked; every loop either scales or gets killed with a reason.

### D3. Geography

Kanpur = operations base. India = the market. Win at home first.

### D4. `future_industry_engine` (weekly inputs)

Trends, demand signals, policy shifts, technology costs — refreshed weekly,
feeding the opportunity engine.

### D5. `industrial_pathfinder` ladder

Climb rung by rung (services → components → systems → industries). No direct
jump to the Moon — each rung funds the next.

---

## Stage E — Industrial Leap

- **Industrial graph:** who makes what, where, at what capacity, at what cost.
- **Technology graph:** which capabilities unlock which industries.
- **Future-industry scanner:** where demand is moving before it arrives.
- **Pathfinder:** cheapest viable ladder from here to there.
- **Research commercialization:** lab → pilot → product pipeline.
- **India-wide supplier graph:** the B2B map as infrastructure.
- **Export engine:** domestic capability → global orders.
