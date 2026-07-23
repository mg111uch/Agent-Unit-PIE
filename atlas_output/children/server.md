# 📂 server
Generated: 2026-07-23 14:15:38
Files: 5

---

F172│__init__.py│100
S: FastAPI server application — global state, middleware, and startup.
D: ●__future__,agent_core,dotenv,os,sys,+2
---

F173│audit.py│65
S: Audit-wrapping and file tree builder shared by routes and ws_handler.
D: ●__future__,agent_core,os
F: build_tree(dir_path,max_depth,depth)
   ↳Called by: F170:get_file_tree,F173:build_tree | Calls: F173:build_tree
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F170:get_file_tree],[F173:build_tree]
F: make_audit_wrapper(active_tools_dict,rate_limiter,audit_log,redact,user_key)
   ↳Called by: F169:handle_chat | Calls: F166:redact
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F169:handle_chat]
   S: Return a wrapped tools dict with audit-log, rate-limit, and redaction.
---

F171│auth.py│22
S: JWT authentication helpers.
D: ●__future__,agent_core,fastapi,jwt,typing
F: verify_token(token)→Optional[dict]
   ↳Called by: F169:websocket_agent,F171:require_auth
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F169:websocket_agent],[F171:require_auth]
F: require_auth(credentials)→dict
   ↳Calls: F171:verify_token
---

F170│routes.py│91
S: REST API routes for the agent server.
D: ●__future__,agent_core,fastapi,os
F: get_status()
F: list_providers(user)
F: switch_provider(data,user)
F: get_file_tree(user)
   ↳Calls: F173:build_tree
F: read_file(path,user)
F: get_audit_log(limit,offset,user)
---

F169│ws_handler.py│290
S: WebSocket handler — agent lifecycle over WebSocket transport.
D: ●__future__,agent_core,asyncio,threading,time,+2
F: websocket_agent(websocket,token)
   ↳Calls: F169:handle_chat,F171:verify_token,F169:handle_slash
F: handle_slash(websocket,command,args,conv_id,user_key,cancel_event)→Optional[str]
   ↳Called by: F169:websocket_agent | Calls: F169:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F169:websocket_agent]
F: handle_chat(websocket,user_input,conversation_id,user_key,cancel_event)→Optional[str]
   ↳Called by: F169:websocket_agent,F169:handle_slash | Calls: F173:make_audit_wrapper,F175:resolve_all_questions,F175:cancel_questions
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F169:websocket_agent],[F169:handle_slash]
---
