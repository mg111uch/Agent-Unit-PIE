"""REST API routes for the agent server."""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException

from agent_core.server import app
from agent_core.server.auth import require_auth
from agent_core.server.audit import build_tree
import agent_core.server as _srv


@app.get("/api/status")
async def get_status():
    return {
        "status": "ok",
        "provider": _srv.active_provider,
        "model": _srv.active_model,
        "kernel": _srv.KERNEL_AVAILABLE,
        "tools": list(_srv.ACTIVE_TOOLS_DICT.keys()),
        "tool_packs": _srv.ACTIVE_TOOL_PACKS,
        "workspace": _srv.get_user_workspace_root() or _srv.workspace_root,
        "total_requests": _srv.orchestrator.total_requests,
        "total_failures": _srv.orchestrator.total_failures,
        "total_tokens": _srv.orchestrator.total_tokens,
        "total_cost": _srv.orchestrator.total_cost,
        "total_retries": getattr(_srv.orchestrator, "total_retries", 0),
        "sessions": len(_srv.msg_store.get_all_sessions()),
    }


@app.get("/api/providers")
async def list_providers(user: dict = Depends(require_auth)):
    full = _srv.get_provider_catalog()
    catalog = {}
    for item in _srv.registered_providers:
        name = item["provider"]
        data = full.get(name, {})
        models = list(data.get("models") or [])
        if item["model"] and item["model"] not in models:
            models = [item["model"], *models]
        if not models:
            models = [item["model"]]
        catalog[name] = {
            "models": models,
            "default_model": data.get("default_model") or item["model"],
        }
    return {
        "active": {"provider": _srv.active_provider, "model": _srv.active_model},
        "catalog": catalog,
        "registered": _srv.registered_providers,
    }


@app.post("/api/switch-provider")
async def switch_provider(data: dict, user: dict = Depends(require_auth)):
    provider = data.get("provider")
    model = data.get("model")
    if not provider or not model:
        raise HTTPException(status_code=400, detail="provider and model are required")
    result = _srv.switch_active(_srv.orchestrator, provider, model)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    _srv.active_provider = provider
    _srv.active_model = model
    _srv.log_output(f"[Server] Switched to {provider}/{model}")
    return {
        "status": "ok",
        "provider": provider,
        "model": model,
        "active": {"provider": _srv.active_provider, "model": _srv.active_model},
    }


@app.get("/api/files/tree")
async def get_file_tree(user: dict = Depends(require_auth)):
    root = _srv.set_user_workspace(str(user.get("id")))
    tree = build_tree(root)
    return {"root": root, "tree": tree}


@app.get("/api/files/read")
async def read_file(path: str, user: dict = Depends(require_auth)):
    try:
        _srv.set_user_workspace(str(user.get("id")))
        full = _srv.ws_resolve(path)
        if not os.path.exists(full):
            return {"error": f"File not found: {path}"}
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": path, "content": content}
    except _srv.PathEscapeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/audit")
async def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(require_auth),
):
    entries = _srv.audit_log.query(limit=limit, offset=offset)
    return {"entries": entries}
