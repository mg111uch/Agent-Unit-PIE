# 📂 loop
Generated: 2026-07-23 14:15:38
Files: 5

---

F194│__init__.py│6
S: Agent loop — shared multi-step tool-calling loop.
D: ●agent_core
---

F195│engine.py│542
S: Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket.
D: ●__future__,concurrent,json,threading,traceback,+3
F: _generate_with_cancel(orchestrator,cancel_event)→Optional[dict]
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
   S: Run orchestrator.generate() in a thread, polling cancel_event every 500ms.
F: iter_agent_events(user_input,orchestrator)→Any
   ↳Called by: F195:run_agent_turn | Calls: F193:build_tool_calls_msg,F193:build_tool_results_msg,F192:execute_tool_calls
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:run_agent_turn]
F: run_agent_turn(user_input,orchestrator)→Any
   ↳Called by: F159:run_auto_research | Calls: F183:log_output,F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F159:run_auto_research]
---

F192│executor.py│117
S: Tool call executor — runs tool calls and collects results.
D: ●__future__,agent_core,threading,typing
F: _normalize_tool_arg(name,arguments)→Any
   ↳Called by: F192:execute_tool_calls
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F192:execute_tool_calls]
F: execute_tool_calls(calls,step,tools,cancel_event)→List[dict]
   ↳Called by: F195:iter_agent_events | Calls: F192:_normalize_tool_arg
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
---

F193│messages.py│71
S: Message builder helpers for the agent loop.
D: ●__future__,agent_core,json,typing
F: tool_followup(tool,tool_input,tool_result)→str
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
F: serialize_tool_input(tool_input)→str
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
F: build_tool_calls_msg(tool_calls)→dict
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
F: build_tool_results_msg(results)→dict
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
F: build_single_tool_result_msg(tool,result_str,call_id)→dict
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
F: build_corrective_msg(text)→dict
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
---

F191│streaming.py│84
S: Streaming helpers for the agent loop — real provider streaming with fake-chunk fallback.
D: ●__future__,time,typing
F: stream_final(content,step,conversation_id,orchestrator)→Any
   ↳Called by: F195:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F195:iter_agent_events]
F: stream_llm_response(orchestrator)→Any
---
