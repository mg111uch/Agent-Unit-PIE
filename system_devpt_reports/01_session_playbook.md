# Session Playbook (Level 1) — running a direction session with docs only

> **Use:** after each coding iteration, paste the docs (never code) into a fresh LLM session and ask where development should go next. The advisor must understand PIE and FireFlow **from the docs alone**. This file defines what to paste, what the coding agent must report, how the advisor answers, and which questions to ask.

## 1. What to paste

| Always | Often | Only if relevant |
|---|---|---|
| `00_README_master.md` · `03_loopholes_and_suggestions.md` · `02_roadmap_master.md` · latest **Iteration Report** (§2) · tail of `04_iteration_log.md` | the module README(s) the iteration touched (+ its `roadmap.md` / `status.md`) | the other module READMEs; `vision.md` for intent |

If total size is too large: master + register + roadmap + report first; module docs on demand. The advisor must say which doc it would like next rather than guess.

## 2. Iteration Report (the coding agent fills this after every iteration; no code inside)

```markdown
## Iteration <N> — <date>
**Goal (one line):**
**Gate(s) targeted:** G0/G1/… or C1/… or "none"
**Outcome:** PASS | PARTIAL | FAIL — one-sentence reason

### Changes (table-ready, no phase/step labels)
| Feature | Notes |   ← one line per shipped capability; module + file + symbol

### Tests
| Suite | Result (pass/total) | New tests |
|---|---|---|

### Register changes
- Closed: <IDs> · Opened: <new IDs + one-line> · Re-rated: <ID old→new>

### Metrics snapshot (omit unknown, never invent)
- Funnel (`/api/metrics/funnel`): prospects / researched / contacted / responses / meetings / proposals / pilots / won / revenue ₹ / cost ₹ / margin ₹ / repeat customers
- Jobs funnel: verdict mix / applications / outreach / responses
- Kernel: registry ACTIVE / PARTIAL / DORMANT / DEPRECATED · smoke x/9 · eval harness pass
- Twins: placeholder vs observed/verified fields per city · baseline error · max agents run
- Ops: last backup date + restore tested? · CI green? · LLM spend this iteration

### Decisions made (with reason) · Open questions for the advisor
### Docs updated (paths) · Docs found stale/contradictory
### Answers to [VERIFY] questions (ID: answer)
```

## 3. Opening prompt (copy/paste)

```
You are the development-direction advisor for PIE (agent) + FireFlow (app). You have only docs — no code.
Read 00_README_master.md first, then the register, roadmap and the latest Iteration Report.
Do NOT ask me for code. If you need a fact the docs don't give, list it as a [VERIFY]-style question for the coding agent.
Respond in the format in the playbook §5. Cite register/roadmap IDs. Prefer the smallest next step that moves a gate.
```

## 4. Advisor rules

1. **Gate-first.** Identify the nearest unmet gate (roadmap §2). Until **G1 (first paid pilot)** is met, any task not on the path to G0/G1, money safety, or documentation correctness needs a written justification.
2. **Respect invariants** (master §11) and the freeze list (STR-01). Reject proposals that violate them (e.g., second brain in FireFlow, scraping portals, arbitrary code on compute hosts, hand-editing `graph.json`).
3. **Docs ≠ truth.** Code is the source of truth. When docs conflict (see register Section K and DBT-01/02/03) say so, and ask for confirmation before recommending work that depends on it.
4. **Evidence honesty.** Don't promote a claim above what the evidence ladder allows (HYPOTHESIS → REPLICATED → FALSIFICATION_PASSED → VALIDATED_OOS). Small-N funnel numbers are hypotheses.
5. **Real-world risk.** For money, outreach, personal data, payments, tax or labor law: give considerations and tell the user to confirm with a lawyer/CA; never present legal conclusions as settled.
6. **No code in answers.** Describe behavior, interfaces, acceptance tests, and data contracts. The coding agent writes code.
7. **Small batches.** ≤3 tasks per iteration, each with an acceptance gate the coding agent can demonstrate and report.
8. **Update the register.** Every answer ends with register deltas (new IDs / closed IDs / re-ratings) and doc updates required.

## 5. Advisor response format

```
1. Verdict on last iteration: <continue | correct course | stop-and-fix> — why (2–4 lines, cite evidence)
2. Gate status: G0 … G5 / C1 … C4 / J1 … J2 table (met / not met / unknown)
3. Next iteration (≤3 tasks): each = goal · why now (IDs) · acceptance test · docs to update · risk
4. Questions for the coding agent (numbered, answerable from code in minutes)
5. Register deltas: new / closed / re-rated
6. Things to stop doing or defer (with reason)
7. Watch-list: top 3 risks for the following iteration
```

## 6. Question bank (ask the coding agent; paste answers back)

**Integration** — Which process moves FireFlow events into the kernel unattended? What actor identity does PIE use when pushing? What happens when the PIE CLI times out? After import, who owns prospect status?
**Money** — Which payment/payout providers, what mode? Global kill switch? Can a contract run with escrow off and manual payment? SQLite pragmas, backup schedule, last restore test? What does `reconcile` compare against? Any invoice/tax line?
**Revenue** — Funnel numbers; how many prospects have non-seed provenance; is `send` a real transport (provider/domain/caps); how does a customer accept and receive a deliverable; who performs each task of `supplier_discovery_100` and at what cost per verified record; how is a delivered batch QC'd?
**Sensors** — What defines "independent" confirmation? Any gold/audit observations?
**Kernel** — Registry counts by status; is the above-HYPOTHESIS rule enforced in code; do revenue findings carry fee-policy/template versions; any DB-locked errors?
**Simulation/twins** — Largest completed population run and time; baseline error at that scale; is `param_hash` in run identity; placeholder vs observed fields per city; does `/game` run on the generic core?
**Debate** — live paths of `belief_state.json`, `interaction_log.json`, topic store; does the analyzer accept `contradicts`; chroma path.
**Jobs** — what the application "submit" gate does; whether overlap gating is hard; any interview/offer records; funnel numbers.
**Ops** — CI status; secrets locations/rotation; Next.js version and `npm audit`; LLM provider and cost per `/auto` run.

## 7. Doc-health checks the coding agent runs each iteration (cheap)

- `grep -rniE "phase [0-9a-z]|stage [a-e]" system_devpt_reports/` → should return nothing in feature tables.
- Ports, absolute personal paths (`/home/…`), line-number citations (`\.py:[0-9]+`) → none.
- Dates: kernel manual "last verified" ≤ last kernel change.
- Every new feature row has file + symbol; every unimplemented idea is in `02_roadmap_master.md`, not in a README table.
- Register: each `[LOOPHOLE/SUGGESTION/VERIFY]` ID in a module doc exists in the register and vice-versa.
- `04_iteration_log.md` appended; Iteration Report saved.

## 8. When the advisor should say "stop"

- A proposed task adds surface area while G1 is unmet and no register ID justifies it.
- Metrics claim improvement from tiny N.
- Any step would move real money, contact real people, or process personal data without a recorded human approval path.
- The same loophole (S1/S2) has been re-deferred twice.
