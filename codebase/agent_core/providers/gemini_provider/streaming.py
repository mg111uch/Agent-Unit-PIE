"""Gemini streaming mixin (Interactions + stateless generateContent).

Three sub-paths mirror the non-streaming dispatch: stateless contents stream,
stateful steps stream (with previous_interaction_id), and plain prompt stream.
"""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Optional

from agent_core import config as cfg
from agent_core.providers.gemini_provider.format import _format_tool_for_gemini, _tools_for_generate_content
from agent_core.providers.gemini_provider.messages import (
    _is_chained_turn,
    _messages_to_contents,
    _messages_to_steps,
    _prune_gc_tools,
)
from agent_core.providers.gemini_provider.parse import _get


class StreamMixin:
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
            if cfg.GEMINI_STATELESS:
                yield from self._stream_stateless(
                    messages, model, system_prompt, temperature, max_tokens, tools,
                )
                return
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

    def _stream_stateless(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]],
    ) -> Generator[str, None, None]:
        contents, extracted_system = _messages_to_contents(messages)
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "(continue)"}]}]
        config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        sys_inst = system_prompt or extracted_system
        gc_tools = _tools_for_generate_content(tools)
        chained = _is_chained_turn(messages)
        if chained and gc_tools and cfg.GEMINI_PRUNE_TOOLS_ON_CHAIN:
            gc_tools = _prune_gc_tools(gc_tools, messages)
        # Implicit cache (Phase 3): keep the system prefix byte-identical
        # so Gemini auto-caches it; explicit only as fallback.
        if cfg.GEMINI_IMPLICIT_CACHE:
            if sys_inst:
                config["system_instruction"] = sys_inst
            if gc_tools:
                config["tools"] = gc_tools
        else:
            cache_name = None
            if self._gemini_cache is not None and cfg.GEMINI_STATELESS_CACHE:
                cache_name = self._gemini_cache.existing(
                    (system_prompt or sys_inst or "").strip(), gc_tools, sys_only=False,
                )
            if cache_name:
                config["cached_content"] = cache_name
            else:
                if not chained and sys_inst:
                    config["system_instruction"] = sys_inst
                if gc_tools:
                    config["tools"] = gc_tools
        stream = self.client.models.generate_content_stream(
            model=model or self.default_model, contents=contents, config=config,
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text