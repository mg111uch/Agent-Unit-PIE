# 📂 ralph_loop
Generated: 2026-07-21 18:31:40
Files: 3

---

F055│phoenix_helper.py│37│⚡
D: ●datetime,os,subprocess,sys,time
C: PhoenixHelper│[__init__,log_event,handle_success,handle_failure]
C: PhoenixHelper│[__init__,log_event,handle_success,handle_failure]
   F: __init__(self,log_file)
   F: log_event(self,message)
      S: Appends a timestamped message to the log file.
   F: handle_success(self,feature_name,loop_iteration,duration)
      S: Consolidates Git commit, logging, and status reporting.
   F: handle_failure(self,rca,loop_iteration,duration)
      S: Consolidates Git checkout and failure logging.
---

F054│ralph_agent.py│52│⚡
D: ►F053 ●google
F: loop_condition_function(state)→bool
   ↳Calls: F053:read_and_update_md
   S: Checks the MD file for any remaining undone features.
---

F053│readWriteMD.py│42│⚡
D: ●os,re,yaml
F: read_and_update_md(file_path,status,feature_name,log_message)→str
   ↳Called by: F054:loop_condition_function
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F054:loop_condition_function]
   S: Reads the next undone feature or updates a feature's status.
---
