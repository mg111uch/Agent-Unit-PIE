# 📂 codebase
Generated: 2026-06-01 13:39:55
Files: 3

---

F003│__init__.py│1
---

F002│agent.py│236│⚡
S: agent.py - Main agent entry point.
D: ►F001 ●dotenv,kernel,os,sys,traceback,+5
C: TeeStderr│[__init__,write,flush]
F: parse_command(user_input)
F: run_agent(user_input)→str
   ↳Calls: F001:extract_json,F001:log_output
F: run_auto_research(goal,max_iterations)→str
   ↳Calls: F001:extract_json,F001:log_output
   S: Autonomous research mode: Goal -> Plan -> Execute -> Learn -> Repeat
---

F001│agent_tools.py│479
S: agent_tools.py - Tool definitions for agent.
D: ●datetime,kernel,os,subprocess,typing,+3
F: log_output(message,end,flush)
   ↳Called by: F002:run_auto_research,F002:run_agent,F001:list_files
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F002:run_auto_research],[F002:run_agent],[F001:list_files]
   S: Write message to both terminal and log file with timestamp
F: extract_json(text)
   ↳Called by: F002:run_agent,F002:run_auto_research
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F002:run_agent],[F002:run_auto_research]
   S: Extract JSON from text
F: _resolve_path(path)→str
   ↳Called by: F001:write_to_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:write_to_file]
   S: Resolve path relative to BASE_DIR
F: _ensure_dir(path)
   ↳Called by: F001:write_to_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:write_to_file]
   S: Ensure directory exists
F: read_file(path)→str
   S: Read file contents
F: list_files(path)→str
   ↳Calls: F001:log_output
   S: List files in directory
F: write_to_file(input_data)→str
   ↳Calls: F001:_ensure_dir,F001:_resolve_path
   S: Write to file with modes: create, overwrite, append, patch
   S: input_data = {
   S: "path": "relative/path.txt",
   S: "mode": "create|overwrite|append|patch",
   S: "content": "string (optional)",
F: execute_command(cmd)→str
   ↳Calls: F001:log_output
   S: Execute allowed shell commands
F: kernel_retrieve(input_data)→str
   S: Retrieve relevant context from kernel memory layers.
   S: Input: {"query": "search terms", "limit": 10}
   S: Returns: relevant memories, patterns, and timeline from all memory layers.
F: kernel_emit_signal(input_data)→str
   S: Emit a signal to the kernel for observation/finding.
   S: Input: {
   S: "signal_type": "observation|finding|insight",
   S: "value": "any value",
   S: "title": "signal title",
F: kernel_store_context(input_data)→str
   ↳Calls: F030:generate_id,F033:generate_id,F032:generate_id
   S: Store context in working memory for later retrieval.
   S: Input: {
   S: "memory_id": "unique_id (optional, auto-generated if not provided)",
   S: "memory_type": "context|observation|hypothesis|summary",
   S: "content": "any content to store",
F: kernel_get_memory(input_data)→str
   S: Retrieve specific memory from working memory.
   S: Input: {
   S: "memory_id": "memory ID to retrieve"
   S: }
   S: Returns: Memory content or error.
F: kernel_create_event(input_data)→str
   S: Create an event from agent action.
   S: Input: {
   S: "event_type": "action|discovery|decision|error",
   S: "title": "event title",
   S: "description": "what happened",
F: simulation_run(input_data)→str
   S: Run simulation and extract signals.
   S: Input: {
   S: "params": {...},    # simulation parameters (optional, uses defaults)
   S: "run_id": "unique_id"   # required
   S: }
F: simulation_compare(input_data)→str
   S: Compare simulation runs.
   S: Input: {
   S: "run_ids": ["run_001", "run_002"]
   S: }
   S: Returns: Comparison table.
F: simulation_list(input_data)→str
   S: List simulation runs.
   S: Input: {}  (no params needed)
   S: Returns: List of run IDs.
F: simulation_get_signals(input_data)→str
   S: Get signals from a simulation run.
   S: Input: {
   S: "run_id": "run_001"
   S: }
   S: Returns: Signals list.
---
