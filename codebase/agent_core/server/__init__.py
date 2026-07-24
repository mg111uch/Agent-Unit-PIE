"""FastAPI server application — global state, middleware, and startup."""

from __future__ import annotations

import os
import sys
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.tools import registry, log_output, KERNEL_AVAILABLE
from agent_core.tools.registry import CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT
from agent_core.config import (
    AGENT_PORT,
    JWT_SECRET,
    CORS_ORIGINS,
    SERVER_STEP_DELAY,
    get_provider_catalog,
    resolve_active_provider,
    resolve_default_model,
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
from agent_core.prompts import load_system_prompt
from agent_core.providers_setup import build_orchestrator, switch_active
from agent_core.loop import iter_agent_events
from agent_core.auto_research import run_auto_research
from agent_core.message_store import MessageStore

_TOOL_PACKS_ENV = os.getenv("AGENT_TOOL_PACKS")
if _TOOL_PACKS_ENV:
    ACTIVE_TOOL_PACKS = [p.strip() for p in _TOOL_PACKS_ENV.split(",")]
else:
    _config_tool_packs = load_config().get("tool_packs")
    ACTIVE_TOOL_PACKS = _config_tool_packs if _config_tool_packs else [CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_GIT]

ACTIVE_TOOLS_DICT = registry.get_tools(categories=ACTIVE_TOOL_PACKS)

active_provider = resolve_active_provider()
active_model = resolve_default_model(active_provider)

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

log_output(
    f"[Server] Active provider={active_provider} model={active_model} "
    f"registered={sorted(_registered_names)}"
)

SYSTEM_PROMPT = load_system_prompt(tools_dict=ACTIVE_TOOLS_DICT, active_packs=ACTIVE_TOOL_PACKS)
workspace_root = WORKSPACE_ROOT
conversations: dict[str, Optional[str]] = {}
msg_store = MessageStore()
rate_limiter = RateLimiter()
audit_log = AuditLog()

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
    read_file,
    get_audit_log,
)

from agent_core.server.ws_handler import websocket_agent

# Serve frontend at /
_frontend_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend"))
if os.path.isdir(_frontend_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
