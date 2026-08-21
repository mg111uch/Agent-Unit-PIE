### Where most tokens were spent

The heaviest steps were **multi-file edits** and **context-gathering reads**:

| Operation | ~Tokens | Why |
|---|---|---|
| Reading `engine.py` 5× at different offsets to understand full structure | **High** | Had to piece together context from scattered reads (lines 1-50, 96-175, 240-360, 590-700, 700-752) |
| Token usage display: 5 files edited (engine.py, ws_handler.py, store.js, index.html, AgentChat.js) | **High** | 5 sequential edit calls, each with file reads beforehand |
| Grep for `conversation_id` → read results → separate `read_file` to see context | **Medium** | Two-step pattern: grep finds line numbers, then read_file offset to see surroundings |

---

## ⏱ Patterns to Avoid (Token Waste)

- **Reading full files** with `Read` when `pie_file_api` already reveals structure. Only Read after you know the exact lines needed.
- **Sequential `pie_file_api` calls for 2+ files.** Use one `pie_file_api` with `paths=[...]` — it does the same work in one round trip.
- **Fetching source without checking metadata first.** Always call `pie_get_symbols_meta` before `pie_get_symbol`. A 200-token symbol may not be worth including.
- **Listing too many starting symbols** — blast radius doubles or triples the count. For `minimal_context_dump`, 5-8 focused symbols yield a tighter dump than 13+ broad ones.
- **Using full class.method() as symbol name** (e.g. `GeminiProvider.generate` instead of `GeminiProvider`). The atlas indexes the class, not individual method paths.
- **One edit per change** when the same pattern repeats in one file. Use `replace_all` for renames, `pie_batch_edit` only for *simple isolated replacements* (variable renames, import additions). For multi-line function-body changes, individual `edit` calls are more reliable — batch failures cost more tokens to recover from.
- **Re-reading freshly edited files** to verify edits. Use `Read` with `offset/limit` targeting only the changed lines instead of the full file.
- **Providing full context_dump to the LLM** when a targeted `minimal_context_dump` with the 5-8 relevant symbols suffices. The 3000-line dump in this project consumes ~25k tokens per read.
- **Multiple validation runs** after every single fix. Apply 3-5 related fixes together, then run validation once. This session did 3 separate validation runs — could have been 1.
- **Inline TODOs that duplicate what's in the fix checklist.** The session's `todowrite` items duplicated the diagnosis doc's checklist. Pick ONE source of truth — either the checklist or the todo list, not both. Keeping both in sync costs update tokens.
- **Context window waste** — holding full-file content in session after editing unrelated functions in that file. *Fix: after applying edits to a file, drop its full content from working memory and retain only the changed signatures.*

## ✅ Patterns to Follow

- **Batch symbol lookup** — pass multiple names in one `pie_get_symbol(names=[...])` call. One network round trip vs N.
- **Group fixes by file** — read a file, apply ALL its fixes, move on. Minimizes re-reading the same file.
- **Bump the checklist** in the diagnosis doc after each fix batch — keeps the session state visible to future agents.
- **DO** — **Check blast radius with `pie_find_impact`** before editing any symbol. Every symbol you modify may have dependents you don't see. Run `pie_find_impact(name="symbol")` during planning to surface all transitive dependents. Fix them in the same edit batch rather than discovering breakage at validation time.

## 🛠 New Tools That Would Accelerate This

- **`pie_validate_imports(package)`** — Static circular import detection: resolves all import chains in a package and flags cycles.
- **`pie_fix_checklist_sync(path)`** — Scans a markdown checklist, resolves each file:function() citation against the atlas, and auto-ticks items whose code matches the expected fix pattern. Keeps the checklist in sync with actual code state.