## Tool Search

A small always-on set of tools is available every turn (file read/search/edit,
`ask_user_question`, plus `find_tool` / `get_tool_schema`). For any capability
outside that set:

1. Call `find_tool(query=...)` with capability keywords to discover matching
   tools (name, category, one-line description, compact params).
2. If you need the exact argument contract, call `get_tool_schema(name=...)`.
3. Then call the discovered tool directly by name — execution runs against the
   full registry, so no schema re-exposure is needed.

`find_tool` only returns tools enabled by the current `tool_packs` / `tool_mode`.
If search returns nothing, rephrase with broader keywords or a category name
(e.g. `code_rag`, `kernel`, `git`, `sim`, `observer`).