"""
llm/providers/gemini_provider.py

Gemini provider using the Interactions API (google-genai >= 2.3.0).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, List, Optional


def _get(obj: Any, attr: str, default: Any = None) -> Any:
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default


def _format_tool_for_gemini(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize OpenAI-style, legacy gemini function_declarations, or flat tools."""
    result: List[Dict[str, Any]] = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        # Legacy generateContent wrapper: {"function_declarations": [...]}
        if "function_declarations" in t:
            for decl in t.get("function_declarations") or []:
                if not isinstance(decl, dict):
                    continue
                fd: dict[str, Any] = {
                    "type": "function",
                    "name": decl.get("name", ""),
                    "description": decl.get("description", ""),
                }
                params = decl.get("parameters") or decl.get("parameters_json_schema") or {}
                if params:
                    fd["parameters"] = params
                result.append(fd)
            continue

        # OpenAI / registry default: {"type": "function", "function": {...}}
        if "function" in t and isinstance(t["function"], dict):
            fn = t["function"]
            fd = {
                "type": "function",
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
            }
            params = fn.get("parameters") or {}
            if params:
                fd["parameters"] = params
            result.append(fd)
            continue

        # Already Interactions-style flat tool
        if t.get("type") == "function" or "name" in t:
            fd = {
                "type": "function",
                "name": t.get("name", ""),
                "description": t.get("description", ""),
            }
            params = t.get("parameters") or {}
            if params:
                fd["parameters"] = params
            result.append(fd)
    return result


def _parse_interaction(res: Any) -> dict[str, Any]:
    output = _get(res, "output_text", None) or ""

    tool_calls: list[dict[str, Any]] = []
    steps = _get(res, "steps", None) or []
    for step in steps:
        step_type = _get(step, "type")
        if step_type == "function_call":
            name = _get(step, "name", "")
            args = _get(step, "arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"input": args}
            call_id = _get(step, "id", "") or ""
            tool_calls.append({
                "id": call_id,
                "call_id": call_id,
                "name": name,
                "arguments": args if isinstance(args, dict) else {"input": args},
            })

    usage = _get(res, "usage", None)
    token_count = 0
    if usage:
        token_count = _get(usage, "total_tokens", 0) or _get(usage, "total_token_count", 0) or 0

    if not tool_calls and output:
        try:
            parsed = json.loads(output)
            if "final" not in parsed and "action" not in parsed:
                output = json.dumps({"final": output})
        except json.JSONDecodeError:
            output = json.dumps({"final": output})

    return {
        "status": "success",
        "response": output,
        "tool_calls": tool_calls or None,
        "conversation_id": _get(res, "id", None),
        "usage": {
            "total_tokens": token_count,
            "estimated_cost": 0.0,
        },
    }


def _messages_to_steps(
    messages: List[Dict[str, Any]],
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """Convert internal chat messages to Interactions API steps."""
    sys_inst = None
    steps: list[dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "user")
        if role == "system":
            sys_inst = msg.get("content", "")
            continue
        content = msg.get("content")
        tool_calls = msg.get("tool_calls")
        tool_results = msg.get("tool_results")

        if role == "user":
            steps.append({
                "type": "user_input",
                "content": [{"type": "text", "text": content or ""}],
            })
        elif role == "assistant":
            if content:
                steps.append({
                    "type": "model_output",
                    "content": [{"type": "text", "text": content}],
                })
            if tool_calls:
                for tc in tool_calls:
                    call_id = (
                        tc.get("id")
                        or tc.get("_call_id")
                        or tc.get("call_id")
                        or ""
                    )
                    steps.append({
                        "type": "function_call",
                        "id": call_id,
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments", {}),
                    })
        elif role == "tool":
            if tool_results:
                for tr in tool_results:
                    call_id = (
                        tr.get("_call_id")
                        or tr.get("call_id")
                        or tr.get("id")
                        or tr.get("tool_call_id")
                        or ""
                    )
                    steps.append({
                        "type": "function_result",
                        "name": tr.get("tool", tr.get("name", "")),
                        "call_id": call_id,
                        "result": [{"type": "text", "text": tr.get("result", "")}],
                    })

    return steps, sys_inst


class GeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash"):
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
            if conversation_id:
                return self._generate_stateful(
                    messages,
                    model or self.default_model,
                    system_prompt,
                    tools,
                    conversation_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            # First turn: store server-side so previous_interaction_id chaining works.
            # Do not use store=False here — that breaks tool follow-ups with 400.
            return self._generate_initial_from_messages(
                messages,
                model or self.default_model,
                system_prompt,
                tools,
            )

        model_name = model or self.default_model
        call_kwargs: dict[str, Any] = {"model": model_name}

        if conversation_id:
            call_kwargs["previous_interaction_id"] = conversation_id
            call_kwargs["input"] = prompt
            if system_prompt:
                call_kwargs["system_instruction"] = system_prompt
        else:
            full = prompt
            if system_prompt:
                full = f"{system_prompt}\n\n{prompt}"
            call_kwargs["input"] = full

        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)

        res = self.client.interactions.create(**call_kwargs)
        return _parse_interaction(res)

    def _generate_with_messages(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return self._generate_initial_from_messages(
            messages, model or self.default_model, system_prompt, tools,
        )

    def _generate_initial_from_messages(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """First Interactions turn: store history server-side for later chaining."""
        sys_inst = None
        last_user = ""
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system" and msg.get("content"):
                sys_inst = msg["content"]
            elif role == "user" and msg.get("content"):
                last_user = msg["content"]

        call_kwargs: dict[str, Any] = {
            "model": model,
            "input": last_user or "",
        }
        if system_prompt or sys_inst:
            call_kwargs["system_instruction"] = system_prompt or sys_inst
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)

        res = self.client.interactions.create(**call_kwargs)
        return _parse_interaction(res)

    def _generate_stateful(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
        conversation_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Continue a server-side conversation; send only the latest turn + tool results."""
        pending_results: list[dict[str, Any]] = []
        last_user = None

        for msg in messages:
            role = msg.get("role", "user")
            if role == "user" and msg.get("content"):
                last_user = msg["content"]
                pending_results = []
            elif role == "tool":
                for tr in msg.get("tool_results") or []:
                    call_id = (
                        tr.get("_call_id")
                        or tr.get("call_id")
                        or tr.get("id")
                        or tr.get("tool_call_id")
                        or ""
                    )
                    name = tr.get("tool", tr.get("name", ""))
                    # Skip parse/corrective pseudo-tools that were never model function_calls
                    if name == "parse" or not call_id:
                        continue
                    text = tr.get("result", "")
                    if not isinstance(text, str):
                        text = json.dumps(text, ensure_ascii=False)
                    step: dict[str, Any] = {
                        "type": "function_result",
                        "name": name,
                        "call_id": call_id,
                        "result": [{"type": "text", "text": text}],
                    }
                    if isinstance(text, str) and text.startswith("Error"):
                        step["is_error"] = True
                    pending_results.append(step)

        if pending_results:
            input_data: Any = pending_results
        else:
            # Fall back to last user text (e.g. corrective follow-ups without call_id)
            input_data = last_user or ""

        call_kwargs: dict[str, Any] = {
            "model": model,
            "previous_interaction_id": conversation_id,
            "input": input_data,
        }
        # Do not resend system_instruction on chained turns (can cause invalid_request).
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)

        res = self.client.interactions.create(**call_kwargs)
        return _parse_interaction(res)

    def _generate_stateless(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Client-managed history. Prefer _generate_initial_from_messages + stateful chaining."""
        steps, sys_inst = _messages_to_steps(messages)

        call_kwargs: dict[str, Any] = {
            "model": model,
            "input": steps,
            "store": False,
        }
        if sys_inst or system_prompt:
            call_kwargs["system_instruction"] = system_prompt or sys_inst
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)

        res = self.client.interactions.create(**call_kwargs)
        return _parse_interaction(res)

    def generate_stream(
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
    ) -> Generator[str, None, None]:
        if messages:
            input_data, extracted_system = _messages_to_steps(messages)
            sys_inst = system_prompt or extracted_system
        else:
            full = prompt
            if system_prompt:
                full = f"{system_prompt}\n\n{prompt}"
            sys_inst = None
            input_data = full

        call_kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "input": input_data,
            "stream": True,
        }
        if conversation_id:
            call_kwargs["previous_interaction_id"] = conversation_id
        if sys_inst:
            call_kwargs["system_instruction"] = sys_inst
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)

        for event in self.client.interactions.create(**call_kwargs):
            if _get(event, "event_type") == "step.delta":
                delta = _get(event, "delta")
                if delta and _get(delta, "type") == "text":
                    text = _get(delta, "text")
                    if text:
                        yield text
