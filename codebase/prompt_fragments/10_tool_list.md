## TOOL USAGE NOTES

- Prefer `edit_file` over `write_to_file` for modifying existing files.
- Don't re-read files marked as "cached, unchanged" in the session context digest.
- `edit_file`'s diff output IS your verification — see rule 6.
- `grep_search` over reading many files individually for find/usages.
- `execute_command` runs trusted commands only — use it for builds/tests/format.
- `get_workspace_info` is called once per session — digest caches it.
