# 📂 providers
Generated: 2026-07-27 19:23:22
Files: 4

---

F204│__init__.py│35
D: ●__future__,typing
C: LLMProvider←Protocol│[generate,generate_stream,supports_stateful]
   S: Protocol that all LLM providers must satisfy.
C: LLMProvider←Protocol│[generate,generate_stream,supports_stateful]
   S: Protocol that all LLM providers must satisfy.
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   F: generate_stream(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   F: supports_stateful(self)→bool
---

F205│gemini_provider.py│365
S: llm/providers/gemini_provider.py
D: ●__future__,google,json,typing
C: GeminiProvider│[__init__,supports_stateful,generate,_generate_with_messages,_generate_initial_from_messages,_generate_stateful,_generate_stateless,generate_stream]
F: _get(obj,attr,default)→Any
   ↳Called by: F205:_parse_interaction,F205:generate_stream
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F205:_parse_interaction],[F205:generate_stream]
F: _format_tool_for_gemini(tools)→Any
   ↳Called by: F205:_generate_stateful,F205:generate_stream,F205:generate
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F205:_generate_stateful],[F205:generate_stream],[F205:generate]
   S: Normalize OpenAI-style, legacy gemini function_declarations, or flat tools.
F: _parse_interaction(res)→Any
   ↳Called by: F205:_generate_initial_from_messages,F205:_generate_stateless,F205:generate | Calls: F205:_get
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F205:_generate_initial_from_messages],[F205:_generate_stateless],[F205:generate]
F: _messages_to_steps(messages)→Any
   ↳Called by: F205:_generate_initial_from_messages,F205:generate_stream,F205:_generate_stateless
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F205:_generate_initial_from_messages],[F205:generate_stream],[F205:_generate_stateless]
   S: Convert internal chat messages to Interactions API steps.
C: GeminiProvider│[__init__,supports_stateful,generate,_generate_with_messages,_generate_initial_from_messages,_generate_stateful,_generate_stateless,generate_stream]
   F: __init__(self,api_key,model)
   F: supports_stateful(self)→bool
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F205:_format_tool_for_gemini,F205:_parse_interaction
   F: _generate_with_messages(self,messages,model,system_prompt,temperature,max_tokens,tools)→Any
   F: _generate_initial_from_messages(self,messages,model,system_prompt,tools)→Any
   ↳Calls: F205:_format_tool_for_gemini,F205:_parse_interaction,F205:_messages_to_steps
      S: First Interactions turn: store history server-side for later chaining.
   F: _generate_stateful(self,messages,model,system_prompt,tools,conversation_id,temperature,max_tokens)→Any
   ↳Calls: F205:_format_tool_for_gemini,F205:_parse_interaction
      S: Continue a server-side conversation; send only the latest turn + tool results.
   F: _generate_stateless(self,messages,model,system_prompt,tools,temperature,max_tokens)→Any
   ↳Calls: F205:_format_tool_for_gemini,F205:_parse_interaction,F205:_messages_to_steps
      S: Client-managed history. Prefer _generate_initial_from_messages + stateful chaining.
   F: generate_stream(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F205:_format_tool_for_gemini,F205:_messages_to_steps,F205:_get
---

F203│mock_provider.py│236
S: Mock LLM provider with configurable response stanzas for testing and frontend dev.
D: ●json,os,time,typing
C: MockProvider│[__init__,supports_stateful,_is_default_stanzas,_select_from_prompt,_write_debug,_dump_messages,_dump_tools,generate,generate_stream]
C: MockProvider│[__init__,supports_stateful,_is_default_stanzas,_select_from_prompt,_write_debug,_dump_messages,_dump_tools,generate,generate_stream]
   F: __init__(self,api_key,model,scenario,stanzas,delay,debug_path)
   F: supports_stateful(self)→bool
   F: _is_default_stanzas(self)→bool
   F: _select_from_prompt(self,prompt,messages)→None
   F: _write_debug(self,entry)
   F: _dump_messages(self,messages,max_chars)→str
   F: _dump_tools(self,tools,max_chars)→str
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   F: generate_stream(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
---

F202│openrouter_provider.py│167
S: llm/providers/openrouter_provider.py
D: ●__future__,json,openai,typing,uuid
C: OpenRouterProvider│[__init__,generate,supports_stateful,generate_stream]
F: _convert_messages_to_openai(messages)→Any
   ↳Called by: F202:generate_stream,F202:generate
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F202:generate_stream],[F202:generate]
   S: Convert internal message array to OpenAI/OpenRouter format.
   S: Internal format uses 'tool_results' and 'tool_calls' as arrays.
   S: OpenAI format uses separate 'tool_calls' on assistant messages
   S: and individual 'tool' messages with 'tool_call_id'.
C: OpenRouterProvider│[__init__,generate,supports_stateful,generate_stream]
   F: __init__(self,api_key,model)
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F202:_convert_messages_to_openai
   F: supports_stateful(self)→bool
   F: generate_stream(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F202:_convert_messages_to_openai
      S: Stream tokens from OpenRouter using OpenAI-compatible streaming.
---
