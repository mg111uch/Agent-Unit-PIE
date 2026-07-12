"""
server.py - FastAPI WebSocket server for browser-based agent control.

Thin transport layer over agent_core (loop, providers, prompts).
"""

from __future__ import annotations

import os
import sys
import asyncio
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt as pyjwt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.tools import TOOLS, log_output, KERNEL_AVAILABLE
from agent_core.config import (
    AGENT_PORT,
    JWT_SECRET,
    SERVER_STEP_DELAY,
    get_provider_catalog,
    resolve_active_provider,
    resolve_default_model,
)
from agent_core.workspace import WORKSPACE_ROOT, resolve as ws_resolve, PathEscapeError
from agent_core.prompts import load_system_prompt
from agent_core.providers_setup import build_orchestrator, switch_active
from agent_core.agent_loop import iter_agent_events
from agent_core.auto_research import run_auto_research
from agent_core.commands import parse_command

active_provider = resolve_active_provider()
active_model = resolve_default_model(active_provider)

orchestrator, registered_providers, provider_models = build_orchestrator(
    default_provider=active_provider,
    default_model=active_model,
    include_mock=True,
)

# Prefer a real registered provider; only use mock if nothing else is available
# or AGENT_PROVIDER=mock explicitly.
_registered_names = {p["provider"] for p in registered_providers}
if active_provider not in orchestrator.providers:
    # e.g. config says gemini but no GEMINI_API_KEY — pick first non-mock if any
    fallback = next(
        (p for p in registered_providers if p["provider"] != "mock"),
        next(iter(registered_providers), None),
    )
    if fallback:
        active_provider = fallback["provider"]
        active_model = fallback["model"]
        orchestrator.default_provider = active_provider
        orchestrator.default_model = active_model
        log_output(
            f"[Server] Preferred provider unavailable; using {active_provider}/{active_model}"
        )
elif active_provider == "mock" and "mock" in orchestrator.providers:
    orchestrator.default_provider = "mock"
    orchestrator.default_model = provider_models.get("mock", "mock")
    active_model = orchestrator.default_model
else:
    # Keep globals in sync with orchestrator for the preferred real provider
    orchestrator.default_provider = active_provider
    orchestrator.default_model = active_model

log_output(
    f"[Server] Active provider={active_provider} model={active_model} "
    f"registered={sorted(_registered_names)}"
)

SYSTEM_PROMPT = load_system_prompt()
workspace_root = WORKSPACE_ROOT
conversations: dict[str, Optional[str]] = {}

app = FastAPI(title="Agentic Unit PIE Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_token(token: str) -> Optional[dict]:
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


@app.get("/api/status")
async def get_status():
    return {
        "status": "ok",
        "provider": active_provider,
        "model": active_model,
        "kernel": KERNEL_AVAILABLE,
        "tools": list(TOOLS.keys()),
        "workspace": workspace_root,
    }


@app.get("/api/providers")
async def list_providers():
    """Catalog is limited to providers that are actually registered (have API keys)."""
    full = get_provider_catalog()
    catalog = {}
    for item in registered_providers:
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
        "active": {"provider": active_provider, "model": active_model},
        "catalog": catalog,
        "registered": registered_providers,
    }


@app.post("/api/switch-provider")
async def switch_provider(data: dict):
    global active_provider, active_model
    provider = data.get("provider")
    model = data.get("model")
    if not provider or not model:
        raise HTTPException(status_code=400, detail="provider and model are required")
    result = switch_active(orchestrator, provider, model)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    active_provider = provider
    active_model = model
    log_output(f"[Server] Switched to {provider}/{model}")
    return {
        "status": "ok",
        "provider": provider,
        "model": model,
        "active": {"provider": active_provider, "model": active_model},
    }


@app.get("/api/files/tree")
async def get_file_tree():
    tree = _build_tree(workspace_root)
    return {"root": workspace_root, "tree": tree}


def _build_tree(dir_path: str, max_depth: int = 4, depth: int = 0):
    if depth > max_depth:
        return {
            "name": os.path.basename(dir_path),
            "type": "dir",
            "children": [],
            "truncated": True,
        }
    try:
        entries = []
        for name in sorted(os.listdir(dir_path)):
            if name.startswith(".") or name.startswith("__pycache__"):
                continue
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                entries.append(_build_tree(full, max_depth, depth + 1))
            else:
                entries.append({"name": name, "type": "file"})
        return {
            "name": os.path.basename(dir_path),
            "type": "dir",
            "children": entries,
        }
    except PermissionError:
        return {
            "name": os.path.basename(dir_path),
            "type": "dir",
            "children": [],
            "error": "permission denied",
        }


@app.get("/api/files/read")
async def read_file(path: str):
    try:
        full = ws_resolve(path)
        if not os.path.exists(full):
            return {"error": f"File not found: {path}"}
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": path, "content": content}
    except PathEscapeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket, token: str = Query(...)):
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    await websocket.accept()
    user_key = str(user.get("id"))
    await websocket.send_json(
        {
            "type": "connected",
            "user": {"id": user.get("id"), "username": user.get("username")},
        }
    )
    conv_id = conversations.get(user_key)

    async def heartbeat():
        while True:
            try:
                await asyncio.sleep(25)
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                content = data.get("content", "")
                conv_id = await handle_chat(websocket, content, conv_id)
                conversations[user_key] = conv_id
            elif msg_type == "reset":
                conv_id = None
                conversations[user_key] = None
                await websocket.send_json({"type": "reset", "status": "ok"})
            elif msg_type == "slash":
                command = data.get("command", "")
                args = data.get("args", "")
                conv_id = await handle_slash(websocket, command, args)
                conversations[user_key] = conv_id
    except WebSocketDisconnect:
        log_output(f"[WS] User {user.get('username')} disconnected")
    finally:
        hb_task.cancel()


async def handle_slash(
    websocket: WebSocket,
    command: str,
    args: str,
) -> Optional[str]:
    # New session: clear conversation memory (Gemini previous_interaction_id, etc.)
    if command in ("/new", "/clear", "/reset", "/session"):
        await websocket.send_json(
            {
                "type": "reset",
                "status": "ok",
                "message": "New session started. You can change the model now.",
            }
        )
        return None

    if command == "/argu":
        parts = args.split(None, 1)
        mode = parts[0] if parts else None
        topic = parts[1] if len(parts) > 1 else None
        if not mode or not topic:
            await websocket.send_json(
                {"type": "error", "message": "Usage: /argu explore <topic>"}
            )
            return None
        try:
            from modules.argu_god.engine.cli import argu_cli
            output = argu_cli(mode, topic)
            await websocket.send_json(
                {"type": "final", "content": output, "step": 0}
            )
        except Exception as e:
            await websocket.send_json(
                {"type": "error", "message": f"ArguGod error: {e}"}
            )
        return None

    if command == "/auto":
        if not args.strip():
            await websocket.send_json(
                {"type": "error", "message": "Usage: /auto <research goal>"}
            )
            return None
        try:
            output = run_auto_research(
                args.strip(),
                orchestrator,
                provider=active_provider,
                model=active_model,
            )
            await websocket.send_json(
                {"type": "final", "content": output, "step": 0}
            )
        except Exception as e:
            await websocket.send_json(
                {"type": "error", "message": f"Auto-research error: {e}"}
            )
        return None

    await websocket.send_json(
        {
            "type": "error",
            "message": (
                f"Unknown slash command: {command}. "
                "Try /new, /argu explore <topic>, /auto <goal>"
            ),
        }
    )
    return None


async def handle_chat(
    websocket: WebSocket,
    user_input: str,
    conversation_id: Optional[str],
) -> Optional[str]:
    """
    Stream agent events to the browser.

    The agent loop is sync (blocking LLM/tool calls). Run it in a worker thread
    and push events through a queue so WebSocket frames flush between steps
    (thinking / tool_call / tool_result / stream_chunk) instead of only at the end.
    """
    conv_id = conversation_id
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _worker() -> None:
        try:
            for event in iter_agent_events(
                user_input,
                orchestrator,
                conversation_id=conversation_id,
                provider=active_provider,
                model=active_model,
                system_prompt=SYSTEM_PROMPT,
                step_delay=SERVER_STEP_DELAY,
            ):
                asyncio.run_coroutine_threadsafe(queue.put(event), loop).result()
        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                queue.put(
                    {
                        "type": "error",
                        "message": f"Agent worker failed: {e}",
                        "conversation_id": conversation_id,
                    }
                ),
                loop,
            ).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

    worker_future = loop.run_in_executor(None, _worker)

    while True:
        event = await queue.get()
        if event is None:
            break

        etype = event["type"]
        if "conversation_id" in event and event.get("conversation_id") is not None:
            conv_id = event["conversation_id"]

        if etype == "step_reply":
            # Internal / CLI; not shown in browser
            continue

        if etype == "status":
            await websocket.send_json(
                {
                    "type": "status",
                    "status": event.get("status", "thinking"),
                    "step": event.get("step", 0),
                }
            )
        elif etype == "tool_call":
            await websocket.send_json(
                {
                    "type": "tool_call",
                    "tool": event["tool"],
                    "input": event["input"],
                    "step": event["step"],
                }
            )
        elif etype == "tool_result":
            await websocket.send_json(
                {
                    "type": "tool_result",
                    "tool": event["tool"],
                    "input": event.get("input", ""),
                    "result": event["result"],
                    "step": event["step"],
                }
            )
        elif etype == "stream_chunk":
            await websocket.send_json(
                {
                    "type": "stream_chunk",
                    "content": event["content"],
                    "step": event["step"],
                }
            )
        elif etype == "final":
            await websocket.send_json(
                {
                    "type": "final",
                    "content": event.get("content") or "",
                    "step": event["step"],
                }
            )
            conv_id = event.get("conversation_id", conv_id)
            break
        elif etype == "error":
            await websocket.send_json(
                {
                    "type": "error",
                    "message": event["message"],
                }
            )
            conv_id = event.get("conversation_id", conv_id)
            break

    await worker_future
    return conv_id


if __name__ == "__main__":
    import uvicorn

    log_output(f"[Server] Starting on port {AGENT_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
