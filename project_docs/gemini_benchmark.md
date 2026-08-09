# Gemini Benchmark — P3 (8 cases A–H)

`codebase/agent_tools/gemini_mode_benchmark.py` now has a dedicated P3 mode
(`GEMINI_P3=true`) that runs the 8 PlanFixes2 §P3 scenarios A–H and prints all
required metrics per case. Offline (no `GEMINI_API_KEY`) it uses deterministic
mock stanzas; live it drives the real Gemini agent loop.

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
- **false_success** — `_detect_false_success()`: 1 when a tool failed but the final answer lacks failure wording (PlanFixes2 P0 #1).

All sourced from `orch.profile_records` (set by `agent_core/context_budget.py`)
and the agent event stream.

## 4. Related modes

Same script, different env toggles:

```bash
# Original 3-mode A/B/C aggregate (stateless vs stateful) over the 5-task set:
conda run -n myenv python codebase/agent_tools/gemini_mode_benchmark.py

# Single 3-step per-call diagnostic (PlanFixes §3 decision experiment)
GEMINI_DIAGNOSE=true conda run -n myenv python codebase/agent_tools/gemini_mode_benchmark.py
```