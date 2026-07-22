# 📂 agent_core_1
Generated: 2026-07-21 18:31:40
Files: 10

---

F326│agent_loop.py│6
S: Shared agent tool loop — now lives in agent_core/loop/ package.
D: ●agent_core
---

F325│audit_log.py│65
D: ●__future__,hashlib,os,threading,typing,+3
C: AuditLog│[__init__,_init_db,log,query,close]
C: AuditLog│[__init__,_init_db,log,query,close]
   F: __init__(self,db_path)
   F: _init_db(self)
   F: log(self,user_id,tool,input_data,status)
   ↳Called by: F023:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F023:main]
   F: query(self,limit,offset)→list[dict]
   F: close(self)
---

F322│auto_research.py│75
S: Autonomous research mode using the shared agent loop.
D: ●__future__,agent_core,kernel,typing
F: run_auto_research(goal,orchestrator)→str
   ↳Calls: F346:log_output,F355:run_agent_turn
---

F324│config.py│48
S: Shared configuration and defaults for agent CLI and server.
D: ●__future__,json,os
F: load_config()→dict
F: get_provider_catalog()→Any
F: resolve_default_model(provider,explicit_model)→str
   ↳Called by: F320:build_orchestrator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F320:build_orchestrator]
F: resolve_active_provider()→str
---

F318│context.py│38
S: Kernel context retrieval for agent turns.
D: ●__future__,agent_core
F: retrieve_kernel_context(query)→str
   ↳Called by: F355:iter_agent_events | Calls: F346:log_output
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
   S: Return a markdown context block, or empty string if unavailable/disabled.
---

F321│mcp_server.py│114│⚡
S: MCP server exposing PIE kernel + simulation tools via stdio transport.
D: ●__future__,agent_core,mcp,os,typing,+4
F: _do_reload()
   ↳Called by: F321:_reload_if_changed | Calls: F346:_register_all
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F321:_reload_if_changed]
F: _reload_if_changed()
   ↳Called by: F321:list_mcp_tools,F321:call_mcp_tool | Calls: F321:_do_reload
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F321:list_mcp_tools],[F321:call_mcp_tool]
   S: Reload modules when source file mtime_ns has changed.
F: _build_tool_list()→list[Tool]
   ↳Called by: F321:list_mcp_tools
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F321:list_mcp_tools]
F: list_mcp_tools()→list[Tool]
   ↳Calls: F321:_build_tool_list,F321:_reload_if_changed
F: call_mcp_tool(name,arguments)→CallToolResult
   ↳Calls: F321:_reload_if_changed
F: main()
---

F323│prompts.py│99
S: System prompt assembly from capability-aware fragments.
D: ●__future__,agent_core,os,typing
F: load_agents_md()→str
   ↳Called by: F323:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F323:load_system_prompt]
F: build_tool_usage_table(tools_dict)→str
   ↳Called by: F323:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F323:load_system_prompt]
F: build_input_format_table(tools_dict)→str
   ↳Called by: F323:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F323:load_system_prompt]
F: _include_fragment(requires,blocks,active_packs)→bool
   ↳Called by: F323:load_system_prompt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F323:load_system_prompt]
F: load_system_prompt(tools_dict,path,active_packs)→str
   ↳Called by: F313:test_kernel_only_prompt_no_sim,F313:test_prompt_includes_only_active_tools_in_table,F313:test_full_prompt_has_file_tools | Calls: F346:log_output,F323:build_input_format_table,F323:_include_fragment
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F313:test_kernel_only_prompt_no_sim],[F313:test_prompt_includes_only_active_tools_in_table],[F313:test_full_prompt_has_file_tools]
---

F320│providers_setup.py│74
S: Register LLM providers from environment — single place for CLI and server.
D: ●__future__,agent_core,os,typing
F: build_orchestrator(default_provider,default_model)→Any
   ↳Calls: F324:resolve_default_model
   S: Build orchestrator and register available providers.
   S: Returns:
   S: (orchestrator, registered_providers, provider_models)
   S: registered_providers: [{"provider": name, "model": model}, ...]
   S: provider_models: {provider_name: model}
F: switch_active(orchestrator,provider,model)→Any
   S: Update orchestrator defaults. Caller must update its own active_* state.
---

F319│response_parse.py│145
S: Parse LLM replies into final answer or tool action.
D: ●__future__,dataclasses,json,re,typing
C: ParsedReply│[]
C: ParsedToolCall│[]
F: parse_provider_response(response_text,tool_calls_raw,known_tools)→ParsedReply
   ↳Called by: F355:iter_agent_events | Calls: F319:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
   S: Parse a provider response that may contain either text or structured tool_calls.
   S: Priority:
   S: 1. Structured tool_calls (native function calling) → multi-tool
   S: 2. Text-JSON {"action": ..., "input": ...} → single tool
   S: 3. Text-JSON {"final": ...} → final
F: parse_agent_reply(reply,known_tools)→ParsedReply
   ↳Called by: F319:parse_provider_response | Calls: F319:_extract_json,F319:_strip_code_fences,F319:_parse_xml_tool_call
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F319:parse_provider_response]
   S: Classify a model text reply:
   S: - final: {"final": "..."}
   S: - tool:  {"action": tool, "input": ...}
   S: - raw:   non-JSON or unparseable
   S: - invalid_tool: JSON action missing or not in TOOLS
F: _strip_code_fences(reply)→str
   ↳Called by: F319:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F319:parse_agent_reply]
F: _extract_json(text)
   ↳Called by: F319:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F319:parse_agent_reply]
F: _parse_xml_tool_call(text,known_tools)→Optional[ParsedReply]
   ↳Called by: F319:parse_agent_reply
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F319:parse_agent_reply]
C: ParsedReply│[]
C: ParsedToolCall│[]
---

F317│workspace.py│48
D: ●__future__,agent_core,os,threading
C: PathEscapeError←ValueError│[]
F: set_user_workspace(user_id)→str
F: get_user_workspace_root()→Any
   ↳Called by: F317:resolve,F317:to_relative,F346:_run_sandboxed
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F317:resolve],[F317:to_relative],[F346:_run_sandboxed]
F: clear_user_context()
F: resolve(path)→str
   ↳Called by: F344:undo_last_edit,F348:read_file,F348:read_file_range | Calls: F317:get_user_workspace_root
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F344:undo_last_edit],[F348:read_file],[F348:read_file_range]
F: to_relative(full_path)→str
   ↳Called by: F344:undo_last_edit,F348:read_file,F348:list_files | Calls: F317:get_user_workspace_root
   ↳Impact: 🔴HIGH (7 dependents) | Breaks: [F344:undo_last_edit],[F348:read_file],[F348:list_files]
C: PathEscapeError←ValueError│[]
---
