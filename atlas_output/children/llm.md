# 📂 llm
Generated: 2026-07-26 16:20:18
Files: 2

---

F201│__init__.py│0
---

F200│llm_orchestrator.py│189
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
