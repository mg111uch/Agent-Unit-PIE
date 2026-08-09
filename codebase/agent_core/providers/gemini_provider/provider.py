"""GeminiProvider concrete class: dispatch + state.

Composes the Interactions (chained), stateless generateContent, and streaming
mixins. Public surface identical to the historical single-file module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core import config as cfg
from agent_core.providers import BaseLLMProvider
from agent_core.providers.gemini_provider.cache import GeminiContextCache
from agent_core.providers.gemini_provider.interaction import InteractionsMixin
from agent_core.providers.gemini_provider.stateless import StatelessMixin
from agent_core.providers.gemini_provider.streaming import StreamMixin


class GeminiProvider(InteractionsMixin, StatelessMixin, StreamMixin, BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash"):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.default_model = model
        self._supports_stateful = True
        self._last_tools_fp: Optional[str] = None
        self._gemini_cache: Optional[GeminiContextCache] = None

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
            if cfg.GEMINI_STATELESS:
                # Client-managed history: send the full (compacted) conversation
                # every call with store=False so billed context is bounded by our
                # compaction, not by Gemini's server-side chain retention.
                return self._generate_stateless(
                    messages,
                    model or self.default_model,
                    system_prompt,
                    tools,
                )
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

        return self._generate_interaction_call(
            prompt,
            model or self.default_model,
            system_prompt,
            conversation_id,
            tools,
        )