# 📂 dummy
Generated: 2026-07-01 17:38:04
Files: 1

---

F001│calculator.py│50│⚡
F: add(n1,n2)
   ↳Called by: F001:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:calculator]
F: subtract(n1,n2)
   ↳Called by: F001:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:calculator]
F: multiply(n1,n2)
   ↳Called by: F001:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:calculator]
F: divide(n1,n2)
   ↳Called by: F001:calculator
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F001:calculator]
F: calculator()
   ↳Calls: F001:add,F001:divide,F001:subtract
   S: Main calculator function that runs in a loop.
---
