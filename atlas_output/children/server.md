# 📂 server
Generated: 2026-07-26 16:20:18
Files: 5

---

F173│__init__.py│111
S: FastAPI server application — global state, middleware, and startup.
D: ●__future__,agent_core,dotenv,os,starlette,+3
---

F174│audit.py│65
S: Audit-wrapping and file tree builder shared by routes and ws_handler.
D: ●__future__,agent_core,os
F: build_tree(dir_path,max_depth,depth)
   ↳Called by: F171:get_file_tree,F174:build_tree | Calls: F174:build_tree
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F171:get_file_tree],[F174:build_tree]
F: make_audit_wrapper(active_tools_dict,rate_limiter,audit_log,redact,user_key)
   ↳Called by: F170:handle_chat | Calls: F167:redact
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F170:handle_chat]
   S: Return a wrapped tools dict with audit-log, rate-limit, and redaction.
---

F172│auth.py│26
S: JWT authentication helpers.
D: ●__future__,agent_core,jwt,os,typing,+1
F: verify_token(token)→Optional[dict]
   ↳Called by: F170:websocket_agent,F172:require_auth
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F170:websocket_agent],[F172:require_auth]
F: require_auth(credentials)→dict
   ↳Calls: F172:verify_token
---

F171│routes.py│91
S: REST API routes for the agent server.
D: ●__future__,agent_core,fastapi,os
F: get_status()
F: list_providers(user)
F: switch_provider(data,user)
F: get_file_tree(user)
   ↳Calls: F174:build_tree
F: read_file(path,user)
F: get_audit_log(limit,offset,user)
---

F170│ws_handler.py│301
S: WebSocket handler — agent lifecycle over WebSocket transport.
D: ●__future__,agent_core,asyncio,threading,time,+2
F: websocket_agent(websocket,token)
   ↳Calls: F170:handle_slash,F170:handle_chat,F172:verify_token
F: handle_slash(websocket,command,args,conv_id,user_key,cancel_event)→Optional[str]
   ↳Called by: F170:websocket_agent | Calls: F170:handle_chat
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F170:websocket_agent]
F: handle_chat(websocket,user_input,conversation_id,user_key,cancel_event)→Optional[str]
   ↳Called by: F170:websocket_agent,F170:handle_slash | Calls: F176:resolve_all_questions,F174:make_audit_wrapper,F176:cancel_questions
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F170:websocket_agent],[F170:handle_slash]
---
