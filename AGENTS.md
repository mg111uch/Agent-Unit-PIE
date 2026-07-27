# AI Agent Development Guidelines 

## Task 

In `Agentic_Unit_PIE/system_devpt_reports/FeatureIdeas.md` are given terminal logs of calls made to llm by agent loop.In `Agentic_Unit_PIE/system_devpt_reports/agent_efficiency_plan.md` is given the plan to make the agent more efficient. We need to implement this. Code snippets given are only suggestions, dont implement them varbatim, only take hints to make code better.

Do not give code or make any changes. Just short give a plan or an answer. 

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/Agentic_Unit_PIE`
- **Codebase atlas:** `/home/manigupt/Hello/Agentic_Unit_PIE/atlas_output`
- **Source_code:** (Working directory) `/home/manigupt/Hello/Agentic_Unit_PIE/codebase`
- **Agent frontend** `/home/manigupt/Hello/Agentic_Unit_PIE/codebase/frontend`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase && conda run -n myenv python server.py`

## Kernel Probing Rules (Mandatory)

**Never `Read` a file under `kernel/` — use `pie_file_api` first, always.** See `Agent_graph.html` notes panel for the full tool-selection table, token-saving workflow, anti-patterns, and atlas-miss escalation.

After editing/creating/deleting any kernel files, regenerate the code_rag.db atlas:
```bash
cd /home/manigupt/Hello/Agentic_Unit_PIE/codebase/agent_tools/atlas_tools && python run_cmds.py /home/manigupt/Hello/Agentic_Unit_PIE/project_tools.md "Make Codebase_atlas"
```

## Core principles

- Small scope always
- Strict modularity — Single responsibility, clear interfaces, minimal coupling.
- Ask the user before installing modules and libraries.
- Ask the user before running tests and verifying implementation.
- Smoke tests are allowed. Keep them small.
- Optimize for handling large codebases while maintaining output quality.
- Generate code which is less verbose to save tokens without compromising on functionality.
- Max 400–500 lines per file (including tests & comments).
- One public class/struct/interface per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.
- Keep all files in `/system_development_report` under 1000 lines.

## Dev Report Integrity Rule

Every status claim in `system_devpt_reports/` must include a file path + function/class reference that exists in the current codebase. "✅ Working" without a verifiable anchor gets deleted on sight. Before closing any session, grep each report to confirm every cited function still exists — if it was refactored or deleted, update the report or remove the entry.

### Operating rules

1. **Verify before trusting** — grep for actual call sites before relying on any "✅ Working" claim.
2. **Kernel owns cognition; modules orchestrate** — argu_god (and any future module) calls into kernel; it does not reimplement.
3. **Don't build empty kernel files ahead of a real consumer** — Tier 5 stubs stay empty until a second module genuinely needs them.
4. **One persistence path** — SQLite only now; don't let a future module invent a second.
5. **Every removal needs a reason on record** — already enforced by the project_history topic's `contradicts` edges.

## Tooling Workflow Rules

1. **Use `batch_edit` for repetitive edits across a single file** — Instead of many sequential `edit_file` calls for the same file (e.g., adding the same parameter to every registration), use one `batch_edit` call with all replacements. The tool applies edits sequentially and supports `replace_all` for bulk renames.

2. **Verify directory paths with `list_files` before reading** — When uncertain about a file's location or the directory structure, call `list_files` on the suspected parent directory first. Guessing paths (e.g. `kernel/tools/` when the actual prefix is `agent_core/tools/`) wastes a round trip on a file-not-found error.

3. **Prefer `pie_batch_file_api` when ≥2 files** — batch reduces token overhead vs. serial `pie_file_api` calls.

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
- Call `pie_report_freshness`.
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
