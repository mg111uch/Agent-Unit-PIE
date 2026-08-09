"""
agent_core/llm/llm_orchestrator.py

Unified multi-LLM orchestration layer.

Provides a single abstraction layer for routing LLM requests across
multiple providers (Gemini, OpenAI, OpenRouter, etc.).
"""

from __future__ import annotations

import time
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Generator

from agent_core.context_budget import build_budget, format_budget

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
        self.profile_records: list[dict[str, Any]] = []

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
        cancel_flag: Optional[threading.Event] = None,
    ) -> Dict[str, Any]:
        started_at = time.time()
        self.total_requests += 1
        call_num = self.total_requests

        provider_name = provider or self.default_provider
        model_name = model or self.default_model

        print(f"[LLM call #{call_num}] {provider_name}/{model_name}", flush=True)
        logger.info(f"LLM request -> {provider_name}/{model_name}")

        last_error = ""
        for attempt in range(self.max_retries + 1):
            if cancel_flag and cancel_flag.is_set():
                self.total_failures += 1
                return {
                    "status": "error",
                    "error": "cancelled",
                    "provider": provider_name,
                    "model": model_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "retries": attempt,
                }
            try:
                if attempt > 0:
                    backoff = RETRY_BACKOFF_BASE ** (attempt - 1)
                    logger.info(f"Retry {attempt}/{self.max_retries} after {backoff}s")
                    time.sleep(backoff)

                provider_client = self.providers.get(provider_name)
                if provider_client is None:
                    raise ValueError(f"Provider not found: {provider_name}")

                profile = build_budget(
                    system_prompt=system_prompt,
                    prompt=prompt,
                    tools=tools,
                    messages=messages,
                )

                # Stable session identity for provider-side prompt-cache routing
                # (OpenRouter sticky sessions) — never optional on a chain.
                provider_extra: Dict[str, Any] = {}
                sess = (metadata or {}).get("session_id")
                if sess:
                    provider_extra["session_id"] = sess

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
                    **provider_extra,
                )

                usage = result.get("usage", {})
                profile.apply_usage(usage)
                self.profile_records.append({
                    "call_num": call_num,
                    "provider": provider_name,
                    "model": model_name,
                    "attempt": attempt,
                    **profile.to_dict(),
                })
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
                err_lower = str(e).lower()
                # Non-retriable: auth errors, 4xx (except 429), or our own cancellation
                if any(x in err_lower for x in ["401", "403", "unauthorized", "authentication",
                                                   "permission denied", "not found", "model not found",
                                                   "invalid api key"]):
                    break
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

    def profile_summary(
        self,
        *,
        latest_only: bool = False,
        include_total: bool = True,
    ) -> list[str]:
        """Human-readable token breakdown of recorded LLM calls."""
        recs = self.profile_records[-1:] if latest_only else self.profile_records
        if not recs:
            return ["No LLM calls profiled yet."]

        def _to_budget(r: dict):
            return type("_B", (), {k: int(v or 0) for k, v in r.items()
                                   if k not in ("call_num", "provider", "model",
                                                "attempt", "provider_source")})()

        lines = []
        for r in recs:
            lines.append(format_budget(
                _to_budget(r),
                label=f"call #{r.get('call_num')} {r.get('provider')}/{r.get('model')}",
            ))
        if include_total and len(recs) > 1:
            keys = ("system_tokens", "tool_schema_tokens", "history_tokens",
                    "tool_result_tokens", "user_tokens", "digest_tokens",
                    "fresh_input_tokens", "output_tokens", "billable_tokens")
            totals = {k: sum(int(r.get(k, 0) or 0) for r in recs) for k in keys}
            lines.append(f"TOTAL over {len(recs)} calls: {totals}")
        return lines

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
