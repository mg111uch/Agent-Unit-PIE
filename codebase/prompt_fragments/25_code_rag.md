## CODE RAG WORKFLOW

1. **Named symbols → `get_symbol` first (batch):** When the user names one or more functions/classes, call `get_symbol` **once** with those exact names — do **not** call `search_symbols` first.

   Example: user asks about `get_counter_argument` and `index_graph` →
   `get_symbol({"names": ["get_counter_argument", "index_graph"]})`

2. **Search only on failure / discovery:** Use `search_symbols` only when:
   - `get_symbol` returns `missing_names` or "not found" (possible misspelling), or
   - the user did **not** give exact names and you need to discover candidates.

   After search, pick only the symbols you still need (do not auto-fetch every search hit), then call `get_symbol` once with that short name list.

3. **Budget awareness:** `get_symbol` may truncate large batches (`truncated_names`). Re-call only for omitted names.

4. **You already have the code:** If `get_symbol` returns a symbol's full `code` field, do not also `read_file` / `read_file_range` for the same symbol.
