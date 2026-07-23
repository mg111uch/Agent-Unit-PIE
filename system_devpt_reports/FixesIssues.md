# Fixes & Remaining Work

_Last updated: 2026-07-23_  
_Source: multi-agent implementation of FeatureIdeas + original FixesIssues plan_  
_Verified against live repo + `pie_report_inventory` / `pie_list_capabilities` / `validate_capabilities.py`_

---

## 0. What is done (do not re-implement)

Phase 1 + most of Phase 2 completed by multi-agent work. Verified:

| Area | Evidence |
|------|----------|
| **A1–A8** Status schema | All 5 module `status.md` use template + `_Last verified: 2026-07-23`; sum ≈109 lines (&lt;250). `debate_argu/improvement.md` deleted |
| **B1–B4** Scripts | `scripts/lib/citations.py`; seed auto-discovers `*/status.md`; validate has `--json` / module grouping; 30/30 capabilities PASS |
| **C1–C5** MCP report tools | `pie_report_inventory`, `pie_report_schema_check`, `pie_list_capabilities`, `pie_resolve_citations` live |
| **D1–D4** AGENTS.md | Report maintenance protocol, batch_file_api rule, one-command seed+validate, status ≻ roadmap |
| **E1–E3** Dogfood Stage 1 | 30 `capability_claim` + 15 `known_gap` hypotheses seeded; validate exit 0 |
| **F1–F4** Doc slim | Thin statuses; `agent_core` design essay → `project_docs/agent_core_design.md`; slim agent_core/debate roadmaps |

**One-command health:**  
`python scripts/seed_hypotheses.py && python scripts/validate_capabilities.py`

**Operational tools:** `pie_report_freshness`, `pie_report_inventory`, `pie_report_schema_check`, `pie_list_capabilities`, `pie_resolve_citations`

---

## 1. Not done — open backlog

### 1.1 Process / docs (small, high leverage)

| ID | Task | Why open | Verification |
|----|------|----------|--------------|
| **B5** | Shrink seed + validate + `citations.py` to ≤250 LOC (now ~336) | Shared lib kept full resolve/parse surface | `wc -l scripts/seed_hypotheses.py scripts/validate_capabilities.py scripts/lib/citations.py` ≤ 250 without dropping flags |
| **D5** | Audit `codebase/prompt_fragments/` for always-on bloat; load only enabled packs | Never prioritized; ~105 lines across 10 fragments | Measure system prompt size before/after; packs filter verified in `prompts.py` |
| **F5** | Cap roadmaps | `codebase_atlas/roadmap.md` still ~201 lines; `kernel/roadmap.md` ~65; `populaDyn_simu/roadmap.md` empty | Near-term sections short; long wishlists → `project_docs/` or delete empty |
| **F6** | Document “do not Read `atlas_output/children/` for routine work” in AGENTS.md | Missed | Rule present under tooling / anti-patterns |
| **Schema-check false positives** | `pie_report_schema_check` flags Known Gaps / Recent Changes bullets as “without citation” | Checker treats all bullets like Capability lines | Only enforce citations under `## Current Capability` |

### 1.2 Kernel dogfood Stage 2–3 (Agent E remainder)

| ID | Task | Anchor | Verification |
|----|------|--------|--------------|
| **E4** | Link gaps that block roadmap items with `requires` / `required_by` edges | `kernel/ontology/relation_types.py` already has types | Blockers queryable on relation graph |
| **E5** | Export validated capabilities + gaps via `HypothesisEngine.export_to_semantic_memory` | Stage 2 | Retrieval/debate can surface capability state |
| **E6** | Emit `dev_change` events on intentional session end (`EventEngine.create_event`) | Stage 3 | Events in timeline with paths + summary |
| **E7** | Drive status Recent Changes from last 10 `dev_change` events (or document hybrid until renderer) | Stage 3 | Recent Changes matches event log or explicit hybrid rule |

**Gate:** do not start E6–E7 until E4–E5 (or multi-session Stage 1 honesty) is proven useful.

### 1.3 Phase 3 — generate-don’t-maintain (deferred)

| ID | Task | Verification |
|----|------|--------------|
| **C6** | `scripts/render_status.py` — hypotheses + events → `status.md` | Generated matches control sample |
| **C7** | Change-triggered revalidation (mtime / path hooks; avoid full re-check every render) | Only re-resolves when cited paths change |
| **C8** | Deprecate hand-edited capability tables; AGENTS.md says treat status capability section as cache | No routine hand-edits to capability bullets |
| **D6** | Intentional removals only in `project_history` with `contradicts` | Graph has removal rationale nodes |
| **D7** | Failed citation validation → suggest project_history note | Validator/tool emits suggestion |
| **D8** | Onboarding via `project_history` + capability hypotheses (prompt fragment) | Fragment exists; agents not forced to read 4 long reports |

### 1.4 Optional later (from original plan §5 / dogfood extras)

| ID | Task | Priority |
|----|------|----------|
| **O1** | Capability regression signal when validate fails after git change | Med |
| **O2** | Tool-bypass pattern: repeated `Read` on indexed kernel files → `detect_repeated_events` | Med |
| **O3** | INDEX.md health badge from inventory + validate | Low |
| **O4** | Dream cycle / TTL sweep on working_memory (dry-run first) | Low — destructive |
| **O5** | Merge or delete residual `scripts/verify_citations.py` if fully redundant with validate | Low |
| **O6** | Hypothesis status after validate still `proposed` in list_capabilities — confirm whether `validate_hypothesis` should flip to validated/rejected and fix if not | Med (integrity) |

---

## 2. Known residual issues (not full features)

1. **`pie_report_schema_check` noise** — gaps/recent bullets fail citation rule; fix checker before treating “clean: false” as real status rot.
2. **Fat roadmaps** — atlas roadmap still phase-essay style; contradicts “roadmap = short speculation.”
3. **Empty `populaDyn_simu/roadmap.md`** — fill minimal deferred list or remove file.
4. **`kernel/README.md`** — absent from inventory (deleted or never filled); add short how-to or leave intentionally absent with note in kernel status.
5. **Script LOC (B5)** — optional polish; do not block Stage 2.

---

## 3. Future development path

Ordered so each step reuses existing machinery; stop if earlier stage is not load-bearing.

### Wave 0 — Hygiene (1 short session)

1. Fix schema-check to scope citations to Current Capability only.  
2. AGENTS.md: add F6 atlas_children anti-pattern.  
3. Slim `codebase_atlas/roadmap.md`; fix empty populaDyn roadmap.  
4. Confirm O6 (hypothesis status after validate).  
5. Optional: B5 LOC trim + verify_citations merge (O5).

**Exit:** inventory + schema_check + validate all green with low noise.

### Wave 1 — Stage 2 dogfood (E4–E5)

1. For each `known_gap` that blocks a near-term roadmap bullet, create `requires` / `required_by` edges in semantic memory (same vocabulary as project decisions).  
2. Batch `export_to_semantic_memory` for validated caps + gaps.  
3. Smoke: agent or debate can retrieve “what is broken / blocked” without reading markdown.

**Exit:** gaps are queryable relations, not only status bullets.

### Wave 2 — Stage 3 events (E6–E7)

1. Session-end helper or tool: `dev_change` event (summary, paths, optional git sha).  
2. Keep hand Recent Changes until 3–5 real sessions emit events cleanly.  
3. Then either auto-fill last 10 lines or document hybrid.

**Exit:** changelog is not only human memory.

### Wave 3 — Stage 4 renderer (C6–C8)

1. `render_status.py` from hypotheses (+ optional events).  
2. mtime-triggered revalidation only.  
3. AGENTS.md: capability tables are generated cache.

**Exit:** status capability section cannot silently diverge from hypotheses.

### Wave 4 — Self-evolution extras (D6–D8, O1–O4)

1. project_history onboarding fragment (D8) + removal discipline (D6–D7).  
2. Regression signals (O1), tool-compliance patterns (O2).  
3. Dream cycle only with dry-run + archive (O4).

**Exit:** reports + history + hypotheses are one reasoning surface for agents.

### Non-goals (still)

- Second persistence backend  
- LLM that rewrites status without citations  
- Full autonomous project manager before Waves 0–2 are stable  
- Re-expanding status.md with phase archaeology  

---

## 4. Session checklist (agents)

**Start**

1. `pie_report_freshness` and/or `pie_report_inventory`  
2. Prefer `*/status.md` over roadmaps for “what works”  
3. `pie_list_capabilities` if hypothesis state needed  

**End (if code or status changed)**

1. Update touched module status citations  
2. `python scripts/seed_hypotheses.py && python scripts/validate_capabilities.py`  
3. Bump `_Last verified`  
4. Do not implement Wave 3+ unless Waves 0–1 are already green  

---

## 5. Success criteria still open

| Criterion | Status |
|-----------|--------|
| No empty status.md for active modules | **Met** |
| One schema across modules | **Met** (minor schema-check noise) |
| One command validates citations | **Met** |
| Session protocol in AGENTS.md | **Met** |
| Kernel Stage 1 multi-session proof before Stage 2–4 | **In progress** — Stage 1 seeded; E4+ not done |
| project_history sole removal log | **Policy met**; D6–D7 automation open |
| Agents answer “what works?” without phase diaries | **Mostly met** — use status + tools |

---

_End of remaining-work tracker. Full historical plan removed after multi-agent completion audit 2026-07-23._
