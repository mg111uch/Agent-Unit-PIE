# 📂 tools_1
Generated: 2026-07-23 14:15:38
Files: 10

---

F183│__init__.py│475
D: ●agent_core,dataclasses,datetime,re,subprocess,+2
C: ToolError←Exception│[__init__]
C: ToolResult│[to_string,to_dict]
F: tool_call(fn)→Callable
   S: Wrap a tool function to catch ToolErrors and return structured ToolResult.
F: log_output(message,end,flush)
   ↳Called by: F160:load_system_prompt,F183:execute_command_raw,F195:run_agent_turn
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F160:load_system_prompt],[F183:execute_command_raw],[F195:run_agent_turn]
F: extract_json(text)
F: _is_command_allowed(cmd)→bool
   ↳Called by: F183:execute_command_raw
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:execute_command_raw]
F: _run_sandboxed(cmd,timeout)→str
   ↳Called by: F183:execute_command_raw | Calls: F154:get_user_workspace_root
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:execute_command_raw]
F: execute_command_raw(cmd)→str
   ↳Calls: F183:log_output,F183:_run_sandboxed,F183:_is_command_allowed
F: _register_file_tools(reg,tc)
   ↳Called by: F183:_register_all | Calls: F187:bool_p,F187:str_p,F187:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_all]
F: _register_meta_tools(reg,tc)
   ↳Called by: F183:_register_all | Calls: F187:arr_p,F187:str_p,F187:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_all]
F: _register_git_tools(reg,tc)
   ↳Called by: F183:_register_all | Calls: F187:bool_p,F187:str_p,F187:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_all]
F: _register_kernel_tools(reg,tc)
   ↳Called by: F183:_register_all | Calls: F187:arr_p,F187:float_p,F187:str_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_all]
F: _register_sim_tools(reg,tc)
   ↳Called by: F183:_register_all | Calls: F187:arr_p,F187:obj_p,F187:str_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_all]
F: _register_code_rag_tools(reg,tc)
   ↳Called by: F183:_register_all | Calls: F187:arr_p,F187:str_p,F187:int_p
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:_register_all]
F: _register_all()
   ↳Called by: F177:kernel_reload,F158:_do_reload | Calls: F183:_register_git_tools,F183:_register_code_rag_tools,F183:_register_file_tools
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F177:kernel_reload],[F158:_do_reload]
C: ToolError←Exception│[__init__]
   F: __init__(self,error_type,message,suggestion)
C: ToolResult│[to_string,to_dict]
   F: to_string(self)→str
   F: to_dict(self)→dict
---

F176│audit_ops.py│36
D: ●json,kernel
F: emit_tool_compliance_signal(read_count,pie_count,kernel_read_count)→str
---

F182│context_dump.py│137
D: ●agent_core,json,os,pathlib,typing
F: _rough_token_count(text)→int
   ↳Called by: F182:minimal_context_dump
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F182:minimal_context_dump]
F: _collect_blast_radius(rag,names,output)→None
F: minimal_context_dump(params)→str
   ↳Calls: F190:_resolve_path,F190:_get_rag,F182:_rough_token_count
---

F180│debate_ops.py│7
D: ●modules,os,sys
---

F177│kernel_ops.py│186
D: ●agent_core,importlib,json,kernel,sys
F: kernel_retrieve(input_data)→str
F: kernel_emit_signal(input_data)→str
F: kernel_store_context(input_data)→str
   ↳Calls: F032:generate_id,F033:generate_id,F028:generate_id
F: kernel_get_memory(input_data)→str
F: kernel_create_event(input_data)→str
F: kernel_reload(input_data)→str
   ↳Calls: F183:_register_all
   S: Reload tool modules from disk to pick up code changes without restart.
---

F174│plan_ops.py│56
D: ●__future__,json,typing
F: _load_plan()→list[dict]
   ↳Called by: F174:todo_write,F174:todo_read
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F174:todo_write],[F174:todo_read]
F: _save_plan()
   ↳Called by: F174:todo_write
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F174:todo_write]
F: todo_write(input_data)→str
   ↳Calls: F174:_save_plan,F174:_load_plan
F: todo_read(_input)→str
   ↳Calls: F174:_load_plan
---

F175│question_ops.py│53
D: ●json,threading,typing
F: ask_user_question(raw_input)→str
F: resolve_all_questions(session_id,answers)→bool
   ↳Called by: F169:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F169:handle_chat]
F: cancel_questions(session_id)→bool
   ↳Called by: F169:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F169:handle_chat]
---

F178│sim_ops.py│117│⚡
D: ●json,modules,os,signal,subprocess,+1
F: _get_project_root()
   ↳Called by: F178:simulation_run
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F178:simulation_run]
F: simulation_run(input_data)→str
   ↳Calls: F178:_get_project_root
F: simulation_compare(input_data)→str
F: simulation_list(input_data)→str
F: simulation_get_signals(input_data)→str
---

F179│test_ops.py│80
S: Test execution tools: discover and run tests.
D: ●__future__,json,os,pathlib,subprocess,+1
F: _discover_test_files(root,pattern)→list[str]
   ↳Called by: F179:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F179:run_tests]
F: _run_pytest(paths,timeout)→str
   ↳Called by: F179:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F179:run_tests]
F: _run_unittest(paths,timeout)→str
   ↳Called by: F179:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F179:run_tests]
F: run_tests(input_data)→str
   ↳Calls: F154:resolve,F179:_run_pytest,F179:_discover_test_files
   S: Discover and run tests.
   S: input_data = {
   S: "pattern": "test_*.py",       # optional glob filter
   S: "path": "tests/",             # optional specific directory
   S: "framework": "pytest",        # optional: pytest (default) or unittest
---

F181│undo_ops.py│114
S: Checkpoint/undo system: save file snapshots before destructive edits.
D: ●__future__,hashlib,json,pathlib,shutil,+2
F: _ensure_checkpoint_dir()
   ↳Called by: F181:_load_index,F181:_save_index,F181:save_checkpoint
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F181:_load_index],[F181:_save_index],[F181:save_checkpoint]
F: _load_index()→list[dict]
   ↳Called by: F181:save_checkpoint,F181:checkpoint_info,F181:undo_last_edit | Calls: F181:_ensure_checkpoint_dir
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F181:save_checkpoint],[F181:checkpoint_info],[F181:undo_last_edit]
F: _save_index(index)
   ↳Called by: F181:save_checkpoint | Calls: F181:_ensure_checkpoint_dir
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:save_checkpoint]
F: _trim_index(index)
   ↳Called by: F181:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:save_checkpoint]
F: _hash_file(path)→str
   ↳Called by: F181:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:save_checkpoint]
F: save_checkpoint(file_path)→Any
   ↳Called by: F185:edit_file,F185:write_to_file | Calls: F181:_save_index,F181:_ensure_checkpoint_dir,F154:resolve
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F185:edit_file],[F185:write_to_file]
   S: Save a checkpoint of the given file before modifying it.
   S: Returns the checkpoint filename if saved, None if skipped.
F: undo_last_edit(file_path)→str
   ↳Calls: F154:resolve,F181:_load_index,F154:to_relative
   S: Restore the most recent checkpoint for a file, or the most recent overall.
   S: input_data = {"path": "optional/path"} — if omitted, returns latest checkpoint info.
F: checkpoint_info()→str
   ↳Calls: F181:_load_index
   S: Return summary of available checkpoints.
---
