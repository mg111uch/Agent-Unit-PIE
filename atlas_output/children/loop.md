# 📂 loop
Generated: 2026-07-21 18:31:40
Files: 5

---

F354│__init__.py│6
S: Agent loop — shared multi-step tool-calling loop.
D: ●agent_core
---

F355│engine.py│542
S: Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket.
D: ●__future__,agent_core,time,traceback,typing,+3
F: _generate_with_cancel(orchestrator,cancel_event)→Optional[dict]
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
   S: Run orchestrator.generate() in a thread, polling cancel_event every 500ms.
F: iter_agent_events(user_input,orchestrator)→Any
   ↳Called by: F355:run_agent_turn | Calls: F353:build_tool_results_msg,F352:execute_tool_calls,F318:retrieve_kernel_context
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:run_agent_turn]
F: run_agent_turn(user_input,orchestrator)→Any
   ↳Called by: F322:run_auto_research | Calls: F355:iter_agent_events,F346:log_output
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F322:run_auto_research]
---

F352│executor.py│117
S: Tool call executor — runs tool calls and collects results.
D: ●__future__,agent_core,threading,typing
F: _normalize_tool_arg(name,arguments)→Any
   ↳Called by: F352:execute_tool_calls
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F352:execute_tool_calls]
F: execute_tool_calls(calls,step,tools,cancel_event)→List[dict]
   ↳Called by: F355:iter_agent_events | Calls: F352:_normalize_tool_arg
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
---

F353│messages.py│71
S: Message builder helpers for the agent loop.
D: ●__future__,agent_core,json,typing
F: tool_followup(tool,tool_input,tool_result)→str
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
F: serialize_tool_input(tool_input)→str
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
F: build_tool_calls_msg(tool_calls)→dict
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
F: build_tool_results_msg(results)→dict
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
F: build_single_tool_result_msg(tool,result_str,call_id)→dict
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
F: build_corrective_msg(text)→dict
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
---

F351│streaming.py│84
S: Streaming helpers for the agent loop — real provider streaming with fake-chunk fallback.
D: ●__future__,time,typing
F: stream_final(content,step,conversation_id,orchestrator)→Any
   ↳Called by: F355:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F355:iter_agent_events]
F: stream_llm_response(orchestrator)→Any
---
