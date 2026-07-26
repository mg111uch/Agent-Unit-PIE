# 📂 loop
Generated: 2026-07-26 16:20:18
Files: 6

---

F198│__init__.py│6
S: Agent loop — shared multi-step tool-calling loop.
D: ●agent_core
---

F195│_helpers.py│93
S: Shared helpers for the agent loop — extracted from engine.py to reduce file size.
D: ●__future__,agent_core,json,threading,typing
F: _truncate_result(result,max_chars)→str
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: _compact_corrective_exchange(messages)→list
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: _run_interactive_tool(tool_name,tool_args,tools,session_id)→Any
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: _handle_corrective_bookkeeping(use_messages,current_messages,current_input,msg_store,session_id,tool_name,corrective,followup)→str
   ↳Called by: F199:iter_agent_events | Calls: F197:build_corrective_msg
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: _generate_with_cancel(orchestrator,cancel_event)→Optional[dict]
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
   S: Run orchestrator.generate() in a daemon thread, signalling stop_flag on cancel.
---

F199│engine.py│483
S: Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket.
D: ●__future__,json,threading,time,traceback,+2
F: iter_agent_events(user_input,orchestrator)→Any
   ↳Called by: F199:run_agent_turn | Calls: F197:build_tool_calls_msg,F196:execute_tool_calls,F195:_truncate_result
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:run_agent_turn]
F: run_agent_turn(user_input,orchestrator)→Any
   ↳Called by: F160:run_auto_research | Calls: F199:iter_agent_events,F185:log_output
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F160:run_auto_research]
---

F196│executor.py│121
S: Tool call executor — runs tool calls and collects results.
D: ●__future__,agent_core,threading,typing
F: _normalize_tool_arg(name,arguments)→Any
   ↳Called by: F159:call_mcp_tool,F196:execute_tool_calls
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F159:call_mcp_tool],[F196:execute_tool_calls]
F: execute_tool_calls(calls,step,tools,cancel_event)→List[dict]
   ↳Called by: F199:iter_agent_events | Calls: F196:_normalize_tool_arg
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
---

F197│messages.py│71
S: Message builder helpers for the agent loop.
D: ●__future__,agent_core,json,typing
F: tool_followup(tool,tool_input,tool_result)→str
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: serialize_tool_input(tool_input)→str
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: build_tool_calls_msg(tool_calls)→dict
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: build_tool_results_msg(results)→dict
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: build_single_tool_result_msg(tool,result_str,call_id)→dict
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: build_corrective_msg(text)→dict
   ↳Called by: F195:_handle_corrective_bookkeeping
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:_handle_corrective_bookkeeping]
---

F194│streaming.py│109
S: Streaming helpers for the agent loop — real provider streaming with fake-chunk fallback.
D: ●__future__,threading,typing
F: stream_final(content,step,conversation_id,orchestrator)→Any
   ↳Called by: F199:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F199:iter_agent_events]
F: stream_llm_response(orchestrator)→Any
---
