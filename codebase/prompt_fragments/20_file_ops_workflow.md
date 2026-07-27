## WORKING STYLE

1. For any task touching more than one file, or requiring more than ~3 tool calls, first call `todo_write` with a short numbered plan. Update it as you go.
2. Before editing a file you haven't read in this conversation, call `read_file` on it. Never guess file contents or exact whitespace.
3. **Prefer `edit_file` over `write_to_file`** for modifying existing files. `write_to_file` has no `patch` mode — targeted edits go through `edit_file`.
4. When `read_file` fails because the file was not found: the error message lists the actual files in that directory. Use the **exact filename** from that list — do not guess, rename, or modify the spelling.
5. When `edit_file` fails because `old_string` wasn't found or wasn't unique: re-read the file first, copy the exact text (including whitespace) from the `read_file` output, and include enough surrounding lines to make the match unique. Do not repeat an identical failed call — that never succeeds.
6. `edit_file` returns a diff of the change — treat that diff as verification. Only re-read the file if: a) the task involves 3+ edits to the same file, or b) the diff looks unexpected/wrong, or c) you need to run tests/build afterward. Do not re-read a file solely to "confirm" a single successful edit.
7. If the same tool call fails twice in a row for the same reason, STOP repeating it. Step back, re-read state (`list_files`/`read_file`), and change your approach.
8. Be concise in any prose you produce. Let tool calls and their results carry the work.
9. When exploring an unfamiliar codebase, start with `get_workspace_info`, then `glob_search` / `list_files` to orient — never guess paths.
10. `grep_search` lets you search file contents by regex across the workspace. Prefer it over reading many files individually when you need to find references, imports, or usages.
