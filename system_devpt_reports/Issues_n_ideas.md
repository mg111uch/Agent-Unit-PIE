# Prompt
I have kernel which is very big and it cannot be read by a llm in one go. Also files in the kernel are also very large in size. I want to a llm to check my kernel codebase using my code_rag based mcp tools only not by reading complete files. I have a max token budget of 80k tokens only. Your task is to design a prompt for external llm so that it can check kernel code in limited budgest to suggest improvement.You are not allowed to read kernel files.

# Response (updated with real atlas stats)
Now I have the context. Here's the designed prompt for the external LLM:

---

## Prompt for External LLM: Kernel Code Review (80k Token Budget)

You are auditing a kernel codebase. **Do NOT read whole files.** Use only code_rag tools. **Start every session by calling `get_index_info`** to get real-time atlas stats — use those numbers to calibrate your batch sizes and budget estimates below.

### Available Tools
- `get_index_info` — Real-time atlas stats (symbols, edges, token ranges, risk). **Call once at session start** to calibrate budget.
- `get_symbols_meta(names=['f1','f2'])` — Batch metadata (signature, token_count, risk, lines) **without code**. Use first to browse cheaply.
- `get_symbol(names=['f1','f2'])` — Full source + docstring for exact names. **Call only after meta tells you it's worth it.**
- `search_symbols(query, top_k=5)` — FTS5 search over names/docs/code. Small `top_k` always.
- `get_callers_callees(name)` — Who calls it / what it calls (depth=1 unless needed).
- `find_impact(name)` — Everything transitively depending on this symbol.
- `read_file_range(path, offset, limit=50)` — Read small slices (<50 lines) only when code RAG cannot answer.
- `grep_search(pattern, include="*.py")` — Pattern match across codebase.
- `kernel_emit_signal(title, value, category, importance)` — Log findings.

### Token Budget Rules (CRITICAL)
- **Total budget: 80k tokens** across ALL rounds. Call `get_index_info` first to get real numbers for your project.
- Use `get_index_info` results to calibrate: total codebase tokens tells you how much headroom you have; avg function token count tells you safe batch sizes.
- `get_symbols_meta(3 names)` → ~200 tokens (cheap — use liberally).
- `get_symbol(n names)` → `n * avg_function_tokens` from index info. **Batch conservatively: aim for ~1k tokens per call.**
- `get_callers_callees` → ~200–800 tokens (depends on graph density).
- `read_file_range(limit=50)` → ~500 tokens.
- After every 8 tool calls, call `kernel_emit_signal` with a running token-estimate summary.
- **Hard stop at 75k tokens used.** Only emit final summary signals.

### Review Strategy
0. **Calibrate**: `get_index_info` — real token counts, edge count, risk distribution. Use this to set batch sizes for the session.
1. **Discover module surface**: `search_symbols(query="{module_name}", top_k=5)` — identify 3–5 key entry points.
2. **Browse cheaply**: `get_symbols_meta(names=['entry1','entry2','entry3'])` — see signatures, token counts, risk levels. Only proceed to step 3 if a symbol seems worth it.
3. **Drill worth-it symbols**: `get_symbol(names=['selected1','selected2'])` — read full source of high-risk or high-token-count functions.
4. **Map dependencies**: `get_callers_callees('key_function')` — check coupling, circular deps, layering violations. Graph is sparse (26 edges / 30 functions) so expect shallow trees — depth >2 unlikely to yield new info.
5. **Validate structure**:
   - Each file should have one public class/function (<500 lines) — use `grep_search("class |def ")` + `read_file_range` to spot-check.
   - No circular imports — use `find_impact` to trace dependency direction.
6. **Spot-check risky patterns**:
   - Hardcoded secrets/keys: `grep_search("api_key|secret|token|password")`
   - Broad except blocks: `grep_search("except:|except Exception")`
   - Mutable global state: `grep_search("^\\w+ = ")` in small slices.
7. **Log findings**: `kernel_emit_signal` for every issue (category="code_review", importance proportional to severity).

### Output
Emit one signal per finding. Final signal must contain a numbered summary: issues found, token usage, files that need refactoring, and suggested next steps.

### Anti-Patterns to Avoid
- ❌ Reading files over 50 lines in a single call
- ❌ Calling `search_symbols` with `top_k > 5`
- ❌ Calling `get_symbol` without `get_symbols_meta` first
- ❌ Deep recursive traversal (>2 levels) — graph is too sparse to benefit
- ❌ Any tool call after 75k tokens estimated


---

## Medium-Term Suggestion: Kernel-Aware Code Exploration

**Problem:** Every code review session starts from scratch. The LLM re-discovers the same symbols, re-traces the same call graphs, and re-notes the same findings. If a session is interrupted (token budget exhausted, tool timeout), all context is lost — the next run has no memory of what was already examined.

**Solution:** Wire `kernel_retrieve` into the code_rag tool chain so the kernel remembers which symbols have already been reviewed across sessions. This requires three additions:

### 1. Signal emission on symbol access

Every code_rag tool (`get_symbol`, `get_symbols_meta`, `get_callers_callees`, etc.) emits a `code_access` signal after returning results:

```python
# Inside get_symbol_tool, before returning:
kernel_emit_signal(
    signal_type="code_access",
    title=f"Reviewed: {name}",
    value=json.dumps({
        "symbols": names,
        "tool": "get_symbol",
        "token_cost": total_tokens,
        "risk_levels": {s["symbol_name"]: s["risk_level"] for s in symbols},
    }),
    category="code_review",
    importance=0.3,  # low — just a breadcrumb
)
```

The kernel stores these as episodic memories. Over time, patterns emerge: "this file's symbols keep getting fetched but never acted on" → suggests it's hard to understand; "this function was flagged high-risk in 3 separate sessions" → suggests it needs refactoring.

### 2. Pre-session retrieval to warm up the review

When a code review session starts, the LLM first calls `kernel_retrieve(query="code_review findings", limit=10)` to pull up symbols that were already examined or flagged in prior sessions. The response tells it:

- Which symbols were already reviewed (skip re-reviewing)
- Which were flagged as high-risk (prioritize re-checking if fixes were applied)
- Which files had structural issues (circular deps, large token counts)

This alone saves 20–30% of the token budget by avoiding redundant work.

### 3. Post-session summary persistence

At session end (or on hard stop at 75k), the LLM emits a `code_review_complete` signal that consolidates all findings into a single kernel memory entry:

```python
kernel_store_context(
    memory_type="code_review",
    content=json.dumps({
        "session_id": "<timestamp>",
        "symbols_reviewed": [...],
        "issues_found": [...],
        "token_used": 72000,
        "truncated_symbols": [...],  # names that hit budget before review
    }),
    importance=0.8,
    tags=["code_review", "atlas", "argu_god"],
    ttl_seconds=86400 * 30,  # 30-day retention
)
```

On the next session, `kernel_retrieve` finds this memory and the LLM knows exactly where it left off.

### Implementation cost

| Component | Change |
|-----------|--------|
| `code_rag.py` | Add `kernel_emit_signal` import + call after each tool function |
| `prompts.py` | Add instruction in code_rag prompt fragment to call `kernel_retrieve` at start and `kernel_store_context` at end |
| `main.py` / `generate_atlas` | No change — atlas is static data, the kernel adds the dynamic session layer |
| Token overhead | ~100 tokens per tool call for the emit, ~300 for the pre-session retrieve |