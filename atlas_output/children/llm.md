# 📂 llm
Generated: 2026-07-21 18:31:40
Files: 3

---

F358│__init__.py│0
---

F356│context_builder.py│385
S: llm/context_builder.py
D: ●__future__,datetime,json,logging,typing
C: ContextBuilder│[__init__,build_context,retrieve_relevant_memory,prioritize_context,compress_context,compress_section,trim_to_token_limit,build_prompt_context,health_check,utc_now]
   S: Dynamic cognition context assembler.
C: ContextBuilder│[__init__,build_context,retrieve_relevant_memory,prioritize_context,compress_context,compress_section,trim_to_token_limit,build_prompt_context,health_check,utc_now]
   S: Dynamic cognition context assembler.
   F: __init__(self,retrieval_engine,memory_engine,compression_engine,token_estimator,config)
   F: build_context(self,task,unit_id,unit_type,additional_context)→Any
      S: Main context generation pipeline.
   F: retrieve_relevant_memory(self,task,unit_id,unit_type)→Any
      S: Retrieve relevant cognition artifacts.
   F: prioritize_context(self,retrieval_result,task)→Any
      S: Rank retrieved artifacts by relevance.
   F: compress_context(self,prioritized_context)→Any
      S: Compress context intelligently.
   F: compress_section(self,section_name,section_data)→Any
      S: Compress individual context section.
   F: trim_to_token_limit(self,context)→Any
      S: Ensure context fits token budget.
   F: build_prompt_context(self,context)→str
      S: Convert context into prompt-safe text.
   F: health_check(self)→Any
   F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
---

F357│llm_orchestrator.py│171
S: agent_core/llm/llm_orchestrator.py
D: ●__future__,datetime,logging,time,typing
C: LLMOrchestrator│[__init__,generate,register_provider,remove_provider,generate_stream]
   S: Universal LLM orchestration system.
C: LLMOrchestrator│[__init__,generate,register_provider,remove_provider,generate_stream]
   S: Universal LLM orchestration system.
   F: __init__(self,providers,default_provider,default_model,config)
   F: generate(self,prompt,system_prompt,provider,model,conversation_id,temperature,max_tokens,structured_output,metadata,tools,messages)→Any
   F: register_provider(self,provider_name,provider_client)→None
   F: remove_provider(self,provider_name)→bool
   F: generate_stream(self,prompt,system_prompt,provider,model,temperature,max_tokens,tools,messages)→Any
      S: Stream tokens from the LLM provider.
      S: Yields incremental text chunks as they arrive from the provider.
      S: Falls back to the non-streaming generate() if the provider lacks
      S: generate_stream().
---
