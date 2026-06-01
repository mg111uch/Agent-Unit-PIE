# 📂 llm
Generated: 2026-06-01 13:39:55
Files: 2

---

F140│context_builder.py│429
S: llm/context_builder.py
D: ●__future__,datetime,json,logging,typing
C: ContextBuilder│[__init__,build_context,retrieve_relevant_memory,prioritize_context,compress_context,compress_section,trim_to_token_limit,build_prompt_context,health_check,utc_now]
   S: Dynamic cognition context assembler.
---

F141│llm_orchestrator.py│424
S: llm/llm_orchestrator.py
D: ●datetime,json,logging,time,typing,+1
C: LLMOrchestrator│[__init__,generate,build_prompt,serialize_context,execute_tool,register_provider,remove_provider,generate_with_fallback,health_check,utc_now]
   S: Universal LLM orchestration system.
---
