## Analysis

### Most token-heavy steps

1. **Reading files to understand structure** (~40% of read tokens) — I read `stepper.py` in full (350+ lines) 3+ times: once to understand the two branches, once before editing each branch, once to verify. Same for `_helpers.py`, `session_state.py`, `providers_setup.py`, `engine.py`.

2. **Multi-round fix cycles** (~20%) — e.g. I wrote `_finish_tool_events` with `local_planner` inside, then had to fix it when I realized multi-tool batches call it per-tool. Each round requires re-reading, editing, verifying.

3. **Verification through import tests** (~10%) — running `py_compile` + `python -c "from ... import ..."` for every changed file.

4. **Pattern searching** (~10%) — grepping for `cancel_event`, `COMPACTION_TRIGGER_CHARS`, `local_planner` across the codebase.

### 4 Novel tool recommendations (no duplicates of existing tools)

**1. `structmap` (highest impact)**
Returns a compact 1-line-per-symbol structural index of Python files: function sigs, class methods, top-level assignments — *without* reading implementation bodies. For `stepper.py` this would return ~40 lines vs 350+ lines, saving ~85% of read tokens on first access.
```
dispatch_step(cancel_event, conv_id, parsed, ...) -> Generator @ L38
  ToolCallData, ToolResult      # imports
  NonStreamingStepResult        # imports
  registry, _debug_dump, ...    # local imports inside function
```
*Not duplicate of `read`* — read returns raw bytes; this returns parsed AST structure.

**2. `touchmap`**
Depends-on / depended-by graph for files. E.g. `touchmap stepper.py` would show: imports `_helpers`, imports `config`, imported-by `loop.py`. A change in `_helpers.py` → 1 downstream file (`stepper.py`). This eliminates the grep/search step entirely when tracing change impact.
*Not duplicate of `grep`* — grep searches content; this resolves the import graph.

**3. `surgery` (token-efficient multi-edit)**
Batch multiple targeted edits across files in a single call with automatic validation. Instead of:
```
1. Read file A → edit → py_compile
2. Read file B → edit → py_compile
3. Import test both
```
`surgery` would accept `[{file, old, new}, {file, old, new}, ...]`, apply atomically, validate all compiles, and report failures per edit. Saves ~60% of the fix-round tokens.
*Not duplicate of `edit`* — edit is single-file, single-hunk; this is a multi-hunk transaction.

**4. `changeprint`**
After a session's edits, produce a compact relational summary: which files changed, what kind of changes (new function, refactored block, deleted code), and a before/after token count. Useful for both the current agent and any future agent picking up the work.
*Not duplicate of `git diff`* — git diff shows raw lines; this shows semantic intent and token impact.

### How to make future agents faster on this codebase

**For the highest ROI in this repo specifically**, create a **stale index** (a file like `codebase.structmap.json`) using `structmap` output after every commit. Agents check it first before reading files. A structmap for the entire `agent_core/` directory would be ~2K tokens vs the ~15K+ tokens I spent reading files in this session.