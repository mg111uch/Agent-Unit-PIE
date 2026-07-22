# 📂 tools_1
Generated: 2026-07-21 18:31:40
Files: 10

---

F346│__init__.py│380
D: ●agent_core,os,re,subprocess,typing,+2
C: ToolError←Exception│[__init__]
C: ToolResult│[to_string,to_dict]
F: tool_call(fn)→Callable
   S: Wrap a tool function to catch ToolErrors and return structured ToolResult.
F: log_output(message,end,flush)
   ↳Called by: F318:retrieve_kernel_context,F323:load_system_prompt,F322:run_auto_research
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F318:retrieve_kernel_context],[F323:load_system_prompt],[F322:run_auto_research]
F: extract_json(text)
F: _is_command_allowed(cmd)→bool
   ↳Called by: F346:execute_command_raw
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F346:execute_command_raw]
F: _run_sandboxed(cmd,timeout)→str
   ↳Called by: F346:execute_command_raw | Calls: F317:get_user_workspace_root
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F346:execute_command_raw]
F: execute_command_raw(cmd)→str
   ↳Calls: F346:_is_command_allowed,F346:_run_sandboxed,F346:log_output
F: _register_all()
   ↳Called by: F321:_do_reload,F340:kernel_reload
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F321:_do_reload],[F340:kernel_reload]
C: ToolError←Exception│[__init__]
   F: __init__(self,error_type,message,suggestion)
C: ToolResult│[to_string,to_dict]
   F: to_string(self)→str
   F: to_dict(self)→dict
---

F339│code_rag.py│553
D: ●agent_core,os,pathlib,sqlite3,typing,+1
C: CodeRAG│[__init__,_get_conn,ensure_indexed,needs_index,get_symbol,get_symbols,search_symbols,get_callers_callees,get_symbols_meta,find_impact,+5]
F: _resolve_path(path)→str
   ↳Called by: F339:compare_apis_tool,F339:file_api_tool,F339:symbols_by_file_tool
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F339:compare_apis_tool],[F339:file_api_tool],[F339:symbols_by_file_tool]
F: _get_rag()→Optional[CodeRAG]
   ↳Called by: F339:get_index_info_tool,F339:call_chain_tool,F339:compare_apis_tool
   ↳Impact: 🔴HIGH (10 dependents) | Breaks: [F339:get_index_info_tool],[F339:call_chain_tool],[F339:compare_apis_tool]
F: get_symbol_tool(params)→str
   ↳Calls: F339:_get_rag
F: get_symbols_meta_tool(params)→str
   ↳Calls: F339:_get_rag
F: search_symbols_tool(params)→str
   ↳Calls: F339:_get_rag
   S: Metadata-only search. Does not prefetch definitions (avoids bloating with unrelated hits).
F: get_callers_callees_tool(params)→str
   ↳Calls: F339:_get_rag
F: find_impact_tool(params)→str
   ↳Calls: F339:_get_rag
F: get_index_info_tool(params)→str
   ↳Calls: F339:_get_rag
F: file_api_tool(params)→str
   ↳Calls: F339:_resolve_path,F339:_get_rag
F: call_chain_tool(params)→str
   ↳Calls: F339:_get_rag
F: compare_apis_tool(params)→str
   ↳Calls: F339:_resolve_path,F339:_get_rag
F: symbols_by_file_tool(params)→str
   ↳Calls: F339:_resolve_path,F339:_get_rag
C: CodeRAG│[__init__,_get_conn,ensure_indexed,needs_index,get_symbol,get_symbols,search_symbols,get_callers_callees,get_symbols_meta,find_impact,+5]
   F: __init__(self,atlas_dir)
   F: _get_conn(self)→sqlite3.Connection
   F: ensure_indexed(self)→bool
   F: needs_index(self)→bool
   F: get_symbol(self,name,file_path,parent_name)→Any
   F: get_symbols(self,names,file_path)→Any
   F: search_symbols(self,query,type_filter,top_k)→Any
   F: get_callers_callees(self,name,file_path,depth,direction)→Any
   F: get_symbols_meta(self,names,file_path)→Any
   F: find_impact(self,name,file_path)→Any
   F: get_index_info(self)→Any
   F: file_api(self,path)→Any
   F: call_chain(self,start_fn,end_module,file_path)→Any
   F: compare_apis(self,path_a,path_b)→Any
   F: symbols_by_file(self,path)→Any
---

F343│debate_ops.py│7
D: ●modules,os,sys
---

F340│kernel_ops.py│186
D: ●agent_core,importlib,json,kernel,sys
F: kernel_retrieve(input_data)→str
F: kernel_emit_signal(input_data)→str
F: kernel_store_context(input_data)→str
   ↳Calls: F073:generate_id,F074:generate_id,F076:generate_id
F: kernel_get_memory(input_data)→str
F: kernel_create_event(input_data)→str
F: kernel_reload(input_data)→str
   ↳Calls: F346:_register_all
   S: Reload tool modules from disk to pick up code changes without restart.
---

F337│plan_ops.py│56
D: ●__future__,json,typing
F: _load_plan()→list[dict]
   ↳Called by: F337:todo_read,F337:todo_write
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F337:todo_read],[F337:todo_write]
F: _save_plan()
   ↳Called by: F337:todo_write
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F337:todo_write]
F: todo_write(input_data)→str
   ↳Calls: F337:_save_plan,F337:_load_plan
F: todo_read(_input)→str
   ↳Calls: F337:_load_plan
---

F338│question_ops.py│53
D: ●json,threading,typing
F: ask_user_question(raw_input)→str
F: resolve_all_questions(session_id,answers)→bool
   ↳Called by: F332:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F332:handle_chat]
F: cancel_questions(session_id)→bool
   ↳Called by: F332:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F332:handle_chat]
---

F345│schemas.py│540
D: ●__future__,typing
F: _str_schema(description)→dict
F: _obj_schema(properties,required)→dict
F: schemas_for_provider(provider_type)→Any
---

F341│sim_ops.py│117│⚡
D: ●json,modules,os,subprocess,sys,+1
F: _get_project_root()
   ↳Called by: F341:simulation_run
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F341:simulation_run]
F: simulation_run(input_data)→str
   ↳Calls: F341:_get_project_root
F: simulation_compare(input_data)→str
F: simulation_list(input_data)→str
F: simulation_get_signals(input_data)→str
---

F342│test_ops.py│80
S: Test execution tools: discover and run tests.
D: ●__future__,agent_core,os,pathlib,subprocess,+1
F: _discover_test_files(root,pattern)→list[str]
   ↳Called by: F342:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F342:run_tests]
F: _run_pytest(paths,timeout)→str
   ↳Called by: F342:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F342:run_tests]
F: _run_unittest(paths,timeout)→str
   ↳Called by: F342:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F342:run_tests]
F: run_tests(input_data)→str
   ↳Calls: F342:_run_unittest,F317:resolve,F342:_discover_test_files
   S: Discover and run tests.
   S: input_data = {
   S: "pattern": "test_*.py",       # optional glob filter
   S: "path": "tests/",             # optional specific directory
   S: "framework": "pytest",        # optional: pytest (default) or unittest
---

F344│undo_ops.py│114
S: Checkpoint/undo system: save file snapshots before destructive edits.
D: ●__future__,agent_core,hashlib,pathlib,shutil,+2
F: _ensure_checkpoint_dir()
   ↳Called by: F344:_load_index,F344:save_checkpoint,F344:_save_index
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F344:_load_index],[F344:save_checkpoint],[F344:_save_index]
F: _load_index()→list[dict]
   ↳Called by: F344:save_checkpoint,F344:undo_last_edit,F344:checkpoint_info | Calls: F344:_ensure_checkpoint_dir
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F344:save_checkpoint],[F344:undo_last_edit],[F344:checkpoint_info]
F: _save_index(index)
   ↳Called by: F344:save_checkpoint | Calls: F344:_ensure_checkpoint_dir
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F344:save_checkpoint]
F: _trim_index(index)
   ↳Called by: F344:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F344:save_checkpoint]
F: _hash_file(path)→str
   ↳Called by: F344:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F344:save_checkpoint]
F: save_checkpoint(file_path)→Any
   ↳Called by: F348:edit_file,F348:write_to_file | Calls: F317:resolve,F317:to_relative,F344:_load_index
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F348:edit_file],[F348:write_to_file]
   S: Save a checkpoint of the given file before modifying it.
   S: Returns the checkpoint filename if saved, None if skipped.
F: undo_last_edit(file_path)→str
   ↳Calls: F317:resolve,F317:to_relative,F344:_load_index
   S: Restore the most recent checkpoint for a file, or the most recent overall.
   S: input_data = {"path": "optional/path"} — if omitted, returns latest checkpoint info.
F: checkpoint_info()→str
   ↳Calls: F344:_load_index
   S: Return summary of available checkpoints.
---
