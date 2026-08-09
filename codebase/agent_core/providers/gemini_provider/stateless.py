"""Gemini stateless generateContent mixin.

Client-managed history: the (client-compacted) conversation is sent fully
self-contained every call. Uses the classic generateContent API, NOT
interactions with store=False (which rejects tool follow-ups with 400).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core import config as cfg
from agent_core.context_budget import estimate_gemini_request, format_budget
from agent_core.providers.gemini_provider.cache import GeminiContextCache
from agent_core.providers.gemini_provider.format import (
    _tool_calls_valid,
    _tools_for_generate_content,
)
from agent_core.providers.gemini_provider.messages import (
    _is_chained_turn,
    _messages_to_contents,
    _prune_gc_tools,
)
from agent_core.providers.gemini_provider.parse import _parse_generate_content


class StatelessMixin:
    def _generate_stateless(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Client-managed history via the classic generateContent API.

        Fully self-contained per call: the (client-compacted) conversation is
        sent every time, so billed context is bounded by our compaction.
        """
        contents, sys_inst = _messages_to_contents(messages)
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "(continue)"}]}]

        sys_text = (system_prompt or sys_inst or "").strip()
        gc_tools = _tools_for_generate_content(tools)
        chained = _is_chained_turn(messages)
        skip_schemas = cfg.GEMINI_STATELESS_SKIP_SCHEMAS
        # Phase 3: prefer Gemini's IMPLICIT caching. Gemini 2.5+ automatically
        # caches a stable repeated request prefix; we keep the system prefix
        # byte-identical on every call so it is billed at the cached-input rate,
        # instead of issuing explicit caches.create (which the PlanFixes2 model
        # test showed contributing zero hits). Explicit path stays as fallback.
        implicit_cache = cfg.GEMINI_IMPLICIT_CACHE
        use_cache = cfg.GEMINI_STATELESS_CACHE and not implicit_cache

        if self._gemini_cache is None:
            self._gemini_cache = GeminiContextCache(self.client, model)
        cache = self._gemini_cache

        config: dict[str, Any] = {"temperature": temperature, "max_output_tokens": max_tokens}
        cache_name: Optional[str] = None

        if implicit_cache:
            # Always re-send the full system prompt (its prefix is what Gemini
            # implicitly caches) plus a lean tool set; per-chain pruning keeps
            # serving tokens low without fragmenting the cached system prefix.
            if sys_text:
                config["system_instruction"] = sys_text
            cfg_tools = gc_tools
            if chained and cfg_tools and cfg.GEMINI_PRUNE_TOOLS_ON_CHAIN:
                cfg_tools = _prune_gc_tools(cfg_tools, messages)
            if cfg_tools:
                config["tools"] = cfg_tools
            use_tools = True
        else:
            # Legacy explicit cache fallback (GEMINI_IMPLICIT_CACHE=0).
            if chained:
                # Tool-chaining step within a turn: do NOT resend the system
                # prompt — it was already sent at the start of this turn. When a
                # cached prefix exists the model still sees it (billed at the
                # discounted cached-input rate); otherwise it continues from the
                # conversation alone. Schemas omitted only when skip_schemas.
                use_tools = not skip_schemas
                if use_tools and gc_tools and cfg.GEMINI_PRUNE_TOOLS_ON_CHAIN:
                    gc_tools = _prune_gc_tools(gc_tools, messages)
                cache_name = cache.existing(sys_text, gc_tools, sys_only=False) if use_cache else None
                if cache_name:
                    config["cached_content"] = cache_name
                elif use_tools and gc_tools:
                    config["tools"] = gc_tools
            else:
                # Start of a turn: send the full system prompt + schemas (cached).
                use_tools = True
                cache_name = cache.ensure(sys_text, gc_tools, sys_only=False) if use_cache else None
                if cache_name:
                    config["cached_content"] = cache_name
                else:
                    if sys_text:
                        config["system_instruction"] = sys_text
                    if gc_tools:
                        config["tools"] = gc_tools

        try:
            wire = estimate_gemini_request(
                contents=contents,
                system_instruction=config.get("system_instruction"),
                tools=config.get("tools"),
            )
            if cfg.DEBUG_DUMP_ENABLED:
                print(format_budget(wire, label=f"WIRE stateless {model}"), flush=True)
            res = self.client.models.generate_content(
                model=model, contents=contents, config=config,
            )
        except Exception:
            # Stale/expired cache reference — drop it and retry once inline.
            if cache_name:
                cache.invalidate()
                config = {"temperature": temperature, "max_output_tokens": max_tokens}
                if not chained and sys_text:
                    config["system_instruction"] = sys_text
                if use_tools and gc_tools:
                    config["tools"] = gc_tools
                wire = estimate_gemini_request(
                    contents=contents,
                    system_instruction=config.get("system_instruction"),
                    tools=config.get("tools"),
                )
                if cfg.DEBUG_DUMP_ENABLED:
                    print(format_budget(wire, label="WIRE stateless-retry"), flush=True)
                res = self.client.models.generate_content(
                    model=model, contents=contents, config=config,
                )
            else:
                raise
        parsed = _parse_generate_content(res)
        if cfg.DEBUG_DUMP_ENABLED and wire is not None:
            usage = parsed.get("usage", {})
            print(format_wire_vs_actual(wire, usage), flush=True)

        # Chained turn with schemas skipped: if the model still emitted a real
        # tool call (it couldn't have seen a schema), retry once WITH tools.
        if (
            chained
            and use_tools is False
            and gc_tools
            and parsed.get("tool_calls")
            and _tool_calls_valid(tools, parsed)
        ):
            full_cache = cache.ensure(sys_text, gc_tools, sys_only=False) if use_cache else None
            retry_config: dict[str, Any] = {"temperature": temperature, "max_output_tokens": max_tokens}
            if full_cache:
                retry_config["cached_content"] = full_cache
            elif gc_tools:
                retry_config["tools"] = gc_tools
            try:
                res = self.client.models.generate_content(
                    model=model, contents=contents, config=retry_config,
                )
            except Exception:
                pass
            else:
                parsed = _parse_generate_content(res)

        parsed["conversation_id"] = None
        return parsed