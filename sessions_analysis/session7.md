Good question — let me analyze this session honestly and give concrete, non-duplicate recommendations.

## 1. Tools/hooks that would have helped this session

**`module_profile` (import-time profiler)** — This session burned ~6 bash calls re-measuring `import agent_core.tools` with `time.perf_counter()` and `-X importtime`, then post-processing the sort. A tool that runs a target module in a subprocess and returns the top-N slow sub-imports (self/cumulative ms) plus an optional before/after delta would collapse all of that into one call. *Not a duplicate*: `tool_stats`/`file_stats` track tool-call usage, not Python import cost; nothing in `code_rag` measures runtime.

**`file_skeleton` (AST structure navigator)** — The biggest token sink this session was reading full files (`__init__.py` 463 lines read ~3×, `registry.py`, `mcp_server.py`). A one-pass AST parse returning imports, classes/methods and top-level defs with signature + line ranges (and "eager vs lazy" flags on imports) would have let me locate `_register_all()`/`_register_debate_tools` without full reads. *Not a duplicate*: `file_api`/`symbols_by_file` are atlas-dependent (index can be stale/disabled) and omit imports; `file_skeleton` is a cheap atlas-free fallback that runs in ~10% of the tokens of a full read.

**`who_imports` (import/reference index)** — I ran greps for `from agent_core.tools import`, `KERNEL_AVAILABLE`, `TOOLS`, `execute_tool_calls` to find consumers before touching registration. A cached AST import-scan that answers "which files import X, eagerly or lazily" (and auto-updates on edit) makes consumer-discovery one call. *Not a duplicate*: `grep_search` is raw regex (false positives from comments/strings); `get_callers_callees`/`find_impact` index function call edges, not module imports.

**`verify_refactor` (post-edit hook)** — After each edit I manually did: import the module → check `tool_count`/`tool_count` correctness → test aliases. A hook that auto-runs `py_compile` on edited files + imports the parent module + runs only the referenced test file (not full pytest discovery like `run_tests`) would give fast, scoped feedback with small output.

**`file_facts` (pre-chat hook / file-keyed decision log)** — I re-derived facts that previous sessions already established (`tool_count`=58, `run_agent_turn` used by `auto_research.py:11,60`, `read_file` cache format, `_register_all` hot-reload usage). Persisting "verified facts" keyed by file (SQLite, per AGENTS single-persistence rule) and injecting only the facts for files the new task will touch — via a pre-chat hook — prevents re-verification. *Not a duplicate*: `kernel_store_context`/`kernel_retrieve` is fuzzy semantic memory and disabled by default (kernel pack off); `todo_read`/`checkpoint_info` track tasks and undo points, not verified facts.

## 2. Faster, precise re-access for the same files

- The **`file_facts` store** (above) + pre-chat injection is the direct answer: an agent starts with the session's verified conclusions instead of re-reading everything.
- Keep the **`read_file` mtime cache** (already done) and make `file_skeleton` the default first touch instead of full reads.
- **Use `subagent_task`/explore for discovery** — delegate "find all consumers of X" to a sub-agent whose context is discarded, so the main loop never pays the exploration tokens.

## 3. Where the most tokens went, and how to save

Roughly: **~70% went to reading files** (`__init__.py` ~7k tokens × multiple reads, `registry.py` ~2.7k, `mcp_server.py` ~2.5k, plus engine/config/tests), **~15% to measurement bash calls**, **~15% to greps/verification**.

Saving tricks:
- Navigate with `file_skeleton` → then `read_section`/`grep` the 2-3 regions you actually need instead of full reads.
- Use `read_file` with `line_numbers=false` and tight `offset/limit`; the compact cache-hit response `(cached: N lines, unchanged)` is already the right shape — prefer it over re-reads.
- Do all measurement via `module_profile` (one structured call) instead of repeated ad-hoc `python -c` timing.
- One trick I used that paid off: `git stash` + measure + `git stash pop` to compare against baseline. Hardcode that as `module_profile --baseline HEAD` so the harness owns it.

## 4. Repeated patterns to hardcode as harness chains (reduce LLM orchestration, reduce drift for smaller LLMs)

These were repeated verbatim this session; encode them as deterministic chains so the LLM issues one call:

| Chain | Steps | Purpose |
|---|---|---|
| `probe_module` | `file_skeleton` → `who_imports`(self) → `who_imports`(consumers) | Understand a module + blast radius before editing |
| `verify_edit` | `edit_file` → `file_diff` → `py_compile` → import parent → targeted test file | Post-edit guard (already partly exists; add the compile+import smoke step) |
| `measure_change` | `module_profile` before → edit → `module_profile` after → delta report | Lazy-import/startup work specifically |

The wins: the LLM never re-derives "how do I find consumers" or "how do I verify a Python edit", so a smaller model needs far less reasoning and drifts less. These are chains, not new tool names — they compose existing tools, so no duplication.

## Summary of genuinely new tools (no duplicates)
1. `module_profile` — import-time profiler with delta comparison.
2. `file_skeleton` — atlas-free AST structure + import flags (complements `file_api`, doesn't replace it).
3. `who_imports` — cached import/reference index (complements `grep_search`).
4. `verify_refactor` — scoped post-edit compile+import+test hook (complements `run_tests`).
5. `file_facts` — file-keyed verified-facts log + pre-chat injection (complements kernel memory, not a duplicate).

**C. New tools from my earlier analysis (each directly cuts tokens):**
- `file_skeleton` — AST structure + import flags; replaces full `read_file` of large files (`file_ops.py` 626 lines, `__init__.py` 457, `stepper.py` 363). Biggest token saver for the "understand a module" step.
- `who_imports` — cached import/reference index; replaces repeated `grep` for `from agent_core.tools import` etc. (I ran this exact grep this session).
- `module_profile` — one-call import-time profiling with before/after delta; this session needed ~6 bash calls to do it manually.
- `file_facts` — file-keyed verified-facts log + pre-chat hook, so a future agent doesn't re-derive "tool_count=58", "`_register_all` is hot-reload API", etc.

**D. Pre/post-chat hooks worth wiring:**
- Post-edit: `verify_refactor` (py_compile + import parent + targeted test) auto-runs after every `edit_file` on `.py` files.
- Pre-chat: inject `file_facts` filtered to the files the task will touch.

Want me to implement any of these? If so, I'd suggest starting with `file_skeleton` and `module_profile` (they save the most tokens), and the `verify_refactor` hook.