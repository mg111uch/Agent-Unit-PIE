META TOOLS:
- get_workspace_info: workspace/path intel. cheap, cached after 1st call. unsure where things live -> call it (or Read). no guessing.
- checkpoints auto-saved before edit_file and Write(overwrite).
- 2+ edits same file -> single edit_file(edits=[{old_string,new_string,replace_all?},...]). 1 call, not sequential.
- prefer batched calls (read path list / file_api paths=[...]) when 2+ files -> less token overhead.