# PlanFixes2 — Status

## Implemented

### P1 — Token reduction

**5. System prompt cut — DONE (2,005 → 899 tokens / 3,665 bytes)**
- Terse LLM-optimized rewrites of all fragments reachable in default config:
  `base_persona.md`, `efficiency_rules.md`, `implementation_guardrails.md`,
  `file_ops_workflow.md`, `response_contract.md`, `meta_playbook.md`.
- No grammar padding; every substantive rule retained (paths, allowed cmds,
  todo lifecycle, honesty contract, `ask_user_question`).
- Required behavior change: `get_workspace_info` guidance moved from
  `base_persona.md` → `meta_playbook.md` (meta pack).
- Fixed latent placeholder bug: `{AGENTS_MD}` was only replaced in non-core
  mode (`agent_core/prompts.py`) — left a literal tag in CORE prompts. Now
  always replaced.
- `system_prompt_core_only` stays `false` (CORE=3 fragments drops guardrails;
  rewrite met the target already).

**6. Minimal tool routing (`agent_core/tools/tool_groups.py`).**
- Split the old broad search group into intent-scoped groups:
  - list → `{list_files, read_file}`
  - find/locate/glob → `{glob_search, list_files, read_file}`
  - grep/usage → `{grep_search, read_file}`
  - read → `{read_file, list_files}`; write/exec/check unchanged.
- Fibonacci request schema payload: **2,587 → 1,057 bytes**.
- Fixed substring bug: `check if .../tooltest exists` matched the word `test`
  in `_EXEC_TOKENS` and routed to `execute_command`. `_has()` now uses
  word-boundary regex — exists checks route to `check_path_exists`.

**7. Compressed tool schemas (`agent_core/tools/__init__.py` `_FILE_SPECS`).**
- Descriptions/catala→ telegn-expand, no repeated prose; editors such as
  `read_file` 1,026→745, `edit_file` 1,283→1,037, `grep_search` 709→600,
  `list_files` 449→312, `write_to_file` 577→503, `glob_search` 403→319,
  `check_path_exists` 390→305, `execute_command` 290→270.

### P3 — Benchmark (`agent_tools/gemini_mode_benchmark.py`)

**Added `GEMINI_P3=true` mode** — runs the 8 cases A–H (`_P3_CASES`) and records
per scenario:

```text
initial_prompt_tokens  tool_schema_tokens  system_tokens
continuation_tokens    output_tokens       total
tool_failures          false_success
```

- Offline: deterministic mock stanzas per case (no API key). Cause paths,
  clean result via `total_tokens + output_tokens`.
- `system_tokens` measured with deployed prompt
  (`load_system_prompt(resolve_active_tool_packs(), ..., SYSTEM_PROMPT_CORE_ONLY)`).
- `false_success` = `_detect_false_success()` (PlanFixes2 P0 #1): `1` when a
  tool failed but the final answer lacks failure wording (deterministic).

**Latent bug fixed:** `agent_core/loop/engine.py:367` referenced
`step_usage` before defining it → `NameError` on any tool-call step. Now set
from the current LLM call's usage.

### Offline P3 result (mock)

```text
A find existing file    failures=0 false_success=0
B read file             failures=0 false_success=0
C create directory      failures=0 false_success=0
D write file            failures=0 false_success=0
E edit file             failures=0 false_success=0
F execute command       failures=0 false_success=0
G failed tool           failures=1 false_success=1
H nonexistent file      failures=1 false_success=1
```

G/H drive a real failing tool call so failure + false-success paths validate.

## Still open

- **P0-3 `make_directory`** — not added (P0-4 skipped; no write-group
  expansion).
- **P2 factory task preprocessing** (find/list/exists/create/delete without an
  LLM decision) — not started.
- **P3 live run** — needs `GEMINI_API_KEY`.

## Run it

```bash
# offline
conda run -n myenv GEMINI_P3=true python codebase/agent_tools/gemini_mode_benchmark.py
# live
GEMINI_API_KEY=... conda run -n myenv GEMINI_P3=true python codebase/agent_tools/gemini_mode_benchmark.py
# prompt token check
conda run -n myenv python -c "import sys,tiktoken;sys.path.insert(0,'codebase');from agent_core.prompts import load_system_prompt;print(len(tiktoken.get_encoding('cl100k_base').encode(load_system_prompt())))"
```

Docs: `project_docs/gemini_benchmark.md`.