# 📂 sub-agents
Generated: 2026-07-21 18:31:40
Files: 6

---

F012│debate_agent.py│46
D: ●kernel
F: emit_belief_signal(argument_name,stance,confidence,topic)→None
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: emit_confidence_signal(argument_name,old_confidence,new_confidence,topic)→None
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
F: emit_contradiction_signal(contradicted_arguments,topic)→None
   ↳Called by: F292:debate_step
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F292:debate_step]
---

F011│improvement_agent.py│0
---

F013│observer_agent.py│0
---

F016│pattern_agent.py│0
---

F015│simulation_agent.py│0
---

F014│summarizer_agent.py│0
---
