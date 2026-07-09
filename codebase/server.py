"""
server.py - FastAPI WebSocket server for browser-based agent control.

All agent logic (tool execution, LLM calls) runs here.
Frontend connects via WebSocket for chat and REST for queries.
"""

import os, sys, json, asyncio, traceback
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

import jwt as pyjwt

sys.path.insert(0, os.path.dirname(__file__))
from agent_tools import (
    TOOLS, log_output, KERNEL_AVAILABLE, AUTO_RETRIEVE_CONTEXT,
    RETRIEVE_LIMIT, retrieval_engine, extract_json,
)
from llm.llm_orchestrator import LLMOrchestrator

JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))

active_provider = os.getenv("AGENT_PROVIDER", "gemini")
active_model: str = ""
registered_providers: list[dict] = []
provider_models: dict[str, str] = {}


def _resolve_initial_model() -> str:
    provider_defaults = {
        "gemini": "gemini-3.1-flash-lite",
        "openrouter": "openai/gpt-oss-20b:free",
        "mock": "mock",
    }
    env_model = os.getenv("AGENT_MODEL")
    if env_model:
        return env_model
    return provider_defaults.get(active_provider, "gemini-3.1-flash-lite")


active_model = _resolve_initial_model()

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


orchestrator = LLMOrchestrator(
    default_provider=active_provider,
    default_model=active_model,
)

gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    gemini_model = os.getenv("GEMINI_MODEL", os.getenv("AGENT_MODEL", "gemini-3.1-flash-lite"))
    from llm.providers.gemini_provider import GeminiProvider
    orchestrator.register_provider("gemini", GeminiProvider(
        api_key=gemini_key,
        model=gemini_model,
    ))
    registered_providers.append({"provider": "gemini", "model": gemini_model})
    provider_models["gemini"] = gemini_model

openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
    from llm.providers.openrouter_provider import OpenRouterProvider
    orchestrator.register_provider("openrouter", OpenRouterProvider(
        api_key=openrouter_key,
        model=openrouter_model,
    ))
    registered_providers.append({"provider": "openrouter", "model": openrouter_model})
    provider_models["openrouter"] = openrouter_model

from llm.providers.mock_provider import MockProvider
orchestrator.register_provider("mock", MockProvider(model="mock"))
registered_providers.append({"provider": "mock", "model": "mock"})
provider_models["mock"] = "mock"

SYSTEM_PROMPT = ""
try:
    system_path = os.path.join(os.path.dirname(__file__), "system_instruction.md")
    with open(system_path, "r") as f:
        SYSTEM_PROMPT = f.read()
except Exception:
    SYSTEM_PROMPT = "You are a helpful assistant."

workspace_root = os.path.abspath(os.path.dirname(__file__))

conversations: dict[str, str] = {}


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
    return {
        "active": {"provider": active_provider, "model": active_model},
        "providers": registered_providers,
    }


@app.post("/api/switch-provider")
async def switch_provider(data: dict):
    provider = data.get("provider")
    model = data.get("model")
    if not provider or not model:
        return {"error": "provider and model are required"}
    if provider not in orchestrator.providers:
        return {"error": f"Provider '{provider}' not registered"}
    global active_provider, active_model
    active_provider = provider
    active_model = model
    orchestrator.default_provider = provider
    orchestrator.default_model = model
    log_output(f"[Server] Switched to {provider}/{model}")
    return {"status": "ok", "provider": provider, "model": model}


@app.get("/api/files/tree")
async def get_file_tree():
    tree = _build_tree(workspace_root)
    return {"root": workspace_root, "tree": tree}


def _build_tree(dir_path: str, max_depth: int = 4, depth: int = 0):
    if depth > max_depth:
        return {"name": os.path.basename(dir_path), "type": "dir", "children": [], "truncated": True}
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
        return {"name": os.path.basename(dir_path), "type": "dir", "children": entries}
    except PermissionError:
        return {"name": os.path.basename(dir_path), "type": "dir", "children": [], "error": "permission denied"}


@app.get("/api/files/read")
async def read_file(path: str):
    full = os.path.abspath(os.path.join(workspace_root, path.lstrip("/")))
    if not full.startswith(workspace_root):
        return {"error": "Path escapes workspace"}
    try:
        with open(full, "r") as f:
            content = f.read()
        return {"path": path, "content": content}
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
    await websocket.send_json({
        "type": "connected",
        "user": {"id": user.get("id"), "username": user.get("username")},
    })
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
    except WebSocketDisconnect:
        log_output(f"[WS] User {user.get('username')} disconnected")
    finally:
        hb_task.cancel()


async def handle_chat(websocket: WebSocket, user_input: str, conversation_id: Optional[str]) -> Optional[str]:
    context_info = ""
    if AUTO_RETRIEVE_CONTEXT and KERNEL_AVAILABLE and retrieval_engine:
        try:
            results = retrieval_engine.search(query=user_input, limit=RETRIEVE_LIMIT)
            patterns = retrieval_engine.retrieve_patterns(limit=3)
            if results or patterns:
                context_parts = ["## Retrieved Context"]
                for r in results:
                    context_parts.append(f"- {r.content.get('content', {})}")
                for p in patterns:
                    context_parts.append(f"- Pattern: {p.content.get('title', 'unknown')}")
                context_info = "\n" + "\n".join(context_parts)
        except Exception as e:
            log_output(f"[Kernel] Context retrieval warning: {e}")

    current_input = user_input + context_info
    conv_id = conversation_id

    for step in range(10):
        try:
            result = orchestrator.generate(
                prompt=current_input,
                system_prompt=SYSTEM_PROMPT if conv_id is None else None,
                conversation_id=conv_id,
                provider=active_provider,
                model=active_model,
            )

            if result["status"] == "error":
                await websocket.send_json({
                    "type": "error",
                    "message": f"LLM call failed: {result.get('error')}",
                })
                return conv_id

            conv_id = result.get("conversation_id")
            reply = result["response"]

            clean_reply = reply.strip()
            if clean_reply.startswith("```"):
                clean_reply = "\n".join(clean_reply.split("\n")[1:])
                clean_reply = clean_reply.rsplit("```", 1)[0].strip()

            try:
                json_str = extract_json(clean_reply)
                if not json_str:
                    await websocket.send_json({"type": "final", "content": reply, "step": step})
                    return conv_id
                data = json.loads(json_str)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "final", "content": reply, "step": step})
                return conv_id

            if "final" in data:
                await websocket.send_json({"type": "final", "content": data["final"], "step": step})
                return conv_id

            tool = data.get("action")
            if not tool or tool not in TOOLS:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid or missing tool: {tool}",
                })
                return conv_id

            tool_input = data.get("input", "")

            await websocket.send_json({
                "type": "tool_call",
                "tool": tool,
                "input": tool_input,
                "step": step,
            })

            tool_result = TOOLS[tool](tool_input)

            await websocket.send_json({
                "type": "tool_result",
                "tool": tool,
                "result": str(tool_result)[:2000],
                "step": step,
            })

            current_input = (
                f"Tool used: {tool}\n"
                f"Input: {tool_input}\n"
                f"Result: {tool_result}\n"
                f"Decide next step."
            )

            await asyncio.sleep(2)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Exception in step {step}: {str(e)}\n{traceback.format_exc()}",
            })
            return conv_id

    await websocket.send_json({"type": "final", "content": "Max iterations reached", "step": 9})
    return conv_id


if __name__ == "__main__":
    import uvicorn
    log_output(f"[Server] Starting on port {AGENT_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
