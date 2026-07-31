## 1. LOC reduction

**A. Table-driven registration (`__init__.py`, 457 lines → ~200).**
57 `reg.register(...)` calls with hand-written `description=` + `params={...}` dicts. `registry.py` already has **`reg.simple()`** and **`derive_schema()`** that are barely used (only `glob_search`). Convert each `_register_*` to a declarative spec list:
```python
_FILE_SPECS = [
  ("read_file", read_file, CAT_FILE, "Read file (returns line-numbered output…)", {"path": str_p(..., req=True), …}),
  …
]
for name, fn, cat, desc, params in _FILE_SPECS:
    reg.set_default_category(cat); reg.register(name, tc(fn), description=desc, params=params)
```
This also kills the duplicated `reg.set_default_category(CAT_X)` (9 occurrences). Most params dicts collapse to `derive_schema(fn, {overrides})`. Biggest single LOC win in the repo.

## 2. Token consumption for future agents

**A. Shrink the per-turn schema payload (highest recurring cost).**
`get_schemas()` serializes all 58 tool descriptions into every LLM call. The loop already filters by active pack (`engine.py:146`), but the CLI path (`run_agent_turn` → `tool_categories=None` → `resolve_active_tool_packs()`) only gets `['file']` by default. Ensure `stepper.py`/CLI always pass the resolved pack list, and **trim the longest descriptions** in `__init__.py` (the token-optimization task trimmed prompt fragments but not tool descriptions). Every 100 chars removed from tool descriptions saves ~100 tokens × turns per session.

=================================

## Finalized Plan: `tool_mode` in config.json

Decisions locked in: single `tool_mode` enum (`all` | `read_only` | `shell_only`), MCP untouched, read_only = exactly 4 tools.

### 1. `config.json`
Add under the existing settings:
```json
"tool_mode": "all"
```

### 2. `agent_core/config.py`
- Add module constant:
  ```python
  TOOL_MODES = {
      "read_only": {"read_file", "list_files", "glob_search", "grep_search"},
      "shell_only": {"execute_command"},
  }
  ```
- `resolve_tool_mode() -> str` → `_CONFIG.get("tool_mode", "all")`
- `resolve_active_tool_names() -> set[str]` → the preset set for the mode, or empty set for `all` (empty = no name filtering)

### 3. `agent_core/tools/registry.py`
- `get_tools(categories=None, names=None)` — when `names` (a set) is non-empty, keep only those tool names.
- `get_schemas(provider_name=None, categories=None, names=None)` — same filter applied to the schema list.
- `to_mcp_tools` untouched (MCP unchanged).

### 4. `agent_core/server/__init__.py`
```python
ACTIVE_TOOLS_DICT = registry.get_tools(
    categories=resolve_active_tool_packs(),
    names=resolve_active_tool_names() or None,
)
```
This is the single enforcement point for execution — it flows to the audit-wrapped `_tools` (ws_handler.py:214) and the frontend tool list (routes.py:23). With current config (`file: true`, others off):
- `all` → 9 file tools
- `read_only` → {read_file, list_files, glob_search, grep_search}
- `shell_only` → {execute_command}

### 5. `agent_core/loop/engine.py`
At line 146, filter the schemas the model sees:
```python
_cached_schemas = registry.get_schemas(
    provider_name=provider,
    categories=tool_categories,
    names=resolve_active_tool_names() or None,
)
```
(import `resolve_active_tool_names` alongside the existing `resolve_active_tool_packs`)

### 6. `agent_core/planning/local_planner.py`
Same `names=` filter in `generate_local` (line 81) for defense-in-depth on local-model steps.

### Enforcement (already verified in code)
- **Schemas**: model is only *shown* the allowlisted tools.
- **Execution**: stepper.py:128 (`invalid_tool` corrective) and executor.py:122 (`_tools[tc.name]` → fail-closed) reject any disallowed call even if the model hallucinates one.

### Not in scope / noted
- MCP server tool list unchanged (per your choice).
- `allowed_commands` still gates `execute_command`; `python`/`pytest` in that list can write files, so `shell_only` is not a hard sandbox — tightening `allowed_commands` is a separate knob.

### Verification (after implementation, with your OK)
- Smoke test all three modes: assert `ACTIVE_TOOLS_DICT` keys and `get_schemas` names per mode.
- Mock-pipeline test: in `read_only` mode, a scenario calling `edit_file` yields the "Unknown tool" corrective listing the 4 valid tools.
- Run `pytest tests/test_tool_pluggability.py tests/test_file_ops_pipeline.py` to confirm no regression (default `tool_mode: all`).


============================

## Execution/token optimization

- **`tool_anatomy` tool** (registration→file:line, category, mcp_expose, mock scenario, test, prompt-fragment refs) — removes the repeated manual tracing.
- **Post-edit import/syntax check hook** after `edit_file` on `.py` files — catches regressions before pytest, cheaper than a full test run.
- **Mode-aware prompt trimming** for read_only/shell_only (don't load fragments for unavailable tools).
