# 📂 tools_2
Generated: 2026-07-23 14:15:38
Files: 4

---

F186│expand_ops.py│7
D: ●modules,os,sys
---

F185│file_ops.py│401
D: ●agent_core,json,pathlib,re,subprocess,+2
F: _ensure_dir(path)
   ↳Called by: F185:write_to_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:write_to_file]
F: _read_file_content(full,offset,limit)→str
   ↳Called by: F185:read_file | Calls: F185:_count_lines,F154:to_relative
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:read_file]
F: _compute_diff(old_str,new_str)→list[str]
   ↳Called by: F185:edit_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:edit_file]
   S: Compute a simple unified diff between old and new strings.
F: _count_lines(path)→int
   ↳Called by: F185:_read_file_content
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_read_file_content]
F: read_file(path)→str
   ↳Calls: F154:resolve,F154:to_relative,F185:_read_file_content
F: list_files(path)→str
   ↳Calls: F154:resolve,F154:to_relative
F: write_to_file(input_data)→str
   ↳Calls: F154:resolve,F181:save_checkpoint,F154:to_relative
   S: Write to file with modes: create, overwrite, append.
   S: input_data = {
   S: "path": "relative/path.txt",
   S: "mode": "create|overwrite|append",
   S: "content": "string (optional)",
F: edit_file(input_data)→str
   ↳Calls: F154:resolve,F185:_compute_diff,F181:save_checkpoint
F: get_workspace_info(_input)→str
F: glob_search(pattern)→str
   S: Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts').
F: grep_search(input_data)→str
   S: Search file contents by regex across the workspace.
   S: input_data = {"pattern": "...", "include": "*.py", "max_results": 50}
   S: Uses ripgrep (rg) if available, falls back to Python regex walk.
F: read_section_tool(params)→str
   ↳Calls: F154:resolve
F: batch_edit_tool(params)→str
   ↳Calls: F154:resolve
F: batch_read_tool(params)→str
---

F184│git_ops.py│112
S: Git operation tools: status, diff, commit — behind config flag.
D: ●__future__,agent_core,json,os,subprocess
F: _check_git_enabled()→Any
   ↳Called by: F184:git_diff,F184:git_commit,F184:git_log
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F184:git_diff],[F184:git_commit],[F184:git_log]
F: _run_git(args,timeout)→str
   ↳Called by: F184:git_diff,F184:git_commit,F184:git_log
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F184:git_diff],[F184:git_commit],[F184:git_log]
F: git_status(input_data)→str
   ↳Calls: F184:_run_git,F184:_check_git_enabled
   S: Show git status of the workspace.
F: git_diff(input_data)→str
   ↳Calls: F184:_run_git,F184:_check_git_enabled
   S: Show git diff of uncommitted changes.
   S: input_data = {"path": "optional/path", "staged": false}
F: git_commit(input_data)→str
   ↳Calls: F184:_run_git,F184:_check_git_enabled
   S: Commit staged changes with a message.
   S: input_data = {
   S: "message": "commit message",
   S: "add_all": true      # optional: git add -A before commit
   S: }
F: git_log(input_data)→str
   ↳Calls: F184:_run_git,F184:_check_git_enabled
   S: Show recent git log.
   S: input_data = {"max_count": 10}
---

F187│registry.py│169
S: ToolRegistry: central registry for pluggable tool functions with category filtering,
D: ●__future__,typing
C: ToolRegistry│[__init__,set_default_category,register,tools_dict,schemas_list,meta_dict,get_tools,get_schemas,to_mcp_tools,add_middleware,+4]
F: _build_params_schema(params)→dict
   ↳Called by: F187:register
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F187:register]
F: _auto_input_format(params)→str
   ↳Called by: F187:register
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F187:register]
F: str_p(desc)
   ↳Called by: F183:_register_git_tools,F183:_register_code_rag_tools,F183:_register_file_tools
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F183:_register_git_tools],[F183:_register_code_rag_tools],[F183:_register_file_tools]
F: int_p(desc)
   ↳Called by: F183:_register_git_tools,F183:_register_code_rag_tools,F183:_register_file_tools
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F183:_register_git_tools],[F183:_register_code_rag_tools],[F183:_register_file_tools]
F: float_p(desc)
   ↳Called by: F183:_register_kernel_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_kernel_tools]
F: bool_p(desc)
   ↳Called by: F183:_register_git_tools,F183:_register_file_tools
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F183:_register_git_tools],[F183:_register_file_tools]
F: arr_p(item_t,desc)
   ↳Called by: F183:_register_code_rag_tools,F183:_register_kernel_tools,F183:_register_sim_tools
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F183:_register_code_rag_tools],[F183:_register_kernel_tools],[F183:_register_sim_tools]
F: obj_p(desc)
   ↳Called by: F183:_register_sim_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_sim_tools]
C: ToolRegistry│[__init__,set_default_category,register,tools_dict,schemas_list,meta_dict,get_tools,get_schemas,to_mcp_tools,add_middleware,+4]
   F: __init__(self,mcp_prefix)
   F: set_default_category(self,category)
   F: register(self,name,fn)
   ↳Calls: F187:_auto_input_format,F187:_build_params_schema
   F: tools_dict(self)→Any
   F: schemas_list(self)→List[dict]
   F: meta_dict(self)→Any
   F: get_tools(self,categories)→Any
   F: get_schemas(self,provider_name)→List[dict]
   F: to_mcp_tools(self,categories)→List[dict]
   F: add_middleware(self,middleware_fn)
   F: get_category(self,name)→str
   F: has_tool(self,name)→bool
   F: tool_names(self)→List[str]
   F: tool_count(self)→int
---
