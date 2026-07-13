"""
llm/providers/gemini_provider.py

Gemini provider adapter for LLMOrchestrator.
Supports two modes:
  1. Stateful via conversation_id -> previous_interaction_id (legacy)
  2. Stateless via explicit messages array -> generate_content
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional, List, Generator


def _format_tool_for_gemini(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert OpenAI-style tool schemas to Gemini function_declarations format."""
    gemini_tools = []
    for t in tools:
        fd = {
            "name": t["function"]["name"],
            "description": t["function"].get("description", ""),
        }
        params = t["function"].get("parameters", {})
        if params:
            fd["parameters"] = params
        gemini_tools.append(fd)
    return gemini_tools


def _convert_messages_to_contents(
    messages: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Convert internal message array to Gemini contents list + system_instruction.

    Internal message format:
      {"role": "user"|"assistant"|"tool", "content": str|None,
       "tool_calls": [{"name":..., "arguments":...}]|None,
       "tool_results": [{"tool":..., "result":...}]|None}
    """
    contents = []
    system_instruction = None

    for msg in messages:
        role = msg.get("role", "user")

        if role == "system":
            system_instruction = msg.get("content", "")
            continue

        parts = []

        content = msg.get("content")
        if content:
            parts.append({"text": str(content)})

        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                parts.append({
                    "function_call": {
                        "name": tc.get("name", ""),
                        "args": tc.get("arguments", {}),
                    }
                })

        tool_results = msg.get("tool_results")
        if tool_results:
            for tr in tool_results:
                parts.append({
                    "function_response": {
                        "name": tr.get("tool", tr.get("name", "")),
                        "response": {"result": tr.get("result", "")},
                    }
                })

        if not parts:
            parts.append({"text": ""})

        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": parts})

    return contents, system_instruction


class GeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite"):
        from google import genai
        self.client = genai.Client(api_key=api_key)
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
            return self._generate_with_messages(
                messages, model, system_prompt, temperature, max_tokens, tools
            )

        full_input = prompt
        if system_prompt and not conversation_id:
            full_input = f"{system_prompt}\n\n{prompt}"

        kwargs = {"model": model or self.default_model, "input": full_input}
        if conversation_id:
            kwargs["previous_interaction_id"] = conversation_id
        if tools:
            kwargs["tools"] = _format_tool_for_gemini(tools)

        res = self.client.interactions.create(**kwargs)

        usage = getattr(res, "usage_metadata", None)
        token_count = 0
        if usage:
            token_count = (
                getattr(usage, "prompt_token_count", 0)
                + getattr(usage, "candidates_token_count", 0)
            )

        tool_calls = getattr(res, "tool_calls", None) or []
        output = getattr(res, "output_text", None)
        if output is None:
            output = getattr(res, "text", None) or ""
        if not isinstance(output, str):
            output = str(output) if output is not None else ""

        structured_calls = []
        for tc in tool_calls:
            fc = getattr(tc, "function_call", None) or tc
            name = getattr(fc, "name", "") or fc.get("name", "")
            args = getattr(fc, "args", {}) or fc.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"input": args}
            structured_calls.append({"name": name, "arguments": args})

        return {
            "status": "success",
            "response": output,
            "tool_calls": structured_calls or None,
            "conversation_id": getattr(res, "id", None),
            "usage": {
                "total_tokens": token_count,
                "estimated_cost": 0.0,
            },
        }

    def _generate_with_messages(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate using explicit message array with generate_content API."""
        from google.genai import types

        contents, extracted_system = _convert_messages_to_contents(messages)
        sys_inst = system_prompt or extracted_system

        config_kwargs = dict(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if sys_inst:
            config_kwargs["system_instruction"] = sys_inst
        if tools:
            config_kwargs["tools"] = _format_tool_for_gemini(tools)

        config = types.GenerateContentConfig(**config_kwargs)

        res = self.client.models.generate_content(
            model=model or self.default_model,
            contents=contents,
            config=config,
        )

        token_count = 0
        usage = getattr(res, "usage_metadata", None)
        if usage:
            token_count = (
                getattr(usage, "prompt_token_count", 0)
                + getattr(usage, "candidates_token_count", 0)
            )

        tool_calls = getattr(res, "function_calls", None) or []
        output = getattr(res, "text", None) or ""
        if not isinstance(output, str):
            output = str(output) if output is not None else ""

        structured_calls = []
        if tool_calls:
            for tc in tool_calls:
                name = getattr(tc, "name", "") or tc.get("name", "")
                args = getattr(tc, "args", {}) or tc.get("args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"input": args}
                structured_calls.append({"name": name, "arguments": args})

        return {
            "status": "success",
            "response": output,
            "tool_calls": structured_calls or None,
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
        """Stream tokens from Gemini using generate_content_stream."""
        from google.genai import types

        if messages:
            contents, extracted_system = _convert_messages_to_contents(messages)
            sys_inst = system_prompt or extracted_system
        else:
            full_input = prompt
            if system_prompt:
                full_input = f"{system_prompt}\n\n{prompt}"
            contents = full_input
            sys_inst = None

        config_kwargs = dict(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if sys_inst:
            config_kwargs["system_instruction"] = sys_inst
        if tools:
            config_kwargs["tools"] = _format_tool_for_gemini(tools)

        config = types.GenerateContentConfig(**config_kwargs)

        stream = self.client.models.generate_content_stream(
            model=model or self.default_model,
            contents=contents,
            config=config,
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text
