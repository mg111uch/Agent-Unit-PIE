# 📂 server
Generated: 2026-07-27 19:23:22
Files: 5

---

F174│__init__.py│114
S: FastAPI server application — global state, middleware, and startup.
D: ●__future__,agent_core,fastapi,starlette,sys,+3
---

F175│audit.py│65
S: Audit-wrapping and file tree builder shared by routes and ws_handler.
D: ●__future__,agent_core,os
F: build_tree(dir_path,max_depth,depth)
   ↳Called by: F175:build_tree,F172:get_file_tree | Calls: F175:build_tree
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F175:build_tree],[F172:get_file_tree]
F: make_audit_wrapper(active_tools_dict,rate_limiter,audit_log,redact,user_key)
   ↳Called by: F171:handle_chat | Calls: F168:redact
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F171:handle_chat]
   S: Return a wrapped tools dict with audit-log, rate-limit, and redaction.
---

F173│auth.py│26
S: JWT authentication helpers.
D: ●__future__,agent_core,fastapi,jwt,os,+1
F: verify_token(token)→Optional[dict]
   ↳Called by: F173:require_auth,F171:websocket_agent
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F173:require_auth],[F171:websocket_agent]
F: require_auth(credentials)→dict
   ↳Calls: F173:verify_token
---

F172│routes.py│91
S: REST API routes for the agent server.
D: ●__future__,agent_core,fastapi,os
F: get_status()
F: list_providers(user)
F: switch_provider(data,user)
F: get_file_tree(user)
   ↳Calls: F175:build_tree
F: read_file(path,user)
F: get_audit_log(limit,offset,user)
---

F171│ws_handler.py│308
S: WebSocket handler — agent lifecycle over WebSocket transport.
D: ●__future__,agent_core,asyncio,fastapi,threading,+2
F: websocket_agent(websocket,token)
   ↳Calls: F171:handle_chat,F173:verify_token,F171:handle_slash
F: handle_slash(websocket,command,args,conv_id,user_key,cancel_event,session_state)→Optional[str]
   ↳Called by: F171:websocket_agent | Calls: F171:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F171:websocket_agent]
F: handle_chat(websocket,user_input,conversation_id,user_key,cancel_event,session_state)→Optional[str]
   ↳Called by: F171:handle_slash,F171:websocket_agent | Calls: F175:make_audit_wrapper,F177:cancel_questions,F177:resolve_all_questions
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F171:handle_slash],[F171:websocket_agent]
---
