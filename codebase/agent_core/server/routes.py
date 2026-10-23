"""REST API routes for the agent server."""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException

from agent_core.server import app
from agent_core.server.auth import require_auth
from agent_core.server.audit import build_tree
from agent_core.config import EXCLUDE_DIRS, SHOW_TOOL_TOKEN_USAGE, resolve_active_tool_packs
import agent_core.server as _srv

MAX_EDIT_BYTES = 2_000_000


@app.get("/api/status")
async def get_status():
    return {
        "status": "ok",
        "provider": _srv.active_provider,
        "model": _srv.active_model,
        "kernel": _srv.KERNEL_AVAILABLE,
        "tools": list(_srv.ACTIVE_TOOLS_DICT.keys()),
        "tool_packs": resolve_active_tool_packs(),
        "workspace": _srv.get_user_workspace_root() or _srv.workspace_root,
        "total_requests": _srv.orchestrator.total_requests,
        "total_failures": _srv.orchestrator.total_failures,
        "total_tokens": _srv.orchestrator.total_tokens,
        "total_cost": _srv.orchestrator.total_cost,
        "total_retries": getattr(_srv.orchestrator, "total_retries", 0),
        "sessions": len(_srv.msg_store.get_all_sessions()),
        "show_tool_token_usage": SHOW_TOOL_TOKEN_USAGE,
        "context_window": getattr(_srv, "active_context_window", 0),
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
    _srv.active_context_window = _srv.resolve_context_window(provider, model)
    _srv.log_output(f"[Server] Switched to {provider}/{model}")
    return {
        "status": "ok",
        "provider": provider,
        "model": model,
        "context_window": _srv.active_context_window,
        "active": {"provider": _srv.active_provider, "model": _srv.active_model},
    }


@app.get("/api/files/tree")
async def get_file_tree(user: dict = Depends(require_auth)):
    root = _srv.set_user_workspace(str(user.get("id")))
    tree = build_tree(root)
    return {"root": root, "tree": tree}


@app.get("/api/files/workspace")
async def get_workspace_files():
    root = _srv.workspace_root
    exclude_set = set(EXCLUDE_DIRS)
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        parts = rel_dir.split("/") if rel_dir != "." else []
        if any(p in exclude_set for p in parts):
            continue
        for fn in filenames:
            rel = os.path.join(rel_dir, fn) if rel_dir != "." else fn
            paths.append(rel)
    return {"root": root, "files": sorted(paths)}


def _workspace_root() -> str:
    return _srv.get_user_workspace_root() or _srv.workspace_root


def _rel(path: str) -> str:
    rel = os.path.relpath(path, _workspace_root()).replace("\\", "/")
    return "" if rel == "." else rel


@app.get("/api/files/ls")
async def list_dir(path: str = "", user: dict = Depends(require_auth)):
    _srv.set_user_workspace(str(user.get("id")))
    try:
        full = _srv.ws_resolve(path or ".")
    except _srv.PathEscapeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not os.path.isdir(full):
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")
    excluded = set(EXCLUDE_DIRS) | {"__pycache__", "node_modules"}
    entries = []
    try:
        names = sorted(os.listdir(full))
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    for name in names:
        if name.startswith(".") or name in excluded:
            continue
        item = os.path.join(full, name)
        if os.path.isdir(item):
            entries.append({"name": name, "type": "dir", "path": _rel(item)})
        elif os.path.isfile(item):
            entries.append({"name": name, "type": "file", "path": _rel(item)})
    entries.sort(key=lambda e: (e["type"] != "dir", e["name"].lower()))
    return {"path": _rel(full), "entries": entries}


@app.get("/api/files/read")
async def Read(path: str, user: dict = Depends(require_auth)):
    try:
        _srv.set_user_workspace(str(user.get("id")))
        full = _srv.ws_resolve(path)
        if not os.path.exists(full):
            return {"error": f"File not found: {path}"}
        if os.path.getsize(full) > MAX_EDIT_BYTES:
            return {"error": f"File too large to open ({os.path.getsize(full)} bytes)"}
        with open(full, "rb") as f:
            raw = f.read()
        if b"\x00" in raw[:8192]:
            return {"error": "Binary file — cannot open in editor"}
        return {"path": path, "content": raw.decode("utf-8", errors="replace")}
    except _srv.PathEscapeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/files/write")
async def write_file(data: dict, user: dict = Depends(require_auth)):
    path = data.get("path")
    content = data.get("content")
    if not isinstance(path, str) or not path.strip():
        raise HTTPException(status_code=400, detail="path is required")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content must be a string")
    if "\x00" in content:
        raise HTTPException(status_code=400, detail="Refusing to write binary content")
    size = len(content.encode("utf-8"))
    if size > MAX_EDIT_BYTES:
        raise HTTPException(status_code=413, detail=f"Content too large ({size} bytes)")
    _srv.set_user_workspace(str(user.get("id")))
    try:
        full = _srv.ws_resolve(path)
    except _srv.PathEscapeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if os.path.isdir(full):
        raise HTTPException(status_code=400, detail=f"Not a file: {path}")
    from agent_core.tools.undo_ops import save_checkpoint

    save_checkpoint(_rel(full))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return {"status": "ok", "path": _rel(full), "bytes": size}


@app.post("/api/files/rename")
async def rename_file(data: dict, user: dict = Depends(require_auth)):
    path = data.get("path")
    new_path = data.get("new_path")
    if not isinstance(path, str) or not isinstance(new_path, str):
        raise HTTPException(status_code=400, detail="path and new_path are required")
    _srv.set_user_workspace(str(user.get("id")))
    try:
        src = _srv.ws_resolve(path)
        dst = _srv.ws_resolve(new_path)
    except _srv.PathEscapeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not os.path.exists(src):
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    if os.path.exists(dst):
        raise HTTPException(status_code=400, detail=f"Target already exists: {new_path}")
    if not os.path.isdir(os.path.dirname(dst)):
        raise HTTPException(status_code=400, detail="Target parent directory does not exist")
    try:
        os.rename(src, dst)
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "path": _rel(dst)}


@app.post("/api/files/delete")
async def delete_file(data: dict, user: dict = Depends(require_auth)):
    path = data.get("path")
    if not isinstance(path, str) or not path.strip():
        raise HTTPException(status_code=400, detail="path is required")
    _srv.set_user_workspace(str(user.get("id")))
    try:
        full = _srv.ws_resolve(path)
    except _srv.PathEscapeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if full == os.path.realpath(_workspace_root()):
        raise HTTPException(status_code=400, detail="Refusing to delete the workspace root")
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    rel = _rel(full)
    try:
        if os.path.isdir(full):
            os.rmdir(full)
        else:
            os.remove(full)
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "path": rel}


@app.get("/api/audit")
async def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(require_auth),
):
    entries = _srv.audit_log.query(limit=limit, offset=offset)
    return {"entries": entries}
