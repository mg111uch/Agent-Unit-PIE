## META TOOLS

- `get_workspace_info` caches after first call — subsequent calls cost nothing.
- Checkpoints are saved automatically before `edit_file` and `write_to_file (overwrite)`.
- **Always prefer `edit_file` with `edits` when editing the same file 2+ times** — Any time you need 2+ edits to the same file, use a single `edit_file` call with `edits=[{old_string, new_string, replace_all?}, ...]` instead of sequential `edit_file` calls. This applies regardless of whether the edits are related or repetitive. Each sequential `edit_file` wastes a step, while one batched `edit_file` does all edits in a single step. Set `replace_all=true` for bulk renames.
- **Prefer `batch_file_api` when ≥2 files** — batch reduces token overhead vs. serial `file_api` calls.