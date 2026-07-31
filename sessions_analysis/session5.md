### Most token-heavy steps

1. **Reading files to understand structure** (~40% of read tokens) — I read `stepper.py` in full (350+ lines) 3+ times: once to understand the two branches, once before editing each branch, once to verify. Same for `_helpers.py`, `session_state.py`, `providers_setup.py`, `engine.py`.

2. **Multi-round fix cycles** (~20%) — e.g. I wrote `_finish_tool_events` with `local_planner` inside, then had to fix it when I realized multi-tool batches call it per-tool. Each round requires re-reading, editing, verifying.

3. **Verification through import tests** (~10%) — running `py_compile` + `python -c "from ... import ..."` for every changed file.

4. **Pattern searching** (~10%) — grepping for `cancel_event`, `COMPACTION_TRIGGER_CHARS`, `local_planner` across the codebase.
