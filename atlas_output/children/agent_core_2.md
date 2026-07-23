# 📂 agent_core_2
Generated: 2026-07-23 14:15:38
Files: 5

---

F164│__init__.py│19
S: agent_core - Shared agent runtime: LLM orchestration, loop, config, commands.
D: ●agent_core
---

F168│commands.py│17
S: CLI slash-command parsing.
D: ●__future__,typing
F: parse_command(user_input)→Any
---

F167│message_store.py│146
D: ●__future__,datetime,json,pathlib,threading,+4
C: MessageStore│[__init__,_init_db,create_session,session_exists,add_message,get_messages,delete_session,count_messages,delete_old_messages,get_all_sessions,+1]
C: MessageStore│[__init__,_init_db,create_session,session_exists,add_message,get_messages,delete_session,count_messages,delete_old_messages,get_all_sessions,+1]
   F: __init__(self,db_path)
   F: _init_db(self)
   F: create_session(self,session_id)→dict
   F: session_exists(self,session_id)→bool
   F: add_message(self,session_id,role,content,tool_calls,tool_results)→int
   F: get_messages(self,session_id,limit)→List[dict]
   ↳Calls: F166:redact
   F: delete_session(self,session_id)
   F: count_messages(self,session_id)→int
   F: delete_old_messages(self,session_id,keep_last)
   F: get_all_sessions(self)→List[dict]
   F: close(self)
---

F165│rate_limiter.py│35
D: ●__future__,collections,threading,time
C: TokenBucket│[__init__,acquire]
C: RateLimiter│[__init__,_get_bucket,check_llm,check_write]
C: TokenBucket│[__init__,acquire]
   F: __init__(self,rate_per_minute)
   F: acquire(self)→bool
C: RateLimiter│[__init__,_get_bucket,check_llm,check_write]
   F: __init__(self)
   F: _get_bucket(self,buckets,key,rate)→TokenBucket
   F: check_llm(self,user_id,rate)→bool
   F: check_write(self,user_id,rate)→bool
---

F166│secrets_redactor.py│15
D: ●__future__,agent_core,re
F: redact(text,patterns)→str
   ↳Called by: F173:make_audit_wrapper,F167:get_messages
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F173:make_audit_wrapper],[F167:get_messages]
---
