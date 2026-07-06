"""
llm/llm_orchestrator.py

Unified multi-LLM orchestration layer.

Provides a single abstraction layer for routing LLM requests across
multiple providers (Gemini, OpenAI, OpenRouter, etc.).
"""

from __future__ import annotations

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


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

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        structured_output: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        started_at = time.time()
        self.total_requests += 1

        provider_name = provider or self.default_provider
        model_name = model or self.default_model

        logger.info(f"LLM request -> {provider_name}/{model_name}")

        try:
            provider_client = self.providers.get(provider_name)
            if provider_client is None:
                raise ValueError(f"Provider not found: {provider_name}")

            result = provider_client.generate(
                prompt=prompt,
                model=model_name,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                conversation_id=conversation_id,
                structured_output=structured_output,
                metadata=metadata or {},
            )

            usage = result.get("usage", {})
            self.total_tokens += int(usage.get("total_tokens", 0))
            self.total_cost += float(usage.get("estimated_cost", 0.0))

            return {
                "status": "success",
                "provider": provider_name,
                "model": model_name,
                "response": result.get("response", ""),
                "conversation_id": result.get("conversation_id"),
                "raw_response": result,
                "usage": usage,
                "latency_seconds": round(time.time() - started_at, 3),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.total_failures += 1
            logger.exception("LLM generation failed.")
            return {
                "status": "error",
                "error": str(e),
                "provider": provider_name,
                "model": model_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
