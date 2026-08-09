"""Gemini Interactions API mixin.

Server-side chaining paths (`previous_interaction_id`): the initial turn built
from internal messages, stateful chained turns that send only the pending tool
results, and the plain prompt path. The skip-tools-with-retry discipline is
shared via _send_interaction.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from agent_core import config as cfg
from agent_core.context_budget import estimate_gemini_request, format_budget, format_wire_vs_actual
from agent_core.providers.gemini_provider.format import (
    _format_tool_for_gemini,
    _tool_calls_valid,
    _tools_fingerprint,
)
from agent_core.providers.gemini_provider.messages import _messages_to_steps
from agent_core.providers.gemini_provider.parse import _parse_interaction


def _wire_profile(model: str, call_kwargs: dict) -> None:
    """Emit the per-call wire estimate for an Interactions request (PlanFixes2 §7)."""
    if not cfg.DEBUG_DUMP_ENABLED:
        return
    wire = estimate_gemini_request(
        contents=call_kwargs.get("input"),
        system_instruction=call_kwargs.get("system_instruction"),
        tools=call_kwargs.get("tools"),
    )
    print(format_budget(wire, label=f"WIRE interaction {model}"), flush=True)


class InteractionsMixin:
    def _generate_interaction_call(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        conversation_id: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Plain-prompt Interactions call (no message history)."""
        call_kwargs: dict[str, Any] = {"model": model}

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

        return self._send_interaction(call_kwargs, tools, conversation_id=conversation_id)

    def _generate_initial_from_messages(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """First Interactions turn: store history server-side for later chaining."""
        steps, sys_inst = _messages_to_steps(messages)

        call_kwargs: dict[str, Any] = {
            "model": model,
            "input": steps,
        }
        if system_prompt or sys_inst:
            call_kwargs["system_instruction"] = system_prompt or sys_inst
        if tools:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
            self._last_tools_fp = _tools_fingerprint(tools)

        _wire_profile(model=model, call_kwargs=call_kwargs)
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
                    if name == "parse" or not call_id:
                        text = tr.get("result", "")
                        if text:
                            last_user = text
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
        elif last_user:
            input_data = last_user
        else:
            input_data = "(continue)"

        call_kwargs: dict[str, Any] = {
            "model": model,
            "previous_interaction_id": conversation_id,
            "input": input_data,
        }

        return self._send_interaction(call_kwargs, tools, conversation_id=conversation_id)

    def _send_interaction(
        self,
        call_kwargs: dict[str, Any],
        tools: Optional[List[Dict[str, Any]]],
        *,
        conversation_id: Optional[str],
    ) -> Dict[str, Any]:
        """One interactions call with the skip-tools retry discipline.

        On a chained turn (conversation_id set) and unchanged tool fingerprint,
        tools can be omitted because the schema persisted server-side; if the
        call fails, or the model hallucinated tool names/args without seeing a
        schema, retry once WITH tools.
        """
        fp = _tools_fingerprint(tools)
        skip_tools = bool(
            conversation_id
            and fp
            and cfg.GEMINI_SKIP_TOOLS_ON_CHAIN
            and fp == self._last_tools_fp
        )
        if not skip_tools and fp:
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
        self._last_tools_fp = fp
        _wire_profile(model=call_kwargs.get("model", ""), call_kwargs=call_kwargs)

        try:
            res = self.client.interactions.create(**call_kwargs)
        except Exception:
            if "tools" not in call_kwargs and fp:
                call_kwargs["tools"] = _format_tool_for_gemini(tools)
                res = self.client.interactions.create(**call_kwargs)
            else:
                raise
        parsed = _parse_interaction(res)
        if skip_tools and fp and not _tool_calls_valid(tools, parsed):
            call_kwargs["tools"] = _format_tool_for_gemini(tools)
            try:
                res = self.client.interactions.create(**call_kwargs)
            except Exception:
                pass
            else:
                parsed = _parse_interaction(res)
        return parsed