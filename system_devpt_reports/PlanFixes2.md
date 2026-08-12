# Consolidated development report

## Context

The original token-bloat problem is solved: tool schemas were compressed to
~237 tokens, first-call accounting is consistent, and the system prompt was
measured precisely. The three-tier routing architecture is implemented. The
remaining work is **benchmark-driven**, not another large refactor.

At the last review, the local FunctionGemma tier was implemented but not
reliable enough to be the default router (misclassification, ~55s CPU
inference). The response was a pivot: **tier 2 now uses a small cloud model by
default** (config-switchable to a local model), giving near-instant, accurate
routing instead of fine-tuning a slow local model.

## Resolution status (original issues)

| # | Issue | Status | Resolution |
|---|-------|--------|------------|
| 1 | First-call token accounting inconsistent (899 vs 1,288) | ✅ done | `context_budget.provider_prompt_tokens` (est vs measured labels); `system_prompt_report.py` (deployed = 5,223 ch / 1,288 tok) |
| 2 | System prompt too large (~1,288 → target 700–900) | ⏳ open | Core-only variant is 831 tokens but is **not enabled** (`system_prompt_core_only: false`) |
| 3 | Routing makes model walk dirs; needs deterministic preprocess | ✅ done | Deterministic factory → 0 LLM calls for find/read/list/check |
| 4 | mkdir path awkward; `create_directory` tool | ✅ done | Dedicated tool **dropped by decision**; factory routes create-dir → allowlisted `execute_command("mkdir -p …")` |
| 5 | Failed-tool recovery wasting an LLM call | ⏸ closed | Deterministic recovery map **dropped by decision**; factory failure falls back to the LLM honestly |
| 6 | False-success detected, not prevented | ✅ done | Bounded honesty gate in the loop (`FAILURE_SIGNALS`); failures counted, false-success = 0 |
| 7 | Irrelevant completed-turn history in new turns | ✅ done | `history_relevance` filter (FixesIssues.md): `filter_irrelevant_history` in `loop/session_state.py` (turn segmentation, recency guard, substring/path overlap); wired before `compact()` in `context_manager.build_active_context` with a dropped-turns note; enabled in config.json (`keep_recent=1`, `min_overlap=1`) |
| 8 | Tool schemas feature-complete | ✅ done | Schema compression landed; stop optimizing further |
| 9 | Stateful Gemini working | ✅ done | Keep stateful chains, no transcript replay |

## Decisions made and kept

- **No dedicated `create_directory` tool.** The factory handles it via an
  allowlisted `mkdir -p`, so obvious requests never reach a model.
- **No deterministic failure-recovery map.** Predictable tool failures are
  handled honestly: the factory's failure falls back to the LLM rather than
  guessing a follow-up.
- **No more tool-schema optimization.** Schemas are feature-complete.
- **Tier 2 pivoted from a local model to a small cloud model.** FunctionGemma
  (270M) was not production-accurate and was too slow on CPU. Tier 2's backend
  is now config-driven (`gemini` / `openrouter` for cloud, `ollama` for local);
  the local path is retained as an offline option, and the config key was
  renamed `local_router` → `tier2_model_router` to reflect this.

## Implementation ledger

| Phase | Work | Status |
|-------|------|--------|
| 1 | First-call token accounting + `system_prompt_report.py` | ✅ done |
| 2 | False-success honesty gate | ✅ done |
| 4 | Deterministic factory (`try_factory`) — 0-LLM fast paths | ✅ done |
| 6 | Tier-2 model router — fixed 9-action vocabulary, policy gate, pluggable backend | ✅ done (evolved: cloud backend default, 60s timeout) |
| — | LocalPlanner (legacy local execution loop) removed — superseded by the factory + router | ✅ done |
| 5 | System prompt reduction (enable core-only) | ⏳ open |
| 7 | Irrelevant-history classification (FixesIssues.md) | ✅ done | `filter_irrelevant_history` drops zero-overlap completed turns; conservative defaults keep the current turn + newest `keep_recent` |

## Remaining work

### System prompt — enable & measure (originally #2)
`system_prompt_core_only: false` today; the 831-token core-only variant is
built but untested. Enable it and measure for behavioral regression before
trimming further. Do not touch prompt fragments without re-running
`system_prompt_report.py`.

### Tier-2 model quality
The fine-tune-FunctionGemma path (build a 50–100-example-per-action dataset,
then SFT) was superseded by the cloud small-model pivot. Revisit only if a
capable local model is needed offline. A routing benchmark decides whether the
cloud tier-2 model is accurate enough to trust at scale.

### Three-way benchmark (the decision point)
Compare:
- **A** — cloud tool-calling only (no router),
- **B** — cloud → tier-2 router → executor,
- **C** — deterministic factory → tier-2 router fallback → executor.

Predict C wins; it is only meaningful once the tier-2 model is accurate. Use
20–50 tasks across read/list/search/grep/write/edit/create/git/shell,
nonexistent paths, invalid requests, and ambiguous requests. Measure: cloud
input/output tokens, cloud calls, router calls, latency (p50/p95), CPU/RAM,
accuracy, tool failures, false successes.

### Batch action plane
Eliminate cloud → router → cloud ping-pong. The cloud reasoning step should
produce a compact plan of N actions; the local/router layer executes the whole
batch, then the cloud synthesizes only when the result needs reasoning.

### Explicit action intent + confidence
Formalize the internal action object (action ID, arguments, source) and add a
confidence signal combined with structural validation (valid ID, required args
present, policy allows). Today only the policy gate exists.

### Success metric
Prefer an efficiency score (correctness × completion / tokens + latency) or a
dashboard over raw token-minimization. Tracked goals: deterministic simple
tasks ≥90%, router accuracy ≥98%, false-success = 0, no cloud schemas on tier 2,
no cloud calls for simple tasks, router p95 < 1s, cloud tokens minimized.

## Strategic principle

The architecture is **progressive intelligence**: the deterministic fast path
handles everything it can, the cheap router handles the rest of the
single-operation requests, and the cloud reasoning model is invoked only when a
request genuinely needs it. The next milestone is proving this three-tier
system is faster and at least as reliable as the original cloud-tool-calling
architecture — through the benchmark above, not more token optimization.

For how a request moves through the tiers and what each tier sees, see
`../project_docs/model_routing.md`.
