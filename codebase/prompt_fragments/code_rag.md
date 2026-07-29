## CODE RAG WORKFLOW

- **Named symbols → `get_symbol` first (batch):** When the user names one or more functions/classes, call `get_symbol` **once** with those exact names — do **not** call `search_symbols` first.
   Example: user asks about `get_counter_argument` and `index_graph` →
   `get_symbol({"names": ["get_counter_argument", "index_graph"]})`
- **Budget awareness:** `get_symbol` may truncate large batches (`truncated_names`). Re-call only for omitted names.
- **You already have the code:** If `get_symbol` returns a symbol's full `code` field, do not also `read_file` / `read_file_range` for the same symbol.
- Never `Read` a file directly — use `pie_file_api` first, always.
