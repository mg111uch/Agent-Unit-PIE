# 📂 agent_core_1
Generated: 2026-07-23 14:15:38
Files: 10

---

F163│agent_loop.py│6
S: Shared agent tool loop — now lives in agent_core/loop/ package.
D: ●agent_core
---

F162│audit_log.py│69
D: ●__future__,hashlib,json,pathlib,threading,+4
C: AuditLog│[__init__,_init_db,log,query,close]
C: AuditLog│[__init__,_init_db,log,query,close]
   F: __init__(self,db_path)
   F: _init_db(self)
   F: log(self,user_id,tool,input_data,status)
   F: query(self,limit,offset)→list[dict]
   F: close(self)
---

F159│auto_research.py│75
S: Autonomous research mode using the shared agent loop.
D: ●__future__,agent_core,kernel,typing
F: run_auto_research(goal,orchestrator)→str
   ↳Calls: F183:log_output,F195:run_agent_turn
---

F161│config.py│48
S: Shared configuration and defaults for agent CLI and server.
D: ●__future__,json,os
F: load_config()→dict
F: get_provider_catalog()→Any
F: resolve_default_model(provider,explicit_model)→str
   ↳Called by: F157:build_orchestrator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F157:build_orchestrator]
F: resolve_active_provider()→str
---

F155│context.py│38
S: Kernel context retrieval for agent turns.
D: ●__future__,agent_core
F: retrieve_kernel_context(query)→str
   ↳Called by: F195:iter_agent_events | Calls: F183:log_output
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
   S: Return a markdown context block, or empty string if unavailable/disabled.
---

F158│mcp_server.py│143│⚡
S: MCP server exposing PIE kernel + simulation tools via stdio transport.
D: ●__future__,importlib,json,mcp,pathlib,+6
F: _do_reload()
   ↳Called by: F158:_reload_if_changed | Calls: F183:_register_all
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F158:_reload_if_changed]
F: _reload_if_changed()
   ↳Called by: F158:call_mcp_tool,F158:list_mcp_tools | Calls: F158:_do_reload
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F158:call_mcp_tool],[F158:list_mcp_tools]
   S: Reload all tool modules when any .py file under _WATCH_DIR changes.
F: _check_kernel_read(name,arguments)→Any
   ↳Called by: F158:call_mcp_tool | Calls: F154:resolve
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F158:call_mcp_tool]
   S: Return warning message if this is a Read call on a kernel file, else None.
F: _build_tool_list()→list[Tool]
   ↳Called by: F158:list_mcp_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F158:list_mcp_tools]
F: list_mcp_tools()→list[Tool]
   ↳Calls: F158:_reload_if_changed,F158:_build_tool_list
F: call_mcp_tool(name,arguments)→CallToolResult
   ↳Calls: F158:_check_kernel_read,F158:_reload_if_changed
F: main()
---

F160│prompts.py│99
S: System prompt assembly from capability-aware fragments.
D: ●__future__,agent_core,os,typing
F: load_agents_md()→str
   ↳Called by: F160:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F160:load_system_prompt]
F: build_tool_usage_table(tools_dict)→str
   ↳Called by: F160:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F160:load_system_prompt]
F: build_input_format_table(tools_dict)→str
   ↳Called by: F160:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F160:load_system_prompt]
F: _include_fragment(requires,blocks,active_packs)→bool
   ↳Called by: F160:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F160:load_system_prompt]
F: load_system_prompt(tools_dict,path,active_packs)→str
   ↳Calls: F160:build_tool_usage_table,F160:_include_fragment,F160:build_input_format_table
---

F157│providers_setup.py│74
S: Register LLM providers from environment — single place for CLI and server.
D: ●__future__,agent_core,os,typing
F: build_orchestrator(default_provider,default_model)→Any
   ↳Called by: F138:_get_orchestrator | Calls: F161:resolve_default_model
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F138:_get_orchestrator]
   S: Build orchestrator and register available providers.
   S: Returns:
   S: (orchestrator, registered_providers, provider_models)
   S: registered_providers: [{"provider": name, "model": model}, ...]
   S: provider_models: {provider_name: model}
F: switch_active(orchestrator,provider,model)→Any
   S: Update orchestrator defaults. Caller must update its own active_* state.
---

F156│response_parse.py│145
S: Parse LLM replies into final answer or tool action.
D: ●__future__,dataclasses,json,re,typing
C: ParsedReply│[]
C: ParsedToolCall│[]
F: parse_provider_response(response_text,tool_calls_raw,known_tools)→ParsedReply
   ↳Called by: F195:iter_agent_events | Calls: F156:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
   S: Parse a provider response that may contain either text or structured tool_calls.
   S: Priority:
   S: 1. Structured tool_calls (native function calling) → multi-tool
   S: 2. Text-JSON {"action": ..., "input": ...} → single tool
   S: 3. Text-JSON {"final": ...} → final
F: parse_agent_reply(reply,known_tools)→ParsedReply
   ↳Called by: F156:parse_provider_response | Calls: F156:_parse_xml_tool_call,F156:_strip_code_fences,F156:_extract_json
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F156:parse_provider_response]
   S: Classify a model text reply:
   S: - final: {"final": "..."}
   S: - tool:  {"action": tool, "input": ...}
   S: - raw:   non-JSON or unparseable
   S: - invalid_tool: JSON action missing or not in TOOLS
F: _strip_code_fences(reply)→str
   ↳Called by: F156:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F156:parse_agent_reply]
F: _extract_json(text)
   ↳Called by: F156:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F156:parse_agent_reply]
F: _parse_xml_tool_call(text,known_tools)→Optional[ParsedReply]
   ↳Called by: F156:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F156:parse_agent_reply]
C: ParsedReply│[]
C: ParsedToolCall│[]
---

F154│workspace.py│48
D: ●__future__,agent_core,os,threading
C: PathEscapeError←ValueError│[]
F: set_user_workspace(user_id)→str
F: get_user_workspace_root()→Any
   ↳Called by: F154:resolve,F183:_run_sandboxed,F154:to_relative
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F154:resolve],[F183:_run_sandboxed],[F154:to_relative]
F: clear_user_context()
F: resolve(path)→str
   ↳Called by: F181:save_checkpoint,F181:undo_last_edit,F185:list_files | Calls: F154:get_user_workspace_root
   ↳Impact: 🔴HIGH (10 dependents) | Breaks: [F181:save_checkpoint],[F181:undo_last_edit],[F185:list_files]
F: to_relative(full_path)→str
   ↳Called by: F181:save_checkpoint,F181:undo_last_edit,F185:list_files | Calls: F154:get_user_workspace_root
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F181:save_checkpoint],[F181:undo_last_edit],[F185:list_files]
C: PathEscapeError←ValueError│[]
---
