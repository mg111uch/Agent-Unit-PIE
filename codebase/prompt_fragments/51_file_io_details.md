**write_to_file modes:**
- `create` — fails if file exists
- `overwrite` — replaces entire file
- `append` — adds content to end

**edit_file rules:**
- `old_string` must match exactly (whitespace-sensitive) and appear exactly once in the file
- Include surrounding lines for uniqueness if needed
- Re-read the file with `read_file` first to copy exact text

**read_file_range:**
- Use `read_file_range` with `offset` and `limit` when you only need a portion of a large file (e.g., the first 50 lines, or lines 100-150)
- `offset` is 1-based; omit to start from line 1
- `limit` is the max lines to return; omit for the rest of the file
- For small files, prefer `read_file` (simpler)
