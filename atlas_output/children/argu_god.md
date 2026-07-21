# 📂 argu_god
Generated: 2026-07-21 18:31:40
Files: 2

---

F291│llm_compiler.py│6
D: ●json,os
F: compile_topic_llm(topic)
   ↳Called by: F290:compile_topic
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F290:compile_topic]
---

F290│main.py│53│⚡
D: ►F291 ●asyncio,fastapi,json,os,uvicorn
F: root()
F: websocket_endpoint(ws)
F: list_topics()
F: get_graph(topic)
F: compile_topic(topic)
   ↳Calls: F291:compile_topic_llm
F: get_mindmap()
---
