# 📂 argu_god
Generated: 2026-07-26 16:20:18
Files: 2

---

F139│llm_compiler.py│88
D: ●agent_core,json,os
F: _get_orchestrator()
   ↳Called by: F139:generate_llm_question,F139:compile_topic_llm | Calls: F158:build_orchestrator
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F139:generate_llm_question],[F139:compile_topic_llm]
F: _parse_json_from_response(response)→Any
   ↳Called by: F139:generate_llm_question,F139:compile_topic_llm
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F139:generate_llm_question],[F139:compile_topic_llm]
F: compile_topic_llm(topic)→dict
   ↳Called by: F138:compile_topic | Calls: F139:_get_orchestrator,F139:_parse_json_from_response
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F138:compile_topic]
F: generate_llm_question(topic,knowledge_context)→Any
   ↳Called by: F146:_generate_next_question | Calls: F139:_get_orchestrator,F139:_parse_json_from_response
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F146:_generate_next_question]
---

F138│main.py│54│⚡
D: ►F139 ●asyncio,fastapi,json,os,uvicorn
F: root()
F: websocket_endpoint(ws)
F: list_topics()
F: get_graph(topic)
F: compile_topic(topic)
   ↳Calls: F139:compile_topic_llm
F: get_mindmap()
---
