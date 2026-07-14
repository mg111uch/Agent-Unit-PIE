"""
agent_core/llm/llm_orchestrator.py

Unified multi-LLM orchestration layer.

Provides a single abstraction layer for routing LLM requests across
multiple providers (Gemini, OpenAI, OpenRouter, etc.).
"""

from __future__ import annotations

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Generator

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 60.0
RETRY_BACKOFF_BASE = 2.0


class LLMOrchestrator:
    """
    Universal LLM orchestration system.
    """

    def __init__(
        self,
        providers: Optional[Dict[str, Any]] = None,
        default_provider: str = "gemini",
        default_model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.providers = providers or {}
        self.default_provider = default_provider
        self.default_model = default_model
        self.config = config or {}
        self.total_requests = 0
        self.total_failures = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_retries = 0
        self.max_retries = DEFAULT_MAX_RETRIES
        self.timeout = DEFAULT_TIMEOUT

    def generate(
        self,
        prompt: str = "",
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        structured_output: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        started_at = time.time()
        self.total_requests += 1

        provider_name = provider or self.default_provider
        model_name = model or self.default_model

        logger.info(f"LLM request -> {provider_name}/{model_name}")

        last_error = ""
        for attempt in range(self.max_retries + 1):
            try:
                provider_client = self.providers.get(provider_name)
                if provider_client is None:
                    raise ValueError(f"Provider not found: {provider_name}")

                if attempt > 0:
                    backoff = RETRY_BACKOFF_BASE ** (attempt - 1)
                    logger.info(f"Retry {attempt}/{self.max_retries} after {backoff}s")
                    time.sleep(backoff)

                result = provider_client.generate(
                    prompt=prompt,
                    model=model_name,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    conversation_id=conversation_id,
                    structured_output=structured_output,
                    metadata=metadata or {},
                    tools=tools,
                    messages=messages,
                )

                usage = result.get("usage", {})
                self.total_tokens += int(usage.get("total_tokens", 0))
                self.total_cost += float(usage.get("estimated_cost", 0.0))
                self.total_retries += attempt

                return {
                    "status": "success",
                    "provider": provider_name,
                    "model": model_name,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id"),
                    "tool_calls": result.get("tool_calls"),
                    "raw_response": result,
                    "usage": usage,
                    "latency_seconds": round(time.time() - started_at, 3),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "retries": attempt,
                }

            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    break

        self.total_failures += 1
        logger.exception("LLM generation failed after retries.")
        return {
            "status": "error",
            "error": last_error,
            "provider": provider_name,
            "model": model_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retries": self.max_retries,
        }

    def register_provider(self, provider_name: str, provider_client: Any) -> None:
        self.providers[provider_name] = provider_client
        logger.info(f"Registered provider: {provider_name}")

    def remove_provider(self, provider_name: str) -> bool:
        if provider_name not in self.providers:
            return False
        del self.providers[provider_name]
        logger.info(f"Removed provider: {provider_name}")
        return True

    def generate_stream(
        self,
        prompt: str = "",
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> Generator[str, None, None]:
        """Stream tokens from the LLM provider.

        Yields incremental text chunks as they arrive from the provider.
        Falls back to the non-streaming generate() if the provider lacks
        generate_stream().
        """
        provider_name = provider or self.default_provider
        model_name = model or self.default_model
        provider_client = self.providers.get(provider_name)

        if provider_client is None:
            yield f"Error: Provider '{provider_name}' not found."
            return

        if hasattr(provider_client, "generate_stream"):
            try:
                yield from provider_client.generate_stream(
                    prompt=prompt,
                    model=model_name,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    messages=messages,
                )
                return
            except Exception as e:
                logger.warning(f"Streaming failed for {provider_name}, falling back: {e}")

        result = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider_name,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            messages=messages,
        )
        if result["status"] == "success":
            yield result.get("response", "")
        else:
            yield f"Error: {result.get('error', 'Generation failed')}"
