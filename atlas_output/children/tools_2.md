# 📂 tools_2
Generated: 2026-07-26 16:20:18
Files: 6

---

F185│__init__.py│494
D: ●datetime,kernel,os,re,subprocess,+3
F: tool_call(fn)→Callable
   S: Wrap a tool function to catch ToolErrors and return structured ToolResult.
F: log_output(message,end,flush)
   ↳Called by: F160:run_auto_research,F185:execute_command_raw,F156:retrieve_kernel_context
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F160:run_auto_research],[F185:execute_command_raw],[F156:retrieve_kernel_context]
F: extract_json(text)
F: _is_command_allowed(cmd)→bool
   ↳Called by: F185:execute_command_raw
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:execute_command_raw]
F: _run_sandboxed(cmd,timeout)→str
   ↳Called by: F185:execute_command_raw | Calls: F155:get_user_workspace_root
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:execute_command_raw]
F: execute_command_raw(cmd)→str
   ↳Calls: F185:_run_sandboxed,F185:_is_command_allowed,F185:log_output
F: _register_file_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:str_p,F189:bool_p,F189:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_meta_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:str_p,F189:arr_p,F189:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_git_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:str_p,F189:bool_p,F189:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_kernel_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:arr_p,F189:float_p,F065:register_handlers
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_sim_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:str_p,F189:obj_p,F189:arr_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_code_rag_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:str_p,F189:arr_p,F189:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_observer_tools(reg,tc)
   ↳Called by: F185:_register_all | Calls: F189:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_all]
F: _register_all()
   ↳Called by: F159:_do_reload,F178:kernel_reload | Calls: F185:_register_observer_tools,F185:_register_file_tools,F185:_register_meta_tools
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F159:_do_reload],[F178:kernel_reload]
---

F188│expand_ops.py│7
D: ●modules,os,sys
---

F187│file_ops.py│417
D: ●json,kernel,os,re,subprocess,+4
F: _ensure_dir(path)
   ↳Called by: F187:write_to_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F187:write_to_file]
F: _read_file_content(full,offset,limit,line_numbers)→ToolResult
   ↳Called by: F187:read_file | Calls: F155:to_relative,F187:_count_lines
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F187:read_file]
F: _compute_diff(old_str,new_str)→list[str]
   ↳Called by: F187:edit_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F187:edit_file]
   S: Compute a simple unified diff between old and new strings.
F: _count_lines(path)→int
   ↳Called by: F187:_read_file_content
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F187:_read_file_content]
F: read_file(path)→ToolResult
   ↳Calls: F155:to_relative,F155:resolve,F187:_read_file_content
F: list_files(path)→ToolResult
   ↳Calls: F155:to_relative,F155:resolve
F: write_to_file(input_data)→ToolResult
   ↳Calls: F187:_ensure_dir,F155:to_relative,F183:save_checkpoint
   S: Write to file with modes: create, overwrite, append.
   S: input_data = {
   S: "path": "relative/path.txt",
   S: "mode": "create|overwrite|append",
   S: "content": "string (optional)",
F: edit_file(input_data)→ToolResult
   ↳Calls: F155:to_relative,F183:save_checkpoint,F187:_compute_diff
F: get_workspace_info(_input)→ToolResult
F: glob_search(pattern)→ToolResult
   S: Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts').
F: grep_search(input_data)→ToolResult
   S: Search file contents by regex across the workspace.
   S: input_data = {"pattern": "...", "include": "*.py", "max_results": 50}
   S: Uses ripgrep (rg) if available, falls back to Python regex walk.
F: read_section_tool(params)→ToolResult
   ↳Calls: F155:resolve
F: batch_edit_tool(params)→ToolResult
   ↳Calls: F155:resolve
F: batch_read_tool(params)→ToolResult
---

F186│git_ops.py│112
S: Git operation tools: status, diff, commit — behind config flag.
D: ●__future__,agent_core,json,os,subprocess
F: _check_git_enabled()→Any
   ↳Called by: F186:git_diff,F186:git_log,F186:git_commit
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F186:git_diff],[F186:git_log],[F186:git_commit]
F: _run_git(args,timeout)→str
   ↳Called by: F186:git_diff,F186:git_log,F186:git_commit
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F186:git_diff],[F186:git_log],[F186:git_commit]
F: git_status(input_data)→str
   ↳Calls: F186:_run_git,F186:_check_git_enabled
   S: Show git status of the workspace.
F: git_diff(input_data)→str
   ↳Calls: F186:_run_git,F186:_check_git_enabled
   S: Show git diff of uncommitted changes.
   S: input_data = {"path": "optional/path", "staged": false}
F: git_commit(input_data)→str
   ↳Calls: F186:_run_git,F186:_check_git_enabled
   S: Commit staged changes with a message.
   S: input_data = {
   S: "message": "commit message",
   S: "add_all": true      # optional: git add -A before commit
   S: }
F: git_log(input_data)→str
   ↳Calls: F186:_run_git,F186:_check_git_enabled
   S: Show recent git log.
   S: input_data = {"max_count": 10}
---

F189│registry.py│173
S: ToolRegistry: central registry for pluggable tool functions with category filtering,
D: ●__future__,typing
C: ToolRegistry│[__init__,set_default_category,register,tools_dict,schemas_list,meta_dict,get_tools,get_schemas,to_mcp_tools,add_middleware,+4]
F: _build_params_schema(params)→dict
   ↳Called by: F189:register
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F189:register]
F: _auto_input_format(params)→str
   ↳Called by: F189:register
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F189:register]
F: str_p(desc)
   ↳Called by: F185:_register_file_tools,F185:_register_meta_tools,F185:_register_git_tools
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F185:_register_file_tools],[F185:_register_meta_tools],[F185:_register_git_tools]
F: int_p(desc)
   ↳Called by: F185:_register_file_tools,F185:_register_observer_tools,F185:_register_meta_tools
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F185:_register_file_tools],[F185:_register_observer_tools],[F185:_register_meta_tools]
F: float_p(desc)
   ↳Called by: F185:_register_kernel_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_kernel_tools]
F: bool_p(desc)
   ↳Called by: F185:_register_git_tools,F185:_register_file_tools
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F185:_register_git_tools],[F185:_register_file_tools]
F: arr_p(item_t,desc)
   ↳Called by: F185:_register_kernel_tools,F185:_register_code_rag_tools,F185:_register_sim_tools
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F185:_register_kernel_tools],[F185:_register_code_rag_tools],[F185:_register_sim_tools]
F: obj_p(desc)
   ↳Called by: F185:_register_sim_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:_register_sim_tools]
C: ToolRegistry│[__init__,set_default_category,register,tools_dict,schemas_list,meta_dict,get_tools,get_schemas,to_mcp_tools,add_middleware,+4]
   F: __init__(self,mcp_prefix)
   F: set_default_category(self,category)
   F: register(self,name,fn)
   ↳Calls: F189:_auto_input_format,F189:_build_params_schema
   F: tools_dict(self)→Any
   F: schemas_list(self)→List[dict]
   F: meta_dict(self)→Any
   F: get_tools(self,categories)→Any
   F: get_schemas(self,provider_name,categories)→List[dict]
   F: to_mcp_tools(self,categories)→List[dict]
   F: add_middleware(self,middleware_fn)
   F: get_category(self,name)→str
   F: has_tool(self,name)→bool
   F: tool_names(self)→List[str]
   F: tool_count(self)→int
---

F190│types.py│24
S: Shared tool types — extracted from __init__.py to break circular imports.
D: ●dataclasses
C: ToolError←Exception│[__init__]
C: ToolResult│[to_string,to_dict]
C: ToolError←Exception│[__init__]
   F: __init__(self,error_type,message,suggestion)
C: ToolResult│[to_string,to_dict]
   F: to_string(self)→str
   F: to_dict(self)→dict
---
