META TOOLS:
- get_workspace_info: workspace/path intel. cheap, cached after 1st call. unsure where things live -> call it (or list_files). no guessing.
- checkpoints auto-saved before edit_file and write_to_file(overwrite).
- 2+ edits same file -> single edit_file(edits=[{old_string,new_string,replace_all?},...]). 1 call, not sequential.
- prefer batched calls (read path list / file_api paths=[...]) when 2+ files -> less token overhead.