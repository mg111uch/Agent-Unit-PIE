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
`get_schemas()` serializes all 58 tool descriptions into every LLM call. The loop already filters by active pack (`engine.py:146`), but the CLI path (`run_agent_turn` → `tool_categories=None` → `resolve_active_tool_packs()`) only gets `['file']` by default. Ensure `stepper.py`/CLI always pass the resolved pack list.

## Execution/token optimization

- **`tool_anatomy` tool** (registration→file:line, category, mcp_expose, mock scenario, test, prompt-fragment refs) — removes the repeated manual tracing.
- **Post-edit import/syntax check hook** after `edit_file` on `.py` files — catches regressions before pytest, cheaper than a full test run.
- **Mode-aware prompt trimming** for read_only/shell_only (don't load fragments for unavailable tools).
- **Notes / out of scope:** base_persona.md and response_contract.md still mention get_workspace_info/read_file/check_path_exists, which are unavailable in shell_only — cosmetic, out of scope unless you want them tagged later.
implementation_guardrails.md items 5/10/11 reference todo/edit_file — also stale in read_only; left as-is per your ask.
=================================
