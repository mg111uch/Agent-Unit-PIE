# PlanFixes3 — status after Phase 1–4 implementation

Original analysis (token accounting, false-success, tool routing, mkdir path,
recovery, history) with the remaining issues kept. Items marked ✅ are
implemented and removed from active scope; their closing notes live in
`project_docs/gemini_benchmark.md` and the code.

## Resolution status (PlanFixes3's original 9 issues)

| # | Issue                                                      | Status | Resolution |
|---|-----------------------------------------------------------|--------|------------|
| 1 | First-call token accounting inconsistent (899 vs 1,288)    | ✅ done | Phase 1: `context_budget.provider_prompt_tokens` (est vs measured labels), `system_prompt_report.py` (deployed = 5,223 ch / 1,288 tok) |
| 2 | System prompt too large (~1,288 → target 700–900)          | open   | Phase 5 (PlanFixes2). Not started. |
| 3 | Routing makes model walk dirs; needs deterministic preprocess | ✅ done | Phase 4: `try_factory` → 0 LLM calls for find/read/list/check |
| 4 | mkdir path awkward; `create_directory` tool                | ✅ done | Dedicated tool **dropped by decision**; factory routes create-dir → allowlisted `execute_command("mkdir -p …")` |
| 5 | Failed-tool recovery wasting an LLM call                   | closed | Deterministic recovery (P3-7) **dropped by decision**; factory failure falls back to the LLM honestly instead |
| 6 | False-success detected, not prevented                      | ✅ done | Phase 2: bounded honesty gate in `stepper.py` (`FAILURE_SIGNALS`); G/H → `failures=1 false_success=0 calls=3` |
| 7 | Irrelevant completed-turn history in new turns             | open   | P2. History RELEVANT/IRRELEVANT classification. Not started. |
| 8 | Tool schemas (~237 tok) feature-complete                   | ✅ done | Schema compression landed; stop optimizing further |
| 9 | Stateful Gemini working                                    | ✅ done | Keep stateful chains, no transcript replay |

## Remaining open work

### #2 — Reduce the deployed system prompt (P1, Phase 5)
Deployed prompt is 5,223 chars / **1,288 tokens**; core-only variant = 831.
Target → 700–900 wire tokens. Options (only after Phase 1 truth is in place):
- enable `system_prompt_core_only` or trim it,
- trim `response_contract.md` (largest core fragment, was 1,025 chars),
- trim AGENTS.md/workspace injection.
Do not touch fragments without re-running `system_prompt_report.py`.

### #5 — Deterministic recovery after predictable tool failures (closed)
Was: "run_shell_command → failed → create_directory". Recovery map + step-1
deterministic substitution (P3-7) was **dropped by the user** — the mkdir need
is already met by the factory (`mkdir -p`), and factory tool failures now fall
back to the LLM (honest recovery). Re-open only if a predictable
command→tool failure resurfaces with measurable cost.

### #7 — Remove irrelevant completed-turn history (P2)
New-turn messages currently include prior completed tasks. Classify history as
RELEVANT / IRRELEVANT and drop completed, unrelated turns from the Gemini
payload. Current 46-token history is cheap → deferred.

## Architecture (unchanged guidance)

```text
                    USER REQUEST
                         │
                         ▼
               ┌─────────────────┐
               │ Task Classifier  │
               │ deterministic    │
               └────────┬────────┘
                         │
          ┌─────────────┴─────────────┐
          │                           │
   obvious filesystem             complex task
          │                           │
          ▼                           ▼
   factory operation             Gemini
          │                           │
          │                    minimal tool set
          │                           │
          └──────────────┬────────────┘
                         ▼
                    TOOL EXECUTION
                         │
                 ┌───────┴───────┐
                 │               │
               success         failure
                 │               │
                 ▼               ▼
               final       |  guarded fallback:
                           |  LLM recovers honestly
                           |  (factory failure → same tool path,
                           |   saw_tool_failure set, honesty gate applies)
```

Key principle (unchanged):
> **Don't use the LLM to solve problems that the orchestrator can solve
> deterministically.** Phases 1–4 delivered 0-LLM fast paths and honest
> failure enforcement; the next step (Phase 6, PlanRecommend3) adds a local
> router as the second tier for **ambiguous** actions that `try_factory`
> declines — keeping the cloud model for reasoning only.

# PlanRecommend3 — local tool router (FunctionGemma) — recommendation + status

Recommendation: **move the entire tool-control plane local; reserve the cloud
model exclusively for reasoning.** FunctionGemma (or any small Ollama model) is
a local **tool/router model**, not a general agent. It only ever maps
plain-language to ONE canonical action from a tiny fixed vocabulary — never
general reasoning. It is a fallback classifier, not the first line of defence.

## Architecture

```text
                 USER
                   │
                   ▼
          ┌──────────────────┐
          │ Deterministic    │   tier 1 (try_factory) — zero LLM calls
          │ task recognizer  │
          └────────┬─────────┘
                   │
          obvious operation?
             /           \
           YES            NO
            │              │
            ▼              ▼
       DIRECT TOOL     LOCAL ROUTER     ── tier 2 (this plan)
            │              │              FunctionGemma → canonical action
            │              ▼              Validate/policy BEFORE execution
            │         tool intent         cmd→allowlist, payload caps, IDs
            │              │
            │              ▼
            └──────┬───────┘
                   ▼
          Deterministic executor
                   │
                   ▼
              tool result
                   │
                   ▼
             Cloud LLM only        ── tier 3: reasoning/final only
             when necessary
```

Core separation:

```text
Cloud model      -> Reasoning, planning, complex interpretation, final synthesis
Local model      -> Tool classification, argument extraction, tool routing
Deterministic code -> Validation, permissions, filesystem, git, shell, execution
```

Rule (original): **don't make Cloud → FunctionGemma → Cloud ping-pong.** The
cloud issues an ACTION/activity, the local router converts it, deterministic
code runs a batch of operations, and the cloud returns only when the result
needs reasoning.

## Design constraints (kept)

* FunctionGemma output = fixed action ID, tiny JSON, `temperature=0`, max ~50–100 tokens → fast CPU inference (i3 concern).
* Cloud model never sees the JSON tool schemas; the catalog lives locally.
* FunctionGemma is **not trusted to execute anything**: intent → validator → policy → executor. e.g. `execute_command("rm -rf ...")` rejected by the command allowlist before execution.
* Simple requests ("create directory X", "list files in foo") bypass models entirely via deterministic parsing.

## Done (Phase 6, tier 2 implemented)

* `codebase/agent_core/planning/local_router.py` — `LocalRouter` with:
  * fixed action-ID vocabulary `ACTION_IDS` (9 IDs: read, list, write, edit, execute, glob, grep, exists, workspace info),
  * tiny plain-text router prompt (no tool schemas) → valid JSON only,
  * strict `_parse_action` (markdown fences stripped, single JSON object, unknown IDs → None),
  * `_policy` gate before execution: `execute_command` checked against `ALLOWED_COMMANDS` allowlist, `Write` content capped (4,000 chars), required args non-empty.
  * pluggable backend: `OllamaProvider` (live) via `build_local_router()`; `deterministic_router()` stub for the offline benchmark / smoke test.
* `codebase/agent_core/config.py` — `LOCAL_ROUTER_ENABLED / MODEL / ENDPOINT / TIMEOUT` (config.json `local_router` block; default off, no model needed to ship).
* `codebase/agent_core/loop/engine.py` — tier-2 wiring: engine tries `try_factory` on step 1; on None it asks the local router (`_get_local_router()` singleton), and only on a validated action executes the single tool call with zero cloud calls. Router disabled → identical prior behavior (ambiguous requests go straight to cloud).
* Smoke test: `python -m agent_core.planning.local_router` covers routing, allowlist rejection, unknown-ID and empty-input fallbacks.

## Not done / next

* Live Ollama tuning: pick a real model id, keep it resident (`OLLAMA_KEEP_ALIVE`), measure TTFT/latency/CPU on the i3.
* Benchmark the three approaches from the original plan (A cloud tool-calling, B cloud→FunctionGemma, C deterministic→FunctionGemma fallback). Predict C wins.
* Wire tier 2 as an execution layer for batched actions issued by a cloudy reasoning step (cloud → N actions → local router → deterministic executor), instead of step-at-a-time routing only.

## Key KPIs to measure (benchmark)

TTFT, total latency, CPU/RAM, cloud input/output tokens, router inference time, tool execution time, success rate.