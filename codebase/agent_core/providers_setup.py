"""Register LLM providers from environment — single place for CLI and server."""

from __future__ import annotations

import os
from typing import Any

from agent_core.config import PROVIDER_DEFAULTS, resolve_default_model, resolve_active_provider
from agent_core.llm_orchestrator import LLMOrchestrator


def _resolve_model(name: str, model_override: str | None = None) -> str:
    env_var = f"{name.upper()}_MODEL"
    return model_override or os.getenv(env_var) or os.getenv("AGENT_MODEL") or PROVIDER_DEFAULTS.get(name, "")


_PROVIDER_CONFIGS = [
    ("gemini",     "GEMINI_API_KEY",     "agent_core.providers.gemini_provider",     "GeminiProvider",     False),
    ("openrouter", "OPENROUTER_API_KEY", "agent_core.providers.openrouter_provider", "OpenRouterProvider", False),
    ("mock",       "",                   "agent_core.providers.mock_provider",       "MockProvider",       True),
]


def _register_provider(name: str, module_path: str, class_name: str, model: str, api_key: str, orchestrator: LLMOrchestrator) -> tuple[dict[str, str], dict[str, str]]:
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    kw = {"model": model}
    if api_key:
        kw["api_key"] = api_key
    orchestrator.register_provider(name, cls(**kw))
    return {"provider": name, "model": model}, {name: model}


def build_orchestrator(
    default_provider: str | None = None,
    default_model: str | None = None,
    *,
    include_mock: bool = False,
    model_override: str | None = None,
) -> tuple[LLMOrchestrator, list[dict[str, str]], dict[str, str]]:
    if default_provider is None:
        default_provider = resolve_active_provider()
    resolved_default = resolve_default_model(default_provider, default_model)
    orchestrator = LLMOrchestrator(
        default_provider=default_provider,
        default_model=resolved_default,
    )
    registered: list[dict[str, str]] = []
    provider_models: dict[str, str] = {}

    for name, key_env, module_path, class_name, is_mock in _PROVIDER_CONFIGS:
        if is_mock and not include_mock:
            continue
        api_key = os.getenv(key_env) if key_env else ""
        if is_mock:
            model = PROVIDER_DEFAULTS.get(name, "")
            reg_entry, pm = _register_provider(name, module_path, class_name, model, "", orchestrator)
            registered.append(reg_entry)
            provider_models.update(pm)
            continue
        if not api_key:
            continue
        model = _resolve_model(name, model_override)
        reg_entry, pm = _register_provider(name, module_path, class_name, model, api_key, orchestrator)
        registered.append(reg_entry)
        provider_models.update(pm)

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
