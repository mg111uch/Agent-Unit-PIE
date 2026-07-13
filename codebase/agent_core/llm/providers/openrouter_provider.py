"""
llm/providers/openrouter_provider.py

OpenRouter provider adapter for LLMOrchestrator.
Uses the OpenAI-compatible SDK pointed at OpenRouter's API.
Supports native function calling via tools=[] parameter.
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional, List, Generator


def _convert_messages_to_openai(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Convert internal message array to OpenAI/OpenRouter format.

    Internal format uses 'tool_results' and 'tool_calls' as arrays.
    OpenAI format uses separate 'tool_calls' on assistant messages
    and individual 'tool' messages with 'tool_call_id'.
    """
    oai_messages = []

    for msg in messages:
        role = msg.get("role", "user")

        if role == "system":
            oai_messages.append({"role": "system", "content": msg.get("content", "")})
            continue

        if role == "tool":
            tool_results = msg.get("tool_results", [])
            if tool_results:
                # OpenAI requires one message per tool result with tool_call_id
                for tr in tool_results:
                    oai_messages.append({
                        "role": "tool",
                        "content": tr.get("result", ""),
                        "tool_call_id": tr.get("tool_call_id", tr.get("tool", "")),
                    })
            else:
                oai_messages.append({
                    "role": "tool",
                    "content": msg.get("content", ""),
                    "tool_call_id": msg.get("tool_call_id", "unknown"),
                })
            continue

        if role == "assistant":
            entry = {"role": "assistant", "content": msg.get("content") or None}
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.get("id", f"call_{tc.get('name', 'unknown')}"),
                        "type": "function",
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": json.dumps(tc.get("arguments", {})),
                        },
                    }
                    for tc in tool_calls
                ]
            oai_messages.append(entry)
            continue

        # user role
        oai_messages.append({"role": "user", "content": msg.get("content", "")})

    return oai_messages


class OpenRouterProvider:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b:free"):
        from openai import OpenAI
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.default_model = model

    def generate(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if messages:
            oai_messages = _convert_messages_to_openai(messages)
        else:
            oai_messages = []
            if system_prompt:
                oai_messages.append({"role": "system", "content": system_prompt})
            oai_messages.append({"role": "user", "content": prompt})

        api_kwargs: dict = dict(
            model=model or self.default_model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            api_kwargs["tools"] = tools

        res = self.client.chat.completions.create(**api_kwargs)

        choice = res.choices[0] if res.choices else None
        response_text = ""
        structured_calls = None

        if choice and choice.message:
            if choice.message.tool_calls:
                structured_calls = []
                for tc in choice.message.tool_calls:
                    raw_args = tc.function.arguments or "{}"
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {"input": raw_args}
                    structured_calls.append({
                        "name": tc.function.name,
                        "arguments": args,
                    })
            response_text = choice.message.content or ""
            if not response_text and not structured_calls:
                refusal = getattr(choice.message, "refusal", None)
                if refusal:
                    response_text = str(refusal)

        token_count = res.usage.total_tokens if res.usage else 0

        return {
            "status": "success",
            "response": response_text if response_text is not None else "",
            "tool_calls": structured_calls,
            "conversation_id": None,
            "usage": {
                "total_tokens": token_count,
                "estimated_cost": 0.0,
            },
        }

    def generate_stream(
        self,
        prompt: str = "",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Stream tokens from OpenRouter using OpenAI-compatible streaming."""
        if messages:
            oai_messages = _convert_messages_to_openai(messages)
        else:
            oai_messages = []
            if system_prompt:
                oai_messages.append({"role": "system", "content": system_prompt})
            oai_messages.append({"role": "user", "content": prompt})

        api_kwargs: dict = dict(
            model=model or self.default_model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        if tools:
            api_kwargs["tools"] = tools

        stream = self.client.chat.completions.create(**api_kwargs)

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
