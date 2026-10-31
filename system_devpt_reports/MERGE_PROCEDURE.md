# README merge procedure (v1 → v2 structure, zero information loss)

> **Status 2026-10-25: complete.** The `system_devpt_reports_v2/` directory has been removed; merged docs live in `system_devpt_reports/<module>/README.md`. The old root master README is now `vision.md` (Level 2), and `00_README_master.md` is the Level-0 entry. This file is kept as the method record, not as pending work.
> **Audience:** the next agent doing doc unification.
> **Goal:** replace each v1 module `README.md` in `system_devpt_reports/<module>/` with the v2 rewrite, **without losing a single fact**.
> **Status of this batch (2026-10-25):** ✅ kernel · ✅ populaDyn_simu · ✅ fireflow_app · ✅ economy · ✅ digital_twins · ✅ debate_argu · ⏭ agent_core (deliberately skipped).

---

## 1. Golden rules

1. **v2 is the skeleton, v1 is the content.** Keep v2 headings/§ numbering/markers; restore every v1 capability, detail, number, path and command into them.
2. **Shipped detail must survive.** v1 feature tables are the record of what exists. A row may be re-worded or regrouped — never dropped.
3. **Only two normalizations are allowed:**
   - phase/stage/step labels are removed from feature tables (DOC-02) — the *capability name* stays;
   - `file.py:123` → `file.py` + symbol (R3/DOC-05) — no line numbers.
   Anything else that disappears is information loss.
4. **Never invent or "improve" facts.** If v1 and v2 disagree, keep both sides visible and flag it (see §6). Do not silently mark a gap as shipped.
5. **Level-2 files stay untouched.** `usage.md`, `roadmap.md`, `status.md`, `SimDvptPhases.md`, benchmarks etc. remain authoritative for detail and are only *referenced* from the README. They are not backups and not merge targets.
6. **No git commands.** Work with file copies.
7. **`agent_core/` is out of scope** — v2's `agent_runtime/` is a 66-line reconstruction, not a merge base.
8. **Report to the user only after verification passes** (§5), and keep the reply ≤200 words.

---

## 2. Backup (do this first, every time)

```bash
mkdir -p legacy_project_docs/v1_doc_backup_<YYYY-MM-DD>/<module>
cp system_devpt_reports/<module>/README.md \
   legacy_project_docs/v1_doc_backup_<YYYY-MM-DD>/<module>/README.md
```

- **README only.** Do not back up `roadmap.md`, `status.md`, `usage.md`, `SimDvptPhases.md`, or benchmarks — they stay live and unmodified.
- **Never** use `/tmp` (erased on restart).
- Exact copies are unmarked. If a copy was missed and you must reconstruct, say so in `legacy_project_docs/v1_doc_backup_<date>/README.md` (there is a provenance table there — extend it).
- The backup folder is **archive-only**: never edit merged docs there.

---

## 3. Procedure

### Step 1 — Read four things
1. `system_devpt_reports/<module>/README.md` (v1)
2. `system_devpt_reports_v2/<module>/README.md` (v2)
3. v1 `roadmap.md` / `status.md` / usage-style files **if they exist** — their *open* items must not vanish from the doc set (see Step 4)
4. `system_devpt_reports_v2/02_roadmap_master.md` + `03_loopholes_and_suggestions.md` — to reuse existing IDs and avoid duplicating register entries

### Step 2 — Build a coverage list before writing
Enumerate, from v1:
- every feature-table row (keep the row label),
- every number/threshold/limit,
- every file path, class, function, command, flag, endpoint, config key,
- every "Next steps" / deferred item,
- every invariant/constraint sentence (e.g. "no parallel books").

### Step 3 — Write the merged file
- Start from the v2 file; keep `Level 1` framing, `[LOOPHOLE]/[SUGGESTION]/[VERIFY]` markers, status legend.
- Restore v1 specifics into the matching v2 section (usually as a longer table cell, occasionally a new row).
- Restore v1-only rows under the nearest v2 section.
- Keep v2's genuine improvements (corrected stale claims, new register items) — but mark the correction (e.g. "the old row is stale, DOC-03").
- Add a Level-2 pointer row/table: which file holds mechanics detail.

### Step 4 — Roadmap duplication guard
If v1 has its own `roadmap.md`, the merged README may summarise its items, but add:
> `roadmap.md` remains the single plan of record; this table is the direction-session summary.
Reconcile stale roadmap wording against the shipped log instead of copying it forward verbatim, and list what is genuinely still open.

### Step 5 — Fix v2 false negatives
v2 was generated from a subset of inputs, so it says *"not supplied"* about files that exist (`AGENTS.md`, prompt fragments, module `roadmap.md`/`status.md`/`usage.md`, stock/virtual_silicon docs). Replace those with the real path, or drop the note.

### Step 6 — Verify (mandatory)

```bash
python - <<'PY'
import pathlib, re
mod = '<module>'
new = pathlib.Path(f'system_devpt_reports/{mod}/README.md').read_text()
old = pathlib.Path(f'legacy_project_docs/v1_doc_backup_<DATE>/{mod}/README.md').read_text()
def toks(t):
    out = set()
    for m in re.findall(r'`([^`]+)`', t):
        for p in re.split(r'[\s,;(){}\[\]]+', m):
            p = p.strip('.:"\'')
            if len(p) >= 4 and re.search(r'[A-Za-z]', p):
                out.add(p)
    return out
missing = sorted(t for t in toks(old) if t not in new)
print('missing code tokens:', missing)
lines = new.splitlines()
print('lines:', len(lines), '| malformed table rows:',
      [i+1 for i, l in enumerate(lines) if l.startswith('|') and l.count('|') < 3])
PY
```

Then, for files whose v1 rows use **bold labels** instead of backticks, also check row labels:

```bash
python - <<'PY'
import pathlib, re
v1 = pathlib.Path('legacy_project_docs/v1_doc_backup_<DATE>/<module>/README.md').read_text()
new = pathlib.Path('system_devpt_reports/<module>/README.md').read_text().lower()
for m in re.finditer(r'^\| \*\*(.+?)\*\*', v1, re.M):
    if m.group(1).strip().lower() not in new:
        print('row label missing:', m.group(1))
PY
```

Acceptable residual "missing" tokens: line-numbered citations, slash-joined names that are now separate spans, markdown bold artifacts, and intentional renames. Everything else must be fixed. Re-check every restored number by grepping it.

*Calibration:* run against `kernel` it reports 24 residuals out of 276 v1 tokens — every one of them a line-number citation, a slash-joined name, `<1.9KB` vs `<1.9 KB`, or a renamed heading. That is a pass, not a failure.

Also confirm: `grep -rn "not supplied" system_devpt_reports/<module>/` returns nothing false; file ≤500 lines.

### Step 7 — Report
State: file + line count, rows restored, numbers verified, normalizations applied, contradictions found (and whether fixed), backup location. Then move to the next module.

---

## 4. Per-module status

| Module | v1 | v2 | Action |
|---|---|---|---|
| `kernel` | README + usage + roadmap + status | README | ✅ merged 2026-10-25 |
| `populaDyn_simu` | README + roadmap + status + SimDvptPhases | README | ✅ merged 2026-10-25 |
| `fireflow_app` | README + roadmap | README | ✅ merged 2026-10-25 |
| `agent_core` | 8 files (1,424 L) | `agent_runtime/` (66 L) | ⏭ **skip** — leave as is |
| `economy` | README 74 L | README 106 L | ✅ merged 2026-10-25 (→131 L) |
| `digital_twins` | README 25 L | README 66 L | ✅ merged 2026-10-25 (→81 L) |
| `debate_argu` | README 284 L | README 89 L | ✅ merged 2026-10-25 (→126 L; v2 was a condensation, internals restored) |
| `codebase_atlas` | README 251 L | — | no merge; keep v1 |
| `stock_analyser` | README 265 L | — | no merge; keep v1 |
| `virtual_silicon` | README 300 L | — | no merge; keep v1 |

Modules with **no v2 README**: leave untouched. Do not port them into the v2 set without a separate instruction.

**Open doc inconsistencies to resolve when the owning module is merged** (do not leave silent):
- `populaDyn_simu/status.md` still claims init is non-deterministic and `heal`/`trade`/`produce` return-intents are open, while the README says done.
- `fireflow_app/roadmap.md` still lists tests / data-compute settlement / ledger double-count / gig-verification as unbuilt although the shipped log says otherwise (marked shipped in the README).
- `agent_runtime/README.md` renamed the doc folder but the master doc still points at code dir `codebase/agent_core/`.
- `digital_twins/status.md` lists the `create_pattern` / `signal_to_event` seam fixes as still-to-do; the README records them verified (flagged in the merged README §8).
- `debate_argu/status.md` "Known Gaps" still list the missing `/argu add-topic` tool and the broken `llm_compiler`, both shipped since (flagged in the merged README §8).

---

## 5. Definition of done

- [ ] v1 README copied to `legacy_project_docs/v1_doc_backup_<DATE>/<module>/README.md` **before** editing
- [ ] merged file lives at `system_devpt_reports/<module>/README.md`
- [ ] v2 structure/markers retained; all v1 rows, numbers, paths, flags, endpoints present
- [ ] only allowed normalizations (phase labels, line numbers)
- [ ] no false "not supplied"; no invented facts; contradictions flagged
- [ ] Level-2 files untouched; roadmap "single plan of record" note added where needed
- [ ] verification script clean; ≤500 lines; tables well-formed
- [ ] user report ≤200 words, backup location included
