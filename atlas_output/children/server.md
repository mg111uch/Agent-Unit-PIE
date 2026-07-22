# 📂 server
Generated: 2026-07-21 18:31:40
Files: 5

---

F335│__init__.py│100
S: FastAPI server application — global state, middleware, and startup.
D: ●__future__,agent_core,fastapi,os,typing,+2
---

F336│audit.py│65
S: Audit-wrapping and file tree builder shared by routes and ws_handler.
D: ●__future__,agent_core,os
F: build_tree(dir_path,max_depth,depth)
   ↳Called by: F336:build_tree,F333:get_file_tree | Calls: F336:build_tree
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F336:build_tree],[F333:get_file_tree]
F: make_audit_wrapper(active_tools_dict,rate_limiter,audit_log,redact,user_key)
   ↳Called by: F332:handle_chat | Calls: F329:redact
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F332:handle_chat]
   S: Return a wrapped tools dict with audit-log, rate-limit, and redaction.
---

F334│auth.py│22
S: JWT authentication helpers.
D: ●__future__,agent_core,fastapi,jwt,typing
F: verify_token(token)→Optional[dict]
   ↳Called by: F332:websocket_agent,F334:require_auth
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F332:websocket_agent],[F334:require_auth]
F: require_auth(credentials)→dict
   ↳Calls: F334:verify_token
---

F333│routes.py│91
S: REST API routes for the agent server.
D: ●__future__,agent_core,fastapi,os
F: get_status()
F: list_providers(user)
F: switch_provider(data,user)
F: get_file_tree(user)
   ↳Calls: F336:build_tree
F: read_file(path,user)
F: get_audit_log(limit,offset,user)
---

F332│ws_handler.py│290
S: WebSocket handler — agent lifecycle over WebSocket transport.
D: ●__future__,agent_core,fastapi,time,typing,+2
F: websocket_agent(websocket,token)
   ↳Calls: F334:verify_token,F332:handle_chat,F332:handle_slash
F: handle_slash(websocket,command,args,conv_id,user_key,cancel_event)→Optional[str]
   ↳Called by: F332:websocket_agent | Calls: F332:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F332:websocket_agent]
F: handle_chat(websocket,user_input,conversation_id,user_key,cancel_event)→Optional[str]
   ↳Called by: F332:websocket_agent,F332:handle_slash | Calls: F338:resolve_all_questions,F338:cancel_questions,F336:make_audit_wrapper
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F332:websocket_agent],[F332:handle_slash]
---
