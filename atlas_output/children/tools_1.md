# 📂 tools_1
Generated: 2026-07-26 16:20:18
Files: 10

---

F177│audit_ops.py│36
D: ●json,kernel
F: emit_tool_compliance_signal(read_count,pie_count,kernel_read_count)→str
---

F184│context_dump.py│122
D: ●agent_core,json,os,pathlib,typing
F: _add_section(header,body,sections,max_tokens,used_tokens)→int
   ↳Called by: F184:minimal_context_dump
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F184:minimal_context_dump]
F: minimal_context_dump(params)→str
   ↳Calls: F193:_resolve_path,F184:_add_section,F193:_get_rag
---

F182│debate_ops.py│7
D: ●modules,os,sys
---

F178│kernel_ops.py│184
D: ●agent_core,importlib,json,kernel,sys
F: kernel_retrieve(input_data)→str
F: kernel_emit_signal(input_data)→str
F: kernel_store_context(input_data)→str
   ↳Calls: F036:generate_id,F033:generate_id,F035:generate_id
F: kernel_get_memory(input_data)→str
F: kernel_create_event(input_data)→str
F: kernel_reload(input_data)→str
   ↳Calls: F185:_register_all
   S: Reload tool modules from disk to pick up code changes without restart.
---

F179│observer_ops.py│64
D: ●json,kernel,time
F: tool_stats(params)→str
F: file_stats(params)→str
F: user_reading_budget(params)→str
---

F175│plan_ops.py│56
D: ●__future__,json,typing
F: _load_plan()→list[dict]
   ↳Called by: F175:todo_read,F175:todo_write
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F175:todo_read],[F175:todo_write]
F: _save_plan()
   ↳Called by: F175:todo_write
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F175:todo_write]
F: todo_write(input_data)→str
   ↳Calls: F175:_save_plan,F175:_load_plan
F: todo_read(_input)→str
   ↳Calls: F175:_load_plan
---

F176│question_ops.py│53
D: ●json,threading,typing
F: ask_user_question(raw_input)→str
F: resolve_all_questions(session_id,answers)→bool
   ↳Called by: F170:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F170:handle_chat]
F: cancel_questions(session_id)→bool
   ↳Called by: F170:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F170:handle_chat]
---

F180│sim_ops.py│117│⚡
D: ●json,modules,os,signal,subprocess,+1
F: _get_project_root()
   ↳Called by: F180:simulation_run
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F180:simulation_run]
F: simulation_run(input_data)→str
   ↳Calls: F180:_get_project_root
F: simulation_compare(input_data)→str
F: simulation_list(input_data)→str
F: simulation_get_signals(input_data)→str
---

F181│test_ops.py│80
S: Test execution tools: discover and run tests.
D: ●__future__,agent_core,json,os,subprocess,+1
F: _discover_test_files(root,pattern)→list[str]
   ↳Called by: F181:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:run_tests]
F: _run_pytest(paths,timeout)→str
   ↳Called by: F181:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:run_tests]
F: _run_unittest(paths,timeout)→str
   ↳Called by: F181:run_tests
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F181:run_tests]
F: run_tests(input_data)→str
   ↳Calls: F181:_discover_test_files,F181:_run_unittest,F181:_run_pytest
   S: Discover and run tests.
   S: input_data = {
   S: "pattern": "test_*.py",       # optional glob filter
   S: "path": "tests/",             # optional specific directory
   S: "framework": "pytest",        # optional: pytest (default) or unittest
---

F183│undo_ops.py│114
S: Checkpoint/undo system: save file snapshots before destructive edits.
D: ●__future__,agent_core,hashlib,json,os,+2
F: _ensure_checkpoint_dir()
   ↳Called by: F183:_save_index,F183:save_checkpoint,F183:_load_index
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F183:_save_index],[F183:save_checkpoint],[F183:_load_index]
F: _load_index()→list[dict]
   ↳Called by: F183:undo_last_edit,F183:save_checkpoint,F183:checkpoint_info | Calls: F183:_ensure_checkpoint_dir
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F183:undo_last_edit],[F183:save_checkpoint],[F183:checkpoint_info]
F: _save_index(index)
   ↳Called by: F183:save_checkpoint | Calls: F183:_ensure_checkpoint_dir
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:save_checkpoint]
F: _trim_index(index)
   ↳Called by: F183:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:save_checkpoint]
F: _hash_file(path)→str
   ↳Called by: F183:save_checkpoint
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F183:save_checkpoint]
F: save_checkpoint(file_path)→Any
   ↳Called by: F187:write_to_file,F187:edit_file | Calls: F183:_ensure_checkpoint_dir,F183:_trim_index,F155:to_relative
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F187:write_to_file],[F187:edit_file]
   S: Save a checkpoint of the given file before modifying it.
   S: Returns the checkpoint filename if saved, None if skipped.
F: undo_last_edit(file_path)→str
   ↳Calls: F155:to_relative,F155:resolve,F183:_load_index
   S: Restore the most recent checkpoint for a file, or the most recent overall.
   S: input_data = {"path": "optional/path"} — if omitted, returns latest checkpoint info.
F: checkpoint_info()→str
   ↳Calls: F183:_load_index
   S: Return summary of available checkpoints.
---
