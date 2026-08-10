"""FastAPI server application — global state, middleware, and startup."""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.tools import registry, log_output, KERNEL_AVAILABLE
from agent_core.config import (
    AGENT_PORT,
    CODEBASE_ROOT,
    JWT_SECRET,
    CORS_ORIGINS,
    DEBUG_DUMP_ENABLED,
    SERVER_STEP_DELAY,
    get_provider_catalog,
    resolve_active_provider,
    resolve_active_tool_mode,
    resolve_active_tool_packs,
    resolve_active_tool_names,
    resolve_default_model,
    resolve_context_window,
    SYSTEM_PROMPT_CORE_ONLY,
    RATE_LIMIT_LLM_CALLS,
    RATE_LIMIT_TOOL_WRITES,
    load_config,
)
from agent_core.secrets_redactor import redact
from agent_core.rate_limiter import RateLimiter
from agent_core.audit_log import AuditLog
from agent_core.workspace import (
    WORKSPACE_ROOT,
    resolve as ws_resolve,
    PathEscapeError,
    get_user_workspace_root,
    set_user_workspace,
    clear_user_context,
)
from functools import partial

from agent_core.prompts import load_system_prompt
from agent_core.providers_setup import build_orchestrator, switch_active
from agent_core.loop import iter_agent_events as _iter_agent_events_base
from agent_core.auto_research import run_auto_research
from agent_core.message_store import MessageStore
from agent_core.planning.local_planner import LocalPlanner

if DEBUG_DUMP_ENABLED:
    open(os.path.join(CODEBASE_ROOT, "tui_output.txt"), "w").close()

ACTIVE_TOOLS_DICT = registry.get_tools(
    categories=resolve_active_tool_packs(),
    names=resolve_active_tool_names() or None,
)

active_provider = resolve_active_provider()
active_model = resolve_default_model(active_provider)
active_context_window = resolve_context_window(active_provider, active_model)

orchestrator, registered_providers, provider_models = build_orchestrator(
    default_provider=active_provider,
    default_model=active_model,
    include_mock=True,
)

_registered_names = {p["provider"] for p in registered_providers}
if active_provider not in orchestrator.providers:
    fallback = next(
        (p for p in registered_providers if p["provider"] != "mock"),
        next(iter(registered_providers), None),
    )
    if fallback:
        active_provider = fallback["provider"]
        active_model = fallback["model"]
        orchestrator.default_provider = active_provider
        orchestrator.default_model = active_model
        log_output(f"[Server] Preferred provider unavailable; using {active_provider}/{active_model}")
elif active_provider == "mock" and "mock" in orchestrator.providers:
    orchestrator.default_provider = "mock"
    orchestrator.default_model = provider_models.get("mock", "mock")
    active_model = orchestrator.default_model
else:
    orchestrator.default_provider = active_provider
    orchestrator.default_model = active_model

active_context_window = resolve_context_window(active_provider, active_model)

log_output(
    f"[Server] Active provider={active_provider} model={active_model} "
    f"registered={sorted(_registered_names)}"
)

SYSTEM_PROMPT = load_system_prompt(
    active_packs=resolve_active_tool_packs(),
    mode=resolve_active_tool_mode(),
    core_only=SYSTEM_PROMPT_CORE_ONLY,
)
workspace_root = WORKSPACE_ROOT
conversations: dict[str, Optional[str]] = {}
user_sessions: dict[str, str] = {}
msg_store = MessageStore()
rate_limiter = RateLimiter()
audit_log = AuditLog()


def get_or_create_session(user_key: str) -> str:
    """Stable server-side session id per user, persisted across turns.

    Provider conversation_ids are often null (e.g. openrouter free models),
    so message history is keyed by this id instead of the provider thread.
    """
    sid = user_sessions.get(user_key)
    if not sid:
        sid = f"session_{user_key}_{time.time_ns()}"
        user_sessions[user_key] = sid
    return sid


def reset_session(user_key: str) -> None:
    user_sessions.pop(user_key, None)

local_planner = None
_local_cfg = load_config().get("local_model", {})
if _local_cfg.get("enabled"):
    from agent_core.providers.ollama_provider import OllamaProvider
    _ollama = OllamaProvider(
        model=_local_cfg.get("model", "gemma-2-2b-it"),
        endpoint=_local_cfg.get("endpoint", "http://localhost:11434"),
        timeout=_local_cfg.get("timeout_seconds", 30),
    )
    local_planner = LocalPlanner(_ollama, _local_cfg)
    log_output(f"[Server] Local model enabled: {_local_cfg.get('model')} @ {_local_cfg.get('endpoint')}")

def iter_agent_events(*args, **kwargs):
    kwargs.setdefault("local_planner", local_planner)
    return _iter_agent_events_base(*args, **kwargs)

app = FastAPI(title="Agentic Unit PIE Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from agent_core.server.routes import (
    get_status,
    list_providers,
    switch_provider,
    get_file_tree,
    Read,
    get_audit_log,
)

from agent_core.server.ws_handler import websocket_agent

# Serve frontend at / (no-cache for development)
_frontend_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend"))
if os.path.isdir(_frontend_dir):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import Response
    class NoCacheStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return resp
    app.mount("/", NoCacheStaticFiles(directory=_frontend_dir, html=True), name="frontend")
