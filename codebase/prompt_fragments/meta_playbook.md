## META TOOLS

- `get_workspace_info` caches after first call — subsequent calls cost nothing.
- Checkpoints are saved automatically before `edit_file` and `write_to_file (overwrite)`.
- **Always prefer `batch_edit` over multiple `edit_file` calls when editing the same file** — Any time you need 2+ edits to the same file, use a single `batch_edit` call instead of sequential `edit_file` calls. This applies regardless of whether the edits are related or repetitive. Each sequential `edit_file` wastes a step, while `batch_edit` does all edits in one step. The tool supports `replace_all` for bulk renames.
- **Prefer `batch_file_api` when ≥2 files** — batch reduces token overhead vs. serial `file_api` calls.