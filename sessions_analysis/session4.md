## Token Spend Analysis & Tool Proposals

### Where most tokens were spent

| Activity | Est. tokens | % of session |
|---|---|---|
| Reading `engine.py` (765 lines) × 4+ passes | ~14,000 | 35% |
| Reading `file_ops.py` (464 lines) × 2 passes | ~4,000 | 10% |
| Exploring provider/model config (5+ files) | ~6,000 | 15% |
| Reading prompt fragments + config.json | ~2,000 | 5% |
| Reading/planning discussions (stepper.py design) | ~8,000 | 20% |
| Edit operations (stepper.py rewrite, engine.py refactor) | ~6,000 | 15% |
| **Total** | **~40,000** | |

**The single biggest sink:** re-reading large files to *understand* them before editing. I read `engine.py` ~4 times fully when a 30-line structural summary would have sufficed for 3 of those passes.

---

### Proposed novel tools

#### 1. `reduce_file` — File structure summarizer

Returns a compact structural map of a Python file (imports, functions/classes with signatures + line ranges, globals). Instead of reading 765 lines, get ~25 lines of output.

```
reduce_file(path="engine.py")
  → imports: [json, os, threading, ..., ParseProviderResponse, ToolResult, ...]
  → functions:
      _debug_dump  L051-070  (22 lines)
      iter_agent_events L073-096  (24 lines  → calls _iter_agent_events_body)
      _iter_agent_events_body L099-295 (197 lines  → calls dispatch_step, _generate_with_cancel)
      run_agent_turn L297-343  (47 lines)
  → globals: [_schema_dumped]
  → total: 343 lines
```

**vs existing tools:**
- `file_api_tool` — similar but requires codebase atlas index (may not exist), returns per-symbol metadata not file-level structure, doesn't show imports or line ranges
- `read_file` with offset/limit — still requires knowing what to ask for

**Novelty:** Pure-Python parser (ast module), no external DB needed, works on any `.py` file immediately. Returns a "table of contents" for a file — something no current tool provides.

#### 2. `session_map` — Working set tracker

Tracks which files were read/edited in the current session and their relevant context. A compact session memory so you don't re-discover the same files.

```
session_map()
  → Files accessed:
      engine.py        (read 4×, edited: lines 150-152, 197, 249-275)
      stepper.py       (created, 353 lines)
      file_ops.py      (read 2×, edited: lines 380-392, 423-424)
      config.py        (read 1×, edited: line 82)
      ...
  → Last edit context: schema caching → moved get_schemas outside loop
```

**vs existing tools:**
- `get_workspace_info` — shows workspace root, file cache, but not session-specific access history
- `todo_write` — tracks task plans, not file access history
- Session `dir_cache` — caches directory listings, not file read/edit history

**Novelty:** Cross-file session-aware context that persists across turns. Currently the agent re-discovers file structures every turn.

#### 3. `dep_graph` — Dependency scanner

Given a file, returns its imports and what imports it — so you know which files break if you change something.

```
dep_graph(path="stepper.py")
  → stepper.py imports:
      agent_core.tools
      agent_core.loop._helpers  (_truncate_result, _compact_corrective_exchange, ...)
      agent_core.loop.messages
      agent_core.loop.streaming
      agent_core.loop.executor
      agent_core.loop.session_state
  → files that import stepper.py:
      agent_core.loop.engine.py
```

**vs existing tools:**
- `get_callers_callees` — symbols only (function-level), not import/module-level
- `find_impact` — symbol-level impact, not file/module-level

**Novelty:** Module-level dependency graph, buildable with `ast` + `grep_search`. Faster than manually tracing imports across files.

#### 4. `smart_read` — Scenario-aware file reading

Read a file with a purpose hint to automatically optimize reading: for editing, include line numbers; for understanding, return structure instead of content; for searching, highlight matches.

```
smart_read(path="stepper.py", purpose="edit")
  → [full content with line numbers for precise editing]
smart_read(path="stepper.py", purpose="structure")
  → [structural summary like reduce_file]
smart_read(path="engine.py", purpose="find", query="dispatch_step")
  → [only lines 267-281 where dispatch_step is called, with context]
```

**vs existing tools:**
- `read_file` — always returns raw content, always with line numbers (by default)
- `grep_search` — returns matching lines from all files, not contextual reads
- `read_section` — needs explicit line numbers

**Novelty:** Single tool that adapts output format to the use case, reducing token waste from irrelevant content.

---

### Where you'd save the most

| Strategy | Tokens saved per session | Effort to build |
|---|---|---|
| `reduce_file` for understanding phase | ~10K-15K (replaces 4× full reads with 1× summary + 1× targeted read) | ~150 lines of Python using `ast` |
| `smart_read` with structure mode | ~8K-12K (no more 700-line reads just to find function signatures) | Wraps `reduce_file` + `read_file` |
| `session_map` for continuity | ~4K-6K (no re-discovering what was done last turn) | ~100 lines, uses existing msg_store |
| `dep_graph` for edit safety | ~2K-4K (no searching for all files that import X) | ~80 lines, uses `ast` + `grep` |

The **highest ROI** is `reduce_file`: ~150 lines of code, pure Python standard library (`ast` module), saves 10K-15K tokens per session by eliminating the "read to understand" phase.

==========================

