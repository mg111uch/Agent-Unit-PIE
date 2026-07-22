# 📂 dummy
Generated: 2026-07-21 18:31:40
Files: 1

---

F051│calculator.py│50│⚡
F: add(n1,n2)
   ↳Called by: F240:subscribe,F091:add_edge,F219:_detect_circular_dependencies
   ↳Impact: 🔴HIGH (11 dependents) | Breaks: [F240:subscribe],[F091:add_edge],[F219:_detect_circular_dependencies]
F: subtract(n1,n2)
   ↳Called by: F051:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F051:calculator]
F: multiply(n1,n2)
   ↳Called by: F051:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F051:calculator]
F: divide(n1,n2)
   ↳Called by: F051:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F051:calculator]
F: calculator()
   ↳Calls: F074:add,F051:multiply,F051:add
   S: Main calculator function that runs in a loop.
---
