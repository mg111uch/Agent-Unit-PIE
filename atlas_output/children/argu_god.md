# 📂 argu_god
Generated: 2026-07-17 18:00:11
Files: 2

---

F002│llm_compiler.py│79
D: ●datetime,json,os,subprocess
F: write_question_to_file(question)
   ↳Called by: F002:compile_topic_llm
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F002:compile_topic_llm]
F: run_gemini_agent()
   ↳Called by: F002:compile_topic_llm
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F002:compile_topic_llm]
F: read_answer_from_file()
   ↳Called by: F002:compile_topic_llm
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F002:compile_topic_llm]
F: compile_topic_llm(topic)
   ↳Called by: F001:compile_topic | Calls: F002:read_answer_from_file,F002:write_question_to_file,F002:run_gemini_agent
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:compile_topic]
---

F001│main.py│47│⚡
D: ►F002 ●fastapi,json,os,uvicorn
F: root()
F: websocket_endpoint(ws)
F: list_topics()
F: get_graph(topic)
F: compile_topic(topic)
   ↳Calls: F002:compile_topic_llm
F: get_mindmap()
---
