# 📂 tools_2
Generated: 2026-07-21 18:31:40
Files: 4

---

F349│expand_ops.py│7
D: ●modules,os,sys
---

F348│file_ops.py│302
D: ●agent_core,os,pathlib,re,subprocess,+2
F: _ensure_dir(path)
   ↳Called by: F348:write_to_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F348:write_to_file]
F: _read_file_content(full,offset,limit)→str
   ↳Called by: F348:read_file,F348:read_file_range | Calls: F317:to_relative,F348:_count_lines
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F348:read_file],[F348:read_file_range]
F: _compute_diff(old_str,new_str)→list[str]
   ↳Called by: F348:edit_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F348:edit_file]
   S: Compute a simple unified diff between old and new strings.
F: _count_lines(path)→int
   ↳Called by: F348:_read_file_content
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F348:_read_file_content]
F: _coerce_str_arg(value)→str
   ↳Called by: F348:read_file,F348:list_files,F348:glob_search
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F348:read_file],[F348:list_files],[F348:glob_search]
   S: Accept a plain string or a dict of tool args (native function calling).
F: read_file(path)→str
   ↳Calls: F348:_coerce_str_arg,F317:resolve,F317:to_relative
F: read_file_range(input_data)→str
   ↳Calls: F317:resolve,F348:_read_file_content
   S: Read a portion of a file with offset (1-based) and optional limit.
   S: input_data = {"path": "...", "offset": 1, "limit": 50}
F: list_files(path)→str
   ↳Calls: F348:_coerce_str_arg,F317:resolve,F317:to_relative
F: write_to_file(input_data)→str
   ↳Calls: F317:resolve,F317:to_relative,F344:save_checkpoint
   S: Write to file with modes: create, overwrite, append.
   S: input_data = {
   S: "path": "relative/path.txt",
   S: "mode": "create|overwrite|append",
   S: "content": "string (optional)",
F: edit_file(input_data)→str
   ↳Calls: F317:resolve,F317:to_relative,F348:_compute_diff
F: get_workspace_info(_input)→str
F: glob_search(pattern)→str
   ↳Calls: F348:_coerce_str_arg
   S: Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts').
F: grep_search(input_data)→str
   S: Search file contents by regex across the workspace.
   S: input_data = {"pattern": "...", "include": "*.py", "max_results": 50}
   S: Uses ripgrep (rg) if available, falls back to Python regex walk.
---

F347│git_ops.py│112
S: Git operation tools: status, diff, commit — behind config flag.
D: ●__future__,agent_core,json,os,subprocess
F: _check_git_enabled()→Any
   ↳Called by: F347:git_status,F347:git_log,F347:git_commit
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F347:git_status],[F347:git_log],[F347:git_commit]
F: _run_git(args,timeout)→str
   ↳Called by: F347:git_status,F347:git_log,F347:git_commit
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F347:git_status],[F347:git_log],[F347:git_commit]
F: git_status(input_data)→str
   ↳Calls: F347:_run_git,F347:_check_git_enabled
   S: Show git status of the workspace.
F: git_diff(input_data)→str
   ↳Calls: F347:_run_git,F347:_check_git_enabled
   S: Show git diff of uncommitted changes.
   S: input_data = {"path": "optional/path", "staged": false}
F: git_commit(input_data)→str
   ↳Calls: F347:_run_git,F347:_check_git_enabled
   S: Commit staged changes with a message.
   S: input_data = {
   S: "message": "commit message",
   S: "add_all": true      # optional: git add -A before commit
   S: }
F: git_log(input_data)→str
   ↳Calls: F347:_run_git,F347:_check_git_enabled
   S: Show recent git log.
   S: input_data = {"max_count": 10}
---

F350│registry.py│103
S: ToolRegistry: central registry for pluggable tool functions with category filtering,
D: ●__future__,typing
C: ToolRegistry│[__init__,register,tools_dict,schemas_list,meta_dict,get_tools,get_schemas,to_mcp_tools,add_middleware,get_category,+3]
   S: Central registry for tool functions, schemas, and metadata.
C: ToolRegistry│[__init__,register,tools_dict,schemas_list,meta_dict,get_tools,get_schemas,to_mcp_tools,add_middleware,get_category,+3]
   S: Central registry for tool functions, schemas, and metadata.
   F: __init__(self)
   F: register(self,name,fn)
   F: tools_dict(self)→Any
   F: schemas_list(self)→List[dict]
   F: meta_dict(self)→Any
   F: get_tools(self,categories)→Any
   F: get_schemas(self,provider_name)→List[dict]
   F: to_mcp_tools(self,categories)→List[dict]
   F: add_middleware(self,middleware_fn)
      S: Add middleware that wraps each tool.
      S: middleware_fn receives (name, fn) and returns wrapped fn.
   F: get_category(self,name)→str
   F: has_tool(self,name)→bool
   F: tool_names(self)→List[str]
   F: tool_count(self)→int
---
