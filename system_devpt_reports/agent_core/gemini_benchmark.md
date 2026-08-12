# Gemini Benchmark — P3 (8 cases A–H)

`codebase/agent_tools/gemini_mode_benchmark.py` now has a dedicated P3 mode
(`GEMINI_P3=true`) that runs the 8 PlanFixes2 §P3 scenarios A–H and prints all
required metrics per case. Offline (no `GEMINI_API_KEY`) it uses deterministic
mock stanzas; live it drives the real Gemini agent loop.

Since PlanFixes3, the benchmark also tracks two cross-cutting guarantees:

- **Unit labeling (Phase 1):** every token number is explicitly marked as
  `tiktoken(cl100k) estimate` or `provider-measured`. The two are different
  tokenizers and must never be summed (the old "899 vs 1,288" confusion).
- **False-success is ENFORCED, not merely detected (Phase 2):** the loop's
  honesty gate (`agent_core/loop/stepper.py`, `FAILURE_SIGNALS`) pushes one
  corrective round when a tool failed but the final answer claims success with
  no failure wording. The benchmark's detector imports the same
  `FAILURE_SIGNALS` so the two can never drift.

## The 8 scenarios

```text
A. find existing file
B. read file
C. create directory
D. write file
E. edit file
F. execute command
G. failed tool
H. nonexistent file
```

Metrics recorded per scenario:

```text
initial_prompt_tokens
tool_schema_tokens
system_tokens
continuation_tokens
output_tokens
total
tool_failures
false_success
```

## 1. Offline run (no API key)

```bash
cd /home/manigupt/Hello/Agentic_Unit_PIE
conda run -n myenv GEMINI_P3=true python codebase/agent_tools/gemini_mode_benchmark.py
```

Each case runs the real agent loop with deterministic mock stanzas that issue
the same tool calls as live. `G` (failed tool) and `H` (nonexistent file)
deliberately end in a failed tool so `tool_failures` / `false_success` are
exercised. `system_tokens` is measured with the deployed system prompt (via
`load_system_prompt(resolve_active_tool_packs(), ..., SYSTEM_PROMPT_CORE_ONLY)`).

The mock stanzas for `G`/`H` are now three steps: a failing tool call, a
dishonest success final (which the loop's honesty gate corrects once), then an
honest final that names the failure. The acceptance target is therefore
`failures=1 false_success=0 calls=3` instead of a detected-but-unprevented
`false_success=1`. Golden offline result (PlanFixes3 #6):

```text
A  find existing file   failures=0 false_success=0 calls=2
B  read file            failures=0 false_success=0 calls=2
C  create directory     failures=0 false_success=0 calls=2
D  write file           failures=1 false_success=1 calls=3   (mock overwrites a non-existent file)
E  edit file            failures=0 false_success=0 calls=2
F  execute command      failures=0 false_success=0 calls=2
G  failed tool          failures=1 false_success=0 calls=3
H  nonexistent file     failures=1 false_success=0 calls=3
```

### Phase 4 — deterministic factory (0-LLM fast path)

`agent_core/tools/tool_groups.py try_factory()` maps an unambiguous
single-intent request to ONE deterministic tool call, executed by the loop
(`engine.py`) before any LLM call, gated by `config.json factories_enabled`
(default true):

- `find <name>` → `glob_search("**/<name>")`
- `read <path>` → `Read`
- `list <dir>` → `Read` (dir path returns its listing)
- `check <path> exists` → `check_path_exists`
- `create dir <path>` → `execute_command("mkdir -p <path>")` (allowlisted)

Ambiguous input returns None → normal Gemini path. If the deterministic tool
fails (e.g. missing dir), the loop records the failure and falls back to the
LLM so recovery stays honest. Golden offline result (PlanFixes2 #8/#10):

```text
F1  find file          failures=0 false_success=0 calls=0  total=0 tokens
F2  read file          failures=0 false_success=0 calls=0  total=0 tokens
F3  list dir           failures=0 false_success=0 calls=0  total=0 tokens
F4  check exists       failures=0 false_success=0 calls=0  total=0 tokens
F5  mkdir              failures=0 false_success=0 calls=0  total=0 tokens
```

`calls=0 total=0` = deterministic tool execution with no LLM round-trip
whatsoever (PlanFixes2 #9 target: "find with exact path" → 0 LLM calls).
Disable with `"factories_enabled": false`.

## 2. Live run (real model)

```bash
GEMINI_API_KEY=sk-... conda run -n myenv GEMINI_P3=true python codebase/agent_tools/gemini_mode_benchmark.py
```

## 3. What each metric means

- **initial_prompt_tokens** — first LLM call's prompt estimate (`total_tokens` of `profile_records[0]`).
- **tool_schema_tokens** — sum of routed tool-schema token estimates across calls.
- **system_tokens** — sum of system-prompt tokens across calls (constant per call).
- **continuation_tokens** — sum of `history_tokens + tool_result_tokens` (context resent on chained calls).
- **output_tokens** — sum of provider completion tokens.
- **total** — sum of `total_tokens + output_tokens` across calls.
- **tool_failures** — count of `tool_result` events with `ok == False`, plus `error`/`parse_error` events.
- **false_success** — `_detect_false_success()` using `agent_core.loop.stepper.FAILURE_SIGNALS`: 1 when a tool failed but the final answer lacks failure wording. In live/offline runs the loop's honesty gate already corrects that final once, so the reported value is what survived the gate.

All sourced from `orch.profile_records` (set by `agent_core/context_budget.py`)
and the agent event stream.

### Units (Phase 1 — never mix these)

- `initial_prompt_tokens`, `tool_schema_tokens`, `system_tokens`,
  `continuation_tokens` are **tiktoken(cl100k) estimates** of the wire payload.
- `output_tokens` (and any `fresh`/`cached` in the `GEMINI_DIAGNOSE` per-call
  logs) are **provider-measured** (Gemini's own tokenizer).
- `agent_core/context_budget.py` keeps the provider's raw count in a separate
  `provider_prompt_tokens` field and labels every `format_budget` /
  `format_wire_vs_actual` row `(est)` vs `(measured)`, so an estimate/measure
  gap (e.g. 899 vs 1,288) is expected and is not a bug to optimize away.

## 4. Related modes

Same script, different env toggles:

```bash
# Original 3-mode A/B/C aggregate (stateless vs stateful) over the 5-task set:
conda run -n myenv python codebase/agent_tools/gemini_mode_benchmark.py

# Single 3-step per-call diagnostic (PlanFixes §3 decision experiment)
GEMINI_DIAGNOSE=true conda run -n myenv python codebase/agent_tools/gemini_mode_benchmark.py

# Deployed system-prompt truth report (PlanFixes3 #1) — resolves the
# "899 vs 1,288" estimate-vs-measure ambiguity:
conda run -n myenv python codebase/agent_tools/system_prompt_report.py
```

The prompt report uses the exact runtime load path
(`load_system_prompt(active_packs=resolve_active_tool_packs(),
mode=resolve_active_tool_mode(), core_only=SYSTEM_PROMPT_CORE_ONLY)`) and prints
chars, tiktoken(cl100k) estimate, and the core-only headroom variant. Current
values: **5,223 chars / 1,288 tokens** deployed; core-only = **831 tokens**.

## Run it

```bash
# offline
conda run -n myenv GEMINI_P3=true python codebase/agent_tools/gemini_mode_benchmark.py
# live
GEMINI_API_KEY=... conda run -n myenv GEMINI_P3=true python codebase/agent_tools/gemini_mode_benchmark.py
# prompt token check (deployed prompt via runtime path)
conda run -n myenv python codebase/agent_tools/system_prompt_report.py
```