"""Register LLM providers from environment — single place for CLI and server."""

from __future__ import annotations

import os
from typing import Any

from agent_core.config import PROVIDER_DEFAULTS, resolve_default_model
from agent_core.llm.llm_orchestrator import LLMOrchestrator


def build_orchestrator(
    default_provider: str = "gemini",
    default_model: str | None = None,
    *,
    include_mock: bool = False,
    model_override: str | None = None,
) -> tuple[LLMOrchestrator, list[dict[str, str]], dict[str, str]]:
    """
    Build orchestrator and register available providers.

    Returns:
        (orchestrator, registered_providers, provider_models)
        registered_providers: [{"provider": name, "model": model}, ...]
        provider_models: {provider_name: model}
    """
    resolved_default = resolve_default_model(default_provider, default_model)
    orchestrator = LLMOrchestrator(
        default_provider=default_provider,
        default_model=resolved_default,
    )
    registered: list[dict[str, str]] = []
    provider_models: dict[str, str] = {}

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        gemini_model = (
            model_override
            or os.getenv("GEMINI_MODEL")
            or os.getenv("AGENT_MODEL")
            or PROVIDER_DEFAULTS["gemini"]
        )
        from agent_core.llm.providers.gemini_provider import GeminiProvider

        orchestrator.register_provider(
            "gemini",
            GeminiProvider(api_key=gemini_key, model=gemini_model),
        )
        registered.append({"provider": "gemini", "model": gemini_model})
        provider_models["gemini"] = gemini_model

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        openrouter_model = (
            model_override
            or os.getenv("OPENROUTER_MODEL")
            or PROVIDER_DEFAULTS["openrouter"]
        )
        from agent_core.llm.providers.openrouter_provider import OpenRouterProvider

        orchestrator.register_provider(
            "openrouter",
            OpenRouterProvider(api_key=openrouter_key, model=openrouter_model),
        )
        registered.append({"provider": "openrouter", "model": openrouter_model})
        provider_models["openrouter"] = openrouter_model

    if include_mock:
        from agent_core.llm.providers.mock_provider import MockProvider

        mock_model = PROVIDER_DEFAULTS["mock"]
        orchestrator.register_provider("mock", MockProvider(model=mock_model))
        registered.append({"provider": "mock", "model": mock_model})
        provider_models["mock"] = mock_model

    return orchestrator, registered, provider_models


def switch_active(
    orchestrator: LLMOrchestrator,
    provider: str,
    model: str,
) -> dict[str, Any]:
    """Update orchestrator defaults. Caller must update its own active_* state."""
    if provider not in orchestrator.providers:
        return {"error": f"Provider '{provider}' not registered"}
    orchestrator.default_provider = provider
    orchestrator.default_model = model
    return {"status": "ok", "provider": provider, "model": model}
