# 📂 agent_core_2
Generated: 2026-07-27 19:23:22
Files: 6

---

F166│__init__.py│25
S: agent_core - Shared agent runtime: LLM orchestration, loop, config, commands.
D: ●agent_core,logging
---

F170│commands.py│17
S: CLI slash-command parsing.
D: ●__future__,typing
F: parse_command(user_input)→Any
---

F165│llm_orchestrator.py│189
S: agent_core/llm/llm_orchestrator.py
D: ●__future__,datetime,logging,threading,time,+1
C: LLMOrchestrator│[__init__,generate,register_provider,remove_provider,generate_stream]
   S: Universal LLM orchestration system.
C: LLMOrchestrator│[__init__,generate,register_provider,remove_provider,generate_stream]
   S: Universal LLM orchestration system.
   F: __init__(self,providers,default_provider,default_model,config)
   F: generate(self,prompt,system_prompt,provider,model,conversation_id,temperature,max_tokens,structured_output,metadata,tools,messages,cancel_flag)→Any
   F: register_provider(self,provider_name,provider_client)→None
   F: remove_provider(self,provider_name)→bool
   F: generate_stream(self,prompt,system_prompt,provider,model,temperature,max_tokens,tools,messages)→Any
      S: Stream tokens from the LLM provider.
      S: Yields incremental text chunks as they arrive from the provider.
      S: Falls back to the non-streaming generate() if the provider lacks
      S: generate_stream().
---

F169│message_store.py│146
D: ●agent_core,json,pathlib,sqlite3,threading,+4
C: MessageStore│[__init__,_init_db,create_session,session_exists,add_message,get_messages,delete_session,count_messages,delete_old_messages,get_all_sessions,+1]
C: MessageStore│[__init__,_init_db,create_session,session_exists,add_message,get_messages,delete_session,count_messages,delete_old_messages,get_all_sessions,+1]
   F: __init__(self,db_path)
   F: _init_db(self)
   F: create_session(self,session_id)→dict
   F: session_exists(self,session_id)→bool
   F: add_message(self,session_id,role,content,tool_calls,tool_results)→int
   F: get_messages(self,session_id,limit)→List[dict]
   ↳Calls: F168:redact
   F: delete_session(self,session_id)
   F: count_messages(self,session_id)→int
   F: delete_old_messages(self,session_id,keep_last)
   F: get_all_sessions(self)→List[dict]
   F: close(self)
---

F167│rate_limiter.py│35
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

F168│secrets_redactor.py│15
D: ●__future__,agent_core,re
F: redact(text,patterns)→str
   ↳Called by: F175:make_audit_wrapper,F169:get_messages
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F175:make_audit_wrapper],[F169:get_messages]
---
