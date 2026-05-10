"""
llm/llm_orchestrator.py

Unified multi-LLM orchestration layer.

Purpose
-------
Provides a single abstraction layer for interacting with:

- OpenAI
- Anthropic
- Gemini
- Local LLMs
- Ollama
- LM Studio
- future providers

Core Responsibilities
---------------------
- provider abstraction
- routing
- retries
- fallback models
- context injection
- structured outputs
- streaming support
- tool execution support
- cost tracking
- token tracking
- memory-aware prompting

This becomes the cognition gateway
for the entire agent_unit_pie architecture.
"""

from __future__ import annotations

import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Universal LLM orchestration system.
    """

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        providers: Optional[
            Dict[str, Any]
        ] = None,
        default_provider: str = "openai",
        default_model: Optional[str] = None,
        context_builder=None,
        tool_registry=None,
        config: Optional[
            Dict[str, Any]
        ] = None,
    ):

        self.providers = providers or {}

        self.default_provider = (
            default_provider
        )

        self.default_model = default_model

        self.context_builder = (
            context_builder
        )

        self.tool_registry = tool_registry

        self.config = config or {}

        # --------------------------------------------------------
        # STATS
        # --------------------------------------------------------

        self.total_requests = 0

        self.total_failures = 0

        self.total_tokens = 0

        self.total_cost = 0.0

    # ============================================================
    # MAIN GENERATION
    # ============================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[
            str
        ] = None,
        provider: Optional[
            str
        ] = None,
        model: Optional[
            str
        ] = None,
        context: Optional[
            Dict[str, Any]
        ] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        structured_output: bool = False,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Main LLM generation entrypoint.
        """

        started_at = time.time()

        self.total_requests += 1

        provider_name = (
            provider
            or self.default_provider
        )

        model_name = (
            model
            or self.default_model
        )

        logger.info(
            f"LLM request → "
            f"{provider_name}/{model_name}"
        )

        try:

            # ----------------------------------------------------
            # BUILD CONTEXT
            # ----------------------------------------------------

            final_prompt = (
                self.build_prompt(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                )
            )

            # ----------------------------------------------------
            # GET PROVIDER
            # ----------------------------------------------------

            provider_client = (
                self.providers.get(
                    provider_name
                )
            )

            if provider_client is None:

                raise ValueError(
                    f"Provider not found: "
                    f"{provider_name}"
                )

            # ----------------------------------------------------
            # GENERATE
            # ----------------------------------------------------

            result = (
                provider_client.generate(
                    prompt=final_prompt,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    structured_output=structured_output,
                    metadata=metadata or {},
                )
            )

            # ----------------------------------------------------
            # METRICS
            # ----------------------------------------------------

            usage = result.get(
                "usage",
                {},
            )

            self.total_tokens += int(
                usage.get(
                    "total_tokens",
                    0,
                )
            )

            self.total_cost += float(
                usage.get(
                    "estimated_cost",
                    0.0,
                )
            )

            # ----------------------------------------------------
            # FINAL RESULT
            # ----------------------------------------------------

            return {
                "status": "success",
                "provider": provider_name,
                "model": model_name,
                "response": result.get(
                    "response",
                    ""
                ),
                "raw_response": result,
                "usage": usage,
                "latency_seconds": round(
                    time.time() - started_at,
                    3,
                ),
                "timestamp": self.utc_now(),
            }

        except Exception as e:

            self.total_failures += 1

            logger.exception(
                "LLM generation failed."
            )

            return {
                "status": "error",
                "error": str(e),
                "provider": provider_name,
                "model": model_name,
                "timestamp": self.utc_now(),
            }

    # ============================================================
    # PROMPT BUILDING
    # ============================================================

    def build_prompt(
        self,
        prompt: str,
        system_prompt: Optional[
            str
        ] = None,
        context: Optional[
            Dict[str, Any]
        ] = None,
    ) -> str:
        """
        Build final context-aware prompt.
        """

        parts = []

        # --------------------------------------------------------
        # SYSTEM PROMPT
        # --------------------------------------------------------

        if system_prompt:

            parts.append(
                f"[SYSTEM]\n"
                f"{system_prompt}"
            )

        # --------------------------------------------------------
        # CONTEXT
        # --------------------------------------------------------

        if context:

            context_block = (
                self.serialize_context(
                    context
                )
            )

            parts.append(
                f"[CONTEXT]\n"
                f"{context_block}"
            )

        # --------------------------------------------------------
        # USER PROMPT
        # --------------------------------------------------------

        parts.append(
            f"[USER]\n{prompt}"
        )

        return "\n\n".join(parts)

    # ============================================================
    # CONTEXT SERIALIZATION
    # ============================================================

    def serialize_context(
        self,
        context: Dict[str, Any],
    ) -> str:
        """
        Serialize context safely.
        """

        try:

            return json.dumps(
                context,
                indent=2,
                ensure_ascii=False,
            )

        except Exception:

            logger.exception(
                "Context serialization failed."
            )

            return str(context)

    # ============================================================
    # TOOL EXECUTION
    # ============================================================

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute registered tool.
        """

        if self.tool_registry is None:

            return {
                "status": "error",
                "error": "tool_registry_missing",
            }

        tool = (
            self.tool_registry.get_tool(
                tool_name
            )
        )

        if tool is None:

            return {
                "status": "error",
                "error": (
                    f"tool_not_found: "
                    f"{tool_name}"
                ),
            }

        try:

            result = tool.execute(
                **arguments
            )

            return {
                "status": "success",
                "tool_name": tool_name,
                "result": result,
            }

        except Exception as e:

            logger.exception(
                f"Tool execution failed: "
                f"{tool_name}"
            )

            return {
                "status": "error",
                "tool_name": tool_name,
                "error": str(e),
            }

    # ============================================================
    # PROVIDER MANAGEMENT
    # ============================================================

    def register_provider(
        self,
        provider_name: str,
        provider_client: Any,
    ) -> None:
        """
        Register LLM provider.
        """

        self.providers[
            provider_name
        ] = provider_client

        logger.info(
            f"Registered provider: "
            f"{provider_name}"
        )

    def remove_provider(
        self,
        provider_name: str,
    ) -> bool:
        """
        Remove provider.
        """

        if (
            provider_name
            not in self.providers
        ):
            return False

        del self.providers[
            provider_name
        ]

        logger.info(
            f"Removed provider: "
            f"{provider_name}"
        )

        return True

    # ============================================================
    # FALLBACK GENERATION
    # ============================================================

    def generate_with_fallback(
        self,
        prompt: str,
        fallback_providers: List[str],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Attempt generation using fallback providers.
        """

        for provider_name in fallback_providers:

            result = self.generate(
                prompt=prompt,
                provider=provider_name,
                **kwargs,
            )

            if (
                result.get("status")
                == "success"
            ):
                return result

        return {
            "status": "error",
            "error": (
                "all_fallback_providers_failed"
            ),
        }

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:
        """
        Runtime orchestrator state.
        """

        return {
            "registered_providers": list(
                self.providers.keys()
            ),
            "default_provider": (
                self.default_provider
            ),
            "default_model": (
                self.default_model
            ),
            "total_requests": (
                self.total_requests
            ),
            "total_failures": (
                self.total_failures
            ),
            "total_tokens": (
                self.total_tokens
            ),
            "total_cost": round(
                self.total_cost,
                4,
            ),
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def utc_now() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()