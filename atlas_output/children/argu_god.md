# 📂 argu_god
Generated: 2026-07-23 14:15:38
Files: 2

---

F138│llm_compiler.py│88
D: ●agent_core,json,os
F: _get_orchestrator()
   ↳Called by: F138:compile_topic_llm,F138:generate_llm_question | Calls: F157:build_orchestrator
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F138:compile_topic_llm],[F138:generate_llm_question]
F: _parse_json_from_response(response)→Any
   ↳Called by: F138:compile_topic_llm,F138:generate_llm_question
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F138:compile_topic_llm],[F138:generate_llm_question]
F: compile_topic_llm(topic)→dict
   ↳Called by: F137:compile_topic | Calls: F138:_parse_json_from_response,F138:_get_orchestrator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F137:compile_topic]
F: generate_llm_question(topic,knowledge_context)→Any
   ↳Called by: F145:_generate_next_question | Calls: F138:_parse_json_from_response,F138:_get_orchestrator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F145:_generate_next_question]
---

F137│main.py│54│⚡
D: ►F138 ●asyncio,fastapi,json,os,uvicorn
F: root()
F: websocket_endpoint(ws)
F: list_topics()
F: get_graph(topic)
F: compile_topic(topic)
   ↳Calls: F138:compile_topic_llm
F: get_mindmap()
---
