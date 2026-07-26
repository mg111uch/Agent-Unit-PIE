# 📂 codebase
Generated: 2026-07-26 16:20:18
Files: 3

---

F002│__init__.py│0
---

F001│server.py│22│⚡
S: server.py - FastAPI WebSocket server for browser-based agent control.
D: ●__future__,getpass,json,os,uvicorn,+4
---

F004│tool_client.py│169│⚡
S: Thin CLI to test code_rag agent tools directly (no server, no LLM).
D: ●agent_core,argparse,json,os,sqlite3,+1
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
