# 📂 tools_1
Generated: 2026-07-27 19:23:22
Files: 10

---

F178│audit_ops.py│36
D: ●json,kernel
F: emit_tool_compliance_signal(read_count,pie_count,kernel_read_count)→str
---

F185│context_dump.py│122
D: ●agent_core,json,os,pathlib,typing
F: _add_section(header,body,sections,max_tokens,used_tokens)→int
   ↳Called by: F185:minimal_context_dump
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F185:minimal_context_dump]
F: minimal_context_dump(params)→str
   ↳Calls: F185:_add_section,F194:_resolve_path,F194:_get_rag
---

F183│debate_ops.py│7
D: ●modules,os,sys
---

F179│kernel_ops.py│184
D: ●agent_core,importlib,json,kernel,sys
F: kernel_retrieve(input_data)→str
F: kernel_emit_signal(input_data)→str
F: kernel_store_context(input_data)→str
   ↳Calls: F029:generate_id,F036:generate_id,F035:generate_id
F: kernel_get_memory(input_data)→str
F: kernel_create_event(input_data)→str
F: kernel_reload(input_data)→str
   ↳Calls: F186:_register_all
   S: Reload tool modules from disk to pick up code changes without restart.
---

F180│observer_ops.py│64
D: ●json,kernel,time
F: tool_stats(params)→str
F: file_stats(params)→str
F: user_reading_budget(params)→str
---

F176│plan_ops.py│56
D: ●__future__,json,typing
F: _load_plan()→list[dict]
   ↳Called by: F176:todo_read,F176:todo_write
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F176:todo_read],[F176:todo_write]
F: _save_plan()
   ↳Called by: F176:todo_write
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F176:todo_write]
F: todo_write(input_data)→str
   ↳Calls: F176:_save_plan,F176:_load_plan
F: todo_read(_input)→str
   ↳Calls: F176:_load_plan
---

F177│question_ops.py│53
D: ●json,threading,typing
F: ask_user_question(raw_input)→str
F: resolve_all_questions(session_id,answers)→bool
   ↳Called by: F171:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F171:handle_chat]
F: cancel_questions(session_id)→bool
   ↳Called by: F171:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F171:handle_chat]
---

F181│sim_ops.py│117│⚡
D: ●json,modules,os,subprocess,sys,+1
F: _get_project_root()
   ↳Called by: F181:simulation_run
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:simulation_run]
F: simulation_run(input_data)→str
   ↳Calls: F181:_get_project_root
F: simulation_compare(input_data)→str
F: simulation_list(input_data)→str
F: simulation_get_signals(input_data)→str
---

F182│test_ops.py│80
S: Test execution tools: discover and run tests.
D: ●__future__,agent_core,json,pathlib,subprocess,+1
F: _discover_test_files(root,pattern)→list[str]
   ↳Called by: F182:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F182:run_tests]
F: _run_pytest(paths,timeout)→str
   ↳Called by: F182:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F182:run_tests]
F: _run_unittest(paths,timeout)→str
   ↳Called by: F182:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F182:run_tests]
F: run_tests(input_data)→str
   ↳Calls: F182:_discover_test_files,F182:_run_pytest,F182:_run_unittest
   S: Discover and run tests.
   S: input_data = {
   S: "pattern": "test_*.py",       # optional glob filter
   S: "path": "tests/",             # optional specific directory
   S: "framework": "pytest",        # optional: pytest (default) or unittest
---

F184│undo_ops.py│114
S: Checkpoint/undo system: save file snapshots before destructive edits.
D: ●__future__,agent_core,hashlib,json,pathlib,+2
F: _ensure_checkpoint_dir()
   ↳Called by: F184:_load_index,F184:save_checkpoint,F184:_save_index
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F184:_load_index],[F184:save_checkpoint],[F184:_save_index]
F: _load_index()→list[dict]
   ↳Called by: F184:undo_last_edit,F184:save_checkpoint,F184:checkpoint_info | Calls: F184:_ensure_checkpoint_dir
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F184:undo_last_edit],[F184:save_checkpoint],[F184:checkpoint_info]
F: _save_index(index)
   ↳Called by: F184:save_checkpoint | Calls: F184:_ensure_checkpoint_dir
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F184:save_checkpoint]
F: _trim_index(index)
   ↳Called by: F184:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F184:save_checkpoint]
F: _hash_file(path)→str
   ↳Called by: F184:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F184:save_checkpoint]
F: save_checkpoint(file_path)→Any
   ↳Called by: F188:edit_file,F188:write_to_file | Calls: F184:_save_index,F184:_load_index,F184:_ensure_checkpoint_dir
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F188:edit_file],[F188:write_to_file]
   S: Save a checkpoint of the given file before modifying it.
   S: Returns the checkpoint filename if saved, None if skipped.
F: undo_last_edit(file_path)→str
   ↳Calls: F184:_load_index,F155:to_relative,F155:resolve
   S: Restore the most recent checkpoint for a file, or the most recent overall.
   S: input_data = {"path": "optional/path"} — if omitted, returns latest checkpoint info.
F: checkpoint_info()→str
   ↳Calls: F184:_load_index
   S: Return summary of available checkpoints.
---
