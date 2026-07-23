# 📂 providers
Generated: 2026-07-23 14:15:38
Files: 4

---

F201│__init__.py│0
---

F202│gemini_provider.py│366
S: llm/providers/gemini_provider.py
D: ●__future__,google,json,typing
C: GeminiProvider│[__init__,generate,_generate_with_messages,_generate_initial_from_messages,_generate_stateful,_generate_stateless,generate_stream]
F: _get(obj,attr,default)→Any
   ↳Called by: F202:generate_stream,F202:_parse_interaction
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F202:generate_stream],[F202:_parse_interaction]
F: _format_tool_for_gemini(tools)→Any
   ↳Called by: F202:_generate_initial_from_messages,F202:generate,F202:generate_stream
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F202:_generate_initial_from_messages],[F202:generate],[F202:generate_stream]
   S: Normalize OpenAI-style, legacy gemini function_declarations, or flat tools.
F: _parse_interaction(res)→Any
   ↳Called by: F202:_generate_initial_from_messages,F202:generate,F202:_generate_stateless | Calls: F202:_get
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F202:_generate_initial_from_messages],[F202:generate],[F202:_generate_stateless]
F: _messages_to_steps(messages)→Any
   ↳Called by: F202:generate_stream,F202:_generate_stateless
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F202:generate_stream],[F202:_generate_stateless]
   S: Convert internal chat messages to Interactions API steps.
C: GeminiProvider│[__init__,generate,_generate_with_messages,_generate_initial_from_messages,_generate_stateful,_generate_stateless,generate_stream]
   F: __init__(self,api_key,model)
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F202:_parse_interaction,F202:_format_tool_for_gemini
   F: _generate_with_messages(self,messages,model,system_prompt,temperature,max_tokens,tools)→Any
   F: _generate_initial_from_messages(self,messages,model,system_prompt,tools)→Any
   ↳Calls: F202:_parse_interaction,F202:_format_tool_for_gemini
      S: First Interactions turn: store history server-side for later chaining.
   F: _generate_stateful(self,messages,model,system_prompt,tools,conversation_id,temperature,max_tokens)→Any
   ↳Calls: F202:_parse_interaction,F202:_format_tool_for_gemini
      S: Continue a server-side conversation; send only the latest turn + tool results.
   F: _generate_stateless(self,messages,model,system_prompt,tools,temperature,max_tokens)→Any
   ↳Calls: F202:_messages_to_steps,F202:_parse_interaction,F202:_format_tool_for_gemini
      S: Client-managed history. Prefer _generate_initial_from_messages + stateful chaining.
   F: generate_stream(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F202:_messages_to_steps,F202:_format_tool_for_gemini,F202:_get
---

F200│mock_provider.py│49
S: llm/providers/mock_provider.py
D: ●time,typing
C: MockProvider│[__init__,generate,generate_stream]
C: MockProvider│[__init__,generate,generate_stream]
   F: __init__(self,api_key,model)
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   F: generate_stream(self,prompt,model,system_prompt,temperature,max_tokens,tools,messages)→Any
      S: Simulate streaming by yielding the mock response character by character.
---

F199│openrouter_provider.py│160
S: llm/providers/openrouter_provider.py
D: ●__future__,json,openai,typing
C: OpenRouterProvider│[__init__,generate,generate_stream]
F: _convert_messages_to_openai(messages)→Any
   ↳Called by: F199:generate,F199:generate_stream
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F199:generate],[F199:generate_stream]
   S: Convert internal message array to OpenAI/OpenRouter format.
   S: Internal format uses 'tool_results' and 'tool_calls' as arrays.
   S: OpenAI format uses separate 'tool_calls' on assistant messages
   S: and individual 'tool' messages with 'tool_call_id'.
C: OpenRouterProvider│[__init__,generate,generate_stream]
   F: __init__(self,api_key,model)
   F: generate(self,prompt,model,system_prompt,conversation_id,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F199:_convert_messages_to_openai
   F: generate_stream(self,prompt,model,system_prompt,temperature,max_tokens,tools,messages)→Any
   ↳Calls: F199:_convert_messages_to_openai
      S: Stream tokens from OpenRouter using OpenAI-compatible streaming.
---
