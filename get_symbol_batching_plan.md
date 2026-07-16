# Code RAG: `get_symbol` Workflow — Diagnosis & Fix Plan

**Date:** 2026-07-16 (updated same day)  
**Status:** Implemented (get-symbol-first; no search prefetch)

---

## Expected behavior (authoritative)

When the user names functions (e.g. “details of `get_counter_argument` and `index_graph`”):

1. **First tool call:** `get_symbol` once with  
   `names: ["get_counter_argument", "index_graph"]`
2. **Do not** call `search_symbols` first.
3. **Only if** `get_symbol` returns not-found / `missing_names` (typo, unknown name):  
   use `search_symbols` for the missing names, then `get_symbol` again with corrected **exact** names the agent still needs.
4. Never auto-fetch definitions for every FTS hit (noise + budget blowup).

---

## What went wrong with the previous fix

Tier-1 “enrich `search_symbols`” added:

- `batch_get_symbol_hint` (all hit names, including unrelated)
- `prefetched_symbols` (full bodies for many hits)

Observed chat (`Issues_n_ideas.md`): agent still **searched first**, then received **prefetch of all hits** (including `run_explore_loop`), which is the opposite of named-lookup efficiency.

Root issue of that design: it optimized “search → batch get” instead of “user already named symbols → direct get.”

---

## Earlier diagnosis (still valid for sequential batching)

| Factor | Role |
|--------|------|
| Single-action response contract | Encourages one tool per turn |
| Soft “search then batch” prompts | Trained wrong default order |
| Same-turn executor merge | Helps only parallel multi-call in one turn |
| Array schema | Fine — model can pass multi-name lists |

---

## Implemented fix (current)

### Server

- **`search_symbols_tool`:** metadata-only again — **no** `prefetched_symbols`, **no** `batch_get_symbol_hint`.
- **`get_symbol_tool`:**
  - Accepts `names` (list) or `name` (string).
  - Returns `missing_names` + hint when some/all names fail → search is the fallback, not the default.
  - Keeps budget / `truncated_names` behavior.

### Prompts / schema

- `prompt_fragments/25_code_rag.md` — **get_symbol first**, search only on miss / discovery.
- `60_response_contract.md` — same efficiency rule.
- Tool schema + registry meta — `get_symbol` primary for named lookups; `search_symbols` secondary.

### Still keep

- Same-turn merge of parallel `get_symbol` in `executor.py` (fan-out full result).
- LLM may still search first if it ignores prompts; server no longer amplifies that with bulk prefetch.

---

## Expected good transcript

```
User: Give short details of functions get_counter_argument and index_graph

[tool: get_symbol]
input: {"names": ["get_counter_argument", "index_graph"]}
result: { "symbols": [ ... both definitions ... ] }

→ final answer from those symbols only
```

Misspelling path:

```
[tool: get_symbol]
input: {"names": ["get_counter_argumnt", "index_graph"]}
result: { "symbols": [...index_graph...], "missing_names": ["get_counter_argumnt"], "hint": "..." }

[tool: search_symbols]
input: {"query": "get_counter_argumnt OR counter argument"}

[tool: get_symbol]
input: {"names": ["get_counter_argument"]}
```

---

## Key files

| File | Role |
|------|------|
| `codebase/agent_core/tools/code_rag.py` | Tools + no prefetch on search |
| `codebase/prompt_fragments/25_code_rag.md` | get_symbol-first workflow |
| `codebase/prompt_fragments/60_response_contract.md` | Efficiency rule |
| `codebase/agent_core/tools/schemas.py` | Tool descriptions |
| `codebase/agent_core/tools/__init__.py` | Registry meta |
| `codebase/agent_core/loop/executor.py` | Same-turn batch merge |
