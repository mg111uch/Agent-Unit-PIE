# 📂 argu_god
Generated: 2026-06-01 13:39:55
Files: 2

---

F125│llm_compiler.py│79
D: ●datetime,json,os,subprocess
F: write_question_to_file(question)
   ↳Called by: F125:compile_topic_llm
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F125:compile_topic_llm]
F: run_gemini_agent()
   ↳Called by: F125:compile_topic_llm
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F125:compile_topic_llm]
F: read_answer_from_file()
   ↳Called by: F125:compile_topic_llm
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F125:compile_topic_llm]
F: compile_topic_llm(topic)
   ↳Called by: F124:compile_topic | Calls: F125:run_gemini_agent,F125:write_question_to_file,F125:read_answer_from_file
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F124:compile_topic]
---

F124│main.py│47│⚡
D: ►F125 ●fastapi,json,os,uvicorn
F: root()
F: websocket_endpoint(ws)
F: list_topics()
F: get_graph(topic)
F: compile_topic(topic)
   ↳Calls: F125:compile_topic_llm
F: get_mindmap()
---
