"""
llm/providers/openrouter_provider.py

OpenRouter provider adapter for LLMOrchestrator.
Uses the OpenAI-compatible SDK pointed at OpenRouter's API.
Supports native function calling via tools=[] parameter.
"""

from __future__ import annotations

import ast
import json
import re
import uuid
from typing import Dict, Any, Optional, List, Generator

from agent_core.config import (
    OPENROUTER_SKIP_TOOLS_ON_CHAIN,
    OPENROUTER_PRUNE_TOOLS_ON_CHAIN,
    OPENROUTER_RETRY_SKIPPED_CHAIN,
)
from agent_core.providers import BaseLLMProvider


def _is_chained_turn(messages: List[Dict[str, Any]]) -> bool:
    """True when tools were already used since the current user prompt — i.e.
    the conversation currently ends in a tool exchange (tool results or a fresh
    tool call). Each new user prompt starts a turn, so the tool schemas are
    re-sent at the start of every user prompt and omitted on the tool-chain
    follow-ups within it.
    """
    if not messages:
        return False
    last = messages[-1]
    role = last.get("role")
    if role == "tool" and last.get("tool_results"):
        return True
    if role == "assistant" and last.get("tool_calls"):
        return True
    return False


def _tool_schema_name(tool: Dict[str, Any]) -> str:
    """Extract a tool's name from either OpenAI-style or flat registry dicts."""
    if not isinstance(tool, dict):
        return ""
    fn = tool.get("function")
    if isinstance(fn, dict):
        return str(fn.get("name", "") or "")
    return str(tool.get("name", "") or "")


def _tools_used_this_turn(messages: List[Dict[str, Any]]) -> set[str]:
    """Collect tool names already called since the last user prompt."""
    used: set[str] = set()
    for msg in reversed(messages):
        if msg.get("role") == "user" and msg.get("content"):
            break
        for tc in msg.get("tool_calls") or []:
            name = tc.get("name", "")
            if name:
                used.add(name)
    return used


def _prune_tools_for_chain(tools: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the turn's active tool set stable across the whole chain.

    The engine routes the user request to a small active group (tool_groups.py)
    once at the start of the turn; every chained step keeps THAT set and never
    widens back to a base set (PlanFixes2 #3/#4/#5). Tools already used this
    turn are additionally preserved. Returns the original list when nothing is
    pruned so callers can distinguish 'no-op' from 'reduced'.
    """
    keep = {_tool_schema_name(t) for t in tools if _tool_schema_name(t)} | _tools_used_this_turn(messages)
    pruned = [t for t in tools if _tool_schema_name(t) in keep]
    if len(pruned) < len(tools):
        return pruned
    return tools


def _looks_like_tool_intent(text: str) -> bool:
    """Heuristic: does a text-only reply still read as a tool attempt (JSON
    action envelope or XML <tool_call>)? Used to decide whether a skipped-chained
    turn should retry WITH tools — a plain final answer should not.
    """
    if not text or not text.strip():
        return True
    if "<tool_call" in text:
        return True
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
        except Exception:
            return False
        if isinstance(data, dict) and ("action" in data or "tool_call" in data):
            return True
    return False


def _coerce_arguments(value: Any) -> Any:
    """Return tool-call arguments as a dict so json.dumps emits a JSON object.

    Older message-store code wrote arguments as a Python repr string; upstream
    OpenAI-style providers reject a non-object 'arguments'. Normalize such
    strings back to a dict before re-serializing.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        s = value.strip()
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            # Only fall back to literal_eval for short, dict-shaped strings so
            # untrusted/corrupted msg_store entries are never evaluated at large.
            if s.startswith("{") and len(s) <= 4096:
                try:
                    parsed = ast.literal_eval(s)
                except (ValueError, SyntaxError):
                    return {}
            else:
                return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


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
                        "tool_call_id": tr.get("tool_call_id", "") or f"call_{uuid.uuid4().hex[:12]}",
                    })
            else:
                oai_messages.append({
                    "role": "tool",
                    "content": msg.get("content", ""),
                    "tool_call_id": msg.get("tool_call_id", "") or f"call_{uuid.uuid4().hex[:12]}",
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
                            "arguments": json.dumps(_coerce_arguments(tc.get("arguments", {}))),
                        },
                    }
                    for tc in tool_calls
                ]
            oai_messages.append(entry)
            continue

        # user role
        oai_messages.append({"role": "user", "content": msg.get("content", "")})

    return oai_messages


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b:free"):
        from openai import OpenAI
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.default_model = model

    def _parse_chat_response(self, res: Any) -> Dict[str, Any]:
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
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": args,
                    })
            response_text = choice.message.content or ""
            if not response_text and not structured_calls:
                refusal = getattr(choice.message, "refusal", None)
                if refusal:
                    response_text = str(refusal)

        token_count = res.usage.total_tokens if res.usage else 0
        prompt_tokens = res.usage.prompt_tokens if res.usage else 0
        completion_tokens = res.usage.completion_tokens if res.usage else 0

        return {
            "status": "success",
            "response": response_text if response_text is not None else "",
            "tool_calls": structured_calls,
            "conversation_id": None,
            "usage": self._build_usage_dict(
                token_count,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
        }

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
        # OpenRouter: stable session identity maximizes sticky-routing prompt
        # cache locality across multi-turn agentic workflows (PlanFixes2 §12).
        session_id = kwargs.get("session_id") or getattr(self, "_session_id", None)
        if session_id:
            api_kwargs["session_id"] = session_id
        chained = _is_chained_turn(messages or [])
        tools_skipped = bool(tools) and OPENROUTER_SKIP_TOOLS_ON_CHAIN and chained
        if tools:
            if tools_skipped:
                pass  # omit tools entirely
            elif chained and OPENROUTER_PRUNE_TOOLS_ON_CHAIN:
                api_kwargs["tools"] = _prune_tools_for_chain(tools, messages or [])
            else:
                api_kwargs["tools"] = tools

        res = self.client.chat.completions.create(**api_kwargs)
        parsed = self._parse_chat_response(res)

        # OpenAI-compatible models can't emit tool_calls when the schema isn't in
        # the request — so a skipped chained turn may drop an intended tool call.
        # Retry once WITH tools only when the reply still reads as a tool attempt
        # (never on a plain final answer), so a skipped chain step doesn't always
        # cost a second call (which would negate the token saving).
        if (
            tools_skipped
            and not parsed.get("tool_calls")
            and tools
            and OPENROUTER_RETRY_SKIPPED_CHAIN
            and _looks_like_tool_intent(parsed.get("response", ""))
        ):
            api_kwargs["tools"] = tools
            try:
                res2 = self.client.chat.completions.create(**api_kwargs)
            except Exception:
                return parsed
            parsed2 = self._parse_chat_response(res2)
            if parsed2.get("tool_calls"):
                parsed = parsed2
            elif parsed2.get("response") and not parsed.get("response"):
                parsed = parsed2
        return parsed

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
        chained = _is_chained_turn(messages or [])
        tools_skipped = bool(tools) and OPENROUTER_SKIP_TOOLS_ON_CHAIN and chained
        if tools:
            if tools_skipped:
                pass  # omit tools entirely
            elif chained and OPENROUTER_PRUNE_TOOLS_ON_CHAIN:
                api_kwargs["tools"] = _prune_tools_for_chain(tools, messages or [])
            else:
                api_kwargs["tools"] = tools

        stream = self.client.chat.completions.create(**api_kwargs)

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
