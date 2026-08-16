- Keep all files in `/system_development_report` under 1000 lines.

## Dev Report Integrity Rule

Every status claim in `system_devpt_reports/` must include a file path + function/class reference that exists in the current codebase. "✅ Working" without a verifiable anchor gets deleted on sight. Before closing any session, grep each report to confirm every cited function still exists — if it was refactored or deleted, update the report or remove the entry.- 

## system_devpt_reports/ File Convention

- `README.md` = how to use/run the module (user-facing docs)
- `status.md` = current verified capability with citations (agent-facing, verified before every session)
- Prefer `status.md` over `roadmap.md` for determining "what works."
- `roadmap.md` = speculative/planned work, never cited as working

## Report Freshness Rule

1. Every system_devpt_reports/*.md status file (not roadmap files) must carry a `_Last verified: <date>_` line under its title.
2. Before using any status report to decide what to build next, check its Last-verified date against the most recent related code change. If the report predates a change to files it describes, treat it as unverified.
3. Before ending any session that touched code: update the Capability/Gaps section of the relevant status file, append one line to Recent Changes, and bump Last-verified.
4. Status files never contain roadmap/speculative content. If a status file and a roadmap file disagree, the status file wins.
5. Citations (`file.py:function()`) in status files must be checked against the codebase before a session closes.
Status reports are subject to the same verify-before-trusting rule as code — see rule 1 in Operating Rules.

## Report maintenance protocol

### Session start (read path)
- Call `report_freshness`.
- If any status is stale or missing stamp → re-validate before trusting.
- Prefer `status.md` over `roadmap.md` for "what works."

### Session end (write path) — if code changed
- Update only modules you touched.
- For each new/changed public behavior: add/adjust one capability line with citation.
- For removed behavior: delete capability line; if intentional removal, record reason in `project_history` (`contradicts` / why).
- Append one Recent Changes line; trim to 10.
- Bump `_Last verified`.
- Optionally: `python scripts/validate_capabilities.py` (must exit 0 for touched modules).

### Schema enforcement
- Status files without `_Last verified` are treated as empty.
- Capability lines without `file:function()` are deleted on sight (existing Dev Report Integrity Rule).
- Roadmap content found in status → move to roadmap, do not leave dual.

### Empty-file rule
- Empty `status.md` is a defect. Either fill minimal schema within the session that touches the module, or remove the module report directory if the module is abandoned.

### Single writer for automated claims
- Prefer regenerate-from-hypotheses over hand-editing long tables once generator exists. Until then, hand-edit only the thin template.

One-command validation: `python scripts/seed_hypotheses.py --quiet && python scripts/validate_capabilities.py --quiet`