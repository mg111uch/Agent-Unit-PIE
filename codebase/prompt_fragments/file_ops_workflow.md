## TOOL USAGE & WORKFLOW

- Don't re-read files marked as "cached, unchanged" in the session context digest.
- Use `grep_search` over reading many files individually for find/usages.
- `execute_command` runs trusted commands only — use it for builds/tests/format.
- For tasks touching >1 file or requiring ~3+ calls, first call `todo_write` with a short numbered plan. Update it as you go.
- Before editing, `read_file` first. Never guess file contents or exact whitespace.
- On `edit_file` failure (old_string not found / not unique): re-read the file, copy exact text with surrounding lines. Do not repeat the identical failed call.
- `edit_file` returns a diff — treat it as verification. Re-read only if 3+ edits, unexpected diff, or tests needed. Do not re-read solely to confirm.
- If a tool call fails twice for the same reason, step back and change approach — do not repeat.
- `check_path_exists` errors list matching files elsewhere — use that hint instead of retrying with guessed prefixes.
- `edit_file` `old_string` must match exactly (whitespace-sensitive) and appear exactly once.
- When `read_file` or `list_files` fails: error lists nearby files. Use the **exact filename** from that list. If still not found, `glob_search("**/<filename>")` before concluding it doesn't exist.
- When exploring: `glob_search` / `list_files` to orient — never guess paths. If a path fails, try prefixing with `codebase/`.
- **Verify directory paths with `list_files` before reading** — When uncertain about a file's location or the directory structure, call `list_files` on the suspected parent directory first. Guessing paths wastes a round trip on a file-not-found error.
- Use `read_file` with `offset` and `limit` for portions of a large file (e.g. first 50 lines, lines 100-150); `offset` is 1-based; omit to start from line 1; `limit` is max lines to return; omit for rest of file.
- **Use the cheapest tool that answers the query** — `check_path_exists` is lighter than `list_files` which is lighter than `read_file`. Don't gather data the user didn't ask for.
- **Stop producing tool calls as soon as you have enough information to respond.**
