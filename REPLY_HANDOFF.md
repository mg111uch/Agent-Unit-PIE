# Reply handoff — paste into a fresh agent session when a prospect replies

> A prospect replied to our outreach. CRM is live: FireFlow backend
> (`cd /home/manigupt/Hello/reddit-clone/backend && npm start`, localhost:5000).
> Login: username `pie_operator`, password from file
> `/home/manigupt/Hello/reddit-clone/backend/.pie_operator` (JWTs expire in 1h).
> Sender signature: `/home/manigupt/Hello/reddit-clone/backend/.sender_identity`.
> Economy code: `/home/manigupt/Hello/Agentic_Unit_PIE/codebase/modules/economy/`
> (`outreach.py`, `revenue.py`, `service_templates.py`, `delivery.py`).
> Runbook: `system_devpt_reports/economy/README.md` → Revenue loop.
>
> THE REPLY (paste raw text + which outreach id it answers, #1 Cybernetik or #2 LB-14247):
>
> [paste here]
>
> Do, in order:
> 1. Classify with `outreach.classify_response` (PIE) / `lib/outreach.js` (FireFlow).
> 2. Record: `POST /api/outreach/:id/respond {"response_text":"..."}`.
> 3. Act on the class: `interested` → draft a `POST /api/proposals` (template + price from the original offer) and show it to me for approval, never auto-create; `later`/`not_relevant` → tell me the parking note to set; `unsubscribe` → confirm opt-out applied; `wrong_person` → propose contact re-lookup.
> 4. Report funnel (`GET /api/metrics/funnel`) and the single next step.
>
> Rules: never send anything externally yourself; every outbound needs my explicit approval. No new dependencies without asking.

---

# Job-hunt handoff — paste into a fresh agent session to continue the job loop

> Continue Manish's personal job hunt. Same backend/auth as above.
> Jobs code: `codebase/modules/economy/jobs/` (`candidate.py`, `sources.py`,
> `fit.py`, `apply.py`, `job_outreach.py`, `learning.py`) + `revenue_job.py` pattern.
> Runbook: `system_devpt_reports/economy/README.md` → Revenue loop + Features table.
> Candidate: resume at `/home/manigupt/Hello/reddit-clone/backend/resume.md`,
> twin prefs = ₹1L/mo floor, ±3h IST, full-time/contract, **india_first + no-relocation**
> (non-India or onsite-only caps at OUTREACH — never loosen without asking).
> Status source of truth: `system_devpt_reports/economy/status.md` → Next/Recent.
>
> Steady-state loop (daily):
> 1. Fetch feeds (`sources.fetch`: remoteok, wwr programming, greenhouse gitlab,
>    ashby linear, hasjob) → import new engineering roles (`POST /api/jobs/import`).
> 2. Score `new` rows (`POST /api/jobs/:id/score`) → report APPLY/TAILOR with scores.
> 3. TAILOR+ → build pack (`apply.build_pack`, gate-checked) → log
>    (`POST /api/applications`) → show cover + apply URL for MY manual submit.
> 4. OUTREACH-grade → draft via `job_outreach.draft_job_message`, log
>    (`POST /api/job-outreach`), show for approval. Never send anything yourself.
> 5. My reports (`applied <company>` / replies) → advance tracker
>    (`POST /api/applications/:id/status`) / classify (`POST /api/job-outreach/:id/respond`).
> 6. Report jobs funnel (`GET /api/metrics/jobs`) + one next step.
>
> Live state (2026-09-17): 95 scored; READY packs = Pivotal Health, GitLab-agent
> (PARKED Remote-Canada), DealerGPT, RSG, VexarDrive (hybrid-caution); 2 job-outreach
> drafts pending approval. Revenue loop parked awaiting 2 replies (see above).
