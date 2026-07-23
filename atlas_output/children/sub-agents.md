# 📂 sub-agents
Generated: 2026-07-23 14:15:38
Files: 6

---

F011│debate_agent.py│46
D: ●kernel
F: emit_belief_signal(argument_name,stance,confidence,topic)→None
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: emit_confidence_signal(argument_name,old_confidence,new_confidence,topic)→None
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
F: emit_contradiction_signal(contradicted_arguments,topic)→None
   ↳Called by: F139:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
---

F010│improvement_agent.py│0
---

F012│observer_agent.py│0
---

F015│pattern_agent.py│0
---

F014│simulation_agent.py│0
---

F013│summarizer_agent.py│0
---
