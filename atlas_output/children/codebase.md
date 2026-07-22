# 📂 codebase
Generated: 2026-07-21 18:31:40
Files: 3

---

F002│__init__.py│1
---

F001│server.py│47│⚡
S: server.py - FastAPI WebSocket server for browser-based agent control.
D: ●__future__,agent_core,base64,cryptography,getpass,+4
F: _derive_key(password,salt)→bytes
   ↳Called by: F001:_try_unlock_env
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:_try_unlock_env]
F: _try_unlock_env()→None
   ↳Calls: F001:_derive_key
---

F004│tool_client.py│169│⚡
S: Thin CLI to test code_rag agent tools directly (no server, no LLM).
D: ●agent_core,argparse,os,sqlite3,sys,+1
F: _resolve_rag(args)→CodeRAG
   ↳Called by: F004:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F004:main]
F: cmd_get_symbol(rag,args)
F: cmd_get_symbols_meta(rag,args)
F: cmd_search_symbols(rag,args)
F: cmd_callers_callees(rag,args)
F: cmd_find_impact(rag,args)
F: cmd_index_info(rag,args)
F: cmd_get_index_info(rag,args)
F: main()
   ↳Calls: F004:_resolve_rag
---
