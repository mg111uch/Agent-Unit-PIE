# 📂 loop
Generated: 2026-07-27 19:23:22
Files: 7

---

F199│__init__.py│6
S: Agent loop — shared multi-step tool-calling loop.
D: ●agent_core
---

F196│_helpers.py│93
S: Shared helpers for the agent loop — extracted from engine.py to reduce file size.
D: ●__future__,agent_core,json,threading,typing
F: _truncate_result(result,max_chars)→str
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: _compact_corrective_exchange(messages)→list
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: _run_interactive_tool(tool_name,tool_args,tools,session_id)→Any
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: _handle_corrective_bookkeeping(use_messages,current_messages,current_input,msg_store,session_id,tool_name,corrective,followup)→str
   ↳Called by: F201:_iter_agent_events_body | Calls: F198:build_corrective_msg
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: _generate_with_cancel(orchestrator,cancel_event)→Optional[dict]
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
   S: Run orchestrator.generate() in a daemon thread, signalling stop_flag on cancel.
---

F201│engine.py│637
S: Agent loop engine — multi-step tool-calling loop shared by CLI and WebSocket.
D: ●__future__,agent_core,json,threading,traceback,+3
F: _debug_dump(mode)
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: iter_agent_events(user_input,orchestrator)→Any
   ↳Called by: F201:run_agent_turn | Calls: F200:reset_session_state,F200:set_session_state,F156:retrieve_kernel_context
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:run_agent_turn]
F: _iter_agent_events_body()→Any
   ↳Called by: F201:iter_agent_events | Calls: F196:_truncate_result,F195:stream_final,F157:parse_provider_response
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:iter_agent_events]
F: run_agent_turn(user_input,orchestrator)→Any
   ↳Called by: F160:run_auto_research | Calls: F201:iter_agent_events,F186:log_output
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F160:run_auto_research]
---

F197│executor.py│121
S: Tool call executor — runs tool calls and collects results.
D: ●__future__,agent_core,threading,typing
F: _normalize_tool_arg(name,arguments)→Any
   ↳Called by: F197:execute_tool_calls,F159:call_mcp_tool
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F197:execute_tool_calls],[F159:call_mcp_tool]
F: execute_tool_calls(calls,step,tools,cancel_event)→List[dict]
   ↳Called by: F201:_iter_agent_events_body | Calls: F197:_normalize_tool_arg
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
---

F198│messages.py│71
S: Message builder helpers for the agent loop.
D: ●__future__,agent_core,json,typing
F: tool_followup(tool,tool_input,tool_result)→str
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: serialize_tool_input(tool_input)→str
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: build_tool_calls_msg(tool_calls)→dict
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: build_tool_results_msg(results)→dict
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: build_single_tool_result_msg(tool,result_str,call_id)→dict
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: build_corrective_msg(text)→dict
   ↳Called by: F196:_handle_corrective_bookkeeping
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F196:_handle_corrective_bookkeeping]
---

F200│session_state.py│253
S: Cross-turn session state: file cache, workspace digest, message compaction.
D: ●__future__,ast,contextvars,dataclasses,hashlib,+2
C: FileCacheEntry│[]
C: SessionState│[begin_turn,note_tool_call,build_digest,set_workspace,get_cached_file,put_file,mark_stale,record_edit,record_outcome,history_summary]
F: get_session_state()→Optional[SessionState]
   ↳Called by: F188:get_workspace_info,F188:edit_file,F188:read_file
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F188:get_workspace_info],[F188:edit_file],[F188:read_file]
F: set_session_state(state)
   ↳Called by: F201:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:iter_agent_events]
F: reset_session_state(token)→None
   ↳Called by: F201:iter_agent_events
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:iter_agent_events]
F: estimate_message_chars(messages)→int
   ↳Called by: F200:compact_messages
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F200:compact_messages]
F: compact_messages(messages,state,trigger_chars,keep_tail)→list[dict]
   ↳Called by: F201:_iter_agent_events_body | Calls: F200:estimate_message_chars,F200:_shrink_tool_payloads
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
   S: Rule-based compaction: shrink old tool results when history grows large.
F: _shrink_tool_payloads(messages)→list[dict]
   ↳Called by: F200:compact_messages
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F200:compact_messages]
F: observe_tool_result(state,tool,arguments,result,ok)→None
   ↳Calls: F200:_parse_workspace_info,F200:_is_partial_read,F200:_extract_path
   S: Update caches from a completed tool call.
F: _extract_path(arguments)→Optional[str]
   ↳Called by: F200:observe_tool_result
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F200:observe_tool_result]
F: _is_partial_read(arguments)→bool
   ↳Called by: F200:observe_tool_result
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F200:observe_tool_result]
F: _parse_workspace_info(text)→Any
   ↳Called by: F200:observe_tool_result
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F200:observe_tool_result]
F: _parse_todo(arguments)→Any
   ↳Called by: F200:observe_tool_result
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F200:observe_tool_result]
C: FileCacheEntry│[]
C: SessionState│[begin_turn,note_tool_call,build_digest,set_workspace,get_cached_file,put_file,mark_stale,record_edit,record_outcome,history_summary]
   F: begin_turn(self)→None
   F: note_tool_call(self)→None
   F: build_digest(self)→str
   F: set_workspace(self,root,entries)→None
   F: get_cached_file(self,path)→Optional[str]
   F: put_file(self,path,content)→None
   F: mark_stale(self,path)→None
   F: record_edit(self,path,summary)→None
   F: record_outcome(self,text)→None
   F: history_summary(self)→str
---

F195│streaming.py│109
S: Streaming helpers for the agent loop — real provider streaming with fake-chunk fallback.
D: ●__future__,threading,typing
F: stream_final(content,step,conversation_id,orchestrator)→Any
   ↳Called by: F201:_iter_agent_events_body
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F201:_iter_agent_events_body]
F: stream_llm_response(orchestrator)→Any
---
