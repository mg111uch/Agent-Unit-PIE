"""WebSocket handler — agent lifecycle over WebSocket transport."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, Query

from agent_core.server.auth import verify_token
from agent_core.server.audit import make_audit_wrapper
from agent_core.server import app
import agent_core.server as _srv


@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket, token: str = Query(...)):
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    await websocket.accept()
    user_key = str(user.get("id"))
    user_ws_root = _srv.set_user_workspace(user_key)
    await websocket.send_json(
        {
            "type": "connected",
            "user": {"id": user.get("id"), "username": user.get("username")},
            "workspace": user_ws_root,
        }
    )
    conv_id = _srv.conversations.get(user_key)
    cancel_event = threading.Event()

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

            if msg_type == "cancel":
                cancel_event.set()
                await websocket.send_json({
                    "type": "final",
                    "content": "",
                    "step": 0,
                    "full_content": "(cancelled)",
                })
            elif msg_type == "chat":
                if not _srv.rate_limiter.check_llm(user_key, _srv.RATE_LIMIT_LLM_CALLS):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Rate limited: too many LLM requests. Please wait.",
                    })
                    continue
                cancel_event.clear()
                content = data.get("content", "")
                conv_id = await handle_chat(websocket, content, conv_id, user_key=user_key, cancel_event=cancel_event)
                _srv.conversations[user_key] = conv_id
            elif msg_type == "reset":
                cancel_event.set()
                conv_id = None
                _srv.conversations[user_key] = None
                await websocket.send_json({"type": "reset", "status": "ok"})
            elif msg_type == "slash":
                if not _srv.rate_limiter.check_llm(user_key, _srv.RATE_LIMIT_LLM_CALLS):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Rate limited: too many requests. Please wait.",
                    })
                    continue
                cancel_event.clear()
                command = data.get("command", "")
                args = data.get("args", "")
                conv_id = await handle_slash(websocket, command, args)
                _srv.conversations[user_key] = conv_id
    except WebSocketDisconnect:
        _srv.log_output(f"[WS] User {user.get('username')} disconnected")
    finally:
        cancel_event.set()
        hb_task.cancel()
        _srv.clear_user_context()


async def handle_slash(
    websocket: WebSocket,
    command: str,
    args: str,
) -> Optional[str]:
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
            output = _srv.run_auto_research(
                args.strip(),
                _srv.orchestrator,
                provider=_srv.active_provider,
                model=_srv.active_model,
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
    user_key: str = "",
    cancel_event: Optional[threading.Event] = None,
) -> Optional[str]:
    conv_id = conversation_id
    session_id = conversation_id or f"session_{user_input[:32]}_{int(time.time())}"
    loop = asyncio.get_running_loop()

    _srv.msg_store.add_message(
        session_id=session_id,
        role="user",
        content=user_input,
    )

    queue: asyncio.Queue = asyncio.Queue()
    _AUDIT_TOOLS = make_audit_wrapper(
        _srv.ACTIVE_TOOLS_DICT, _srv.rate_limiter, _srv.audit_log, _srv.redact, user_key
    )

    def _worker() -> None:
        try:
            for event in _srv.iter_agent_events(
                user_input,
                _srv.orchestrator,
                conversation_id=conv_id,
                provider=_srv.active_provider,
                model=_srv.active_model,
                system_prompt=_srv.SYSTEM_PROMPT,
                step_delay=_srv.SERVER_STEP_DELAY,
                msg_store=_srv.msg_store,
                session_id=session_id,
                cancel_event=cancel_event,
                tools_override=_AUDIT_TOOLS,
            ):
                asyncio.run_coroutine_threadsafe(queue.put(event), loop).result()
        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                queue.put(
                    {
                        "type": "error",
                        "message": f"Agent worker failed: {e}",
                        "conversation_id": conv_id,
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
            continue

        if etype == "llm_call":
            await websocket.send_json({
                "type": "llm_call",
                "status": event.get("status", ""),
                "step": event.get("step", 0),
            })
            continue

        if etype == "question":
            await websocket.send_json({
                "type": "question",
                "questions": event.get("questions", []),
                "session_id": event.get("session_id", ""),
                "step": event.get("step", 0),
            })
            from agent_core.tools.question_ops import resolve_all_questions, cancel_questions
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "question_answer":
                    resolve_all_questions(
                        event.get("session_id", ""),
                        data.get("answers", []),
                    )
                    break
                elif data.get("type") == "cancel":
                    cancel_questions(event.get("session_id", ""))
                    break
            continue

        if etype == "status":
            await websocket.send_json({
                "type": "status",
                "status": event.get("status", "thinking"),
                "step": event.get("step", 0),
            })
        elif etype == "tool_call":
            await websocket.send_json({
                "type": "tool_call",
                "tool": event["tool"],
                "input": event["input"],
                "step": event["step"],
            })
        elif etype == "tool_result":
            await websocket.send_json({
                "type": "tool_result",
                "tool": event["tool"],
                "input": event.get("input", ""),
                "result": event["result"],
                "step": event["step"],
            })
        elif etype == "stream_chunk":
            await websocket.send_json({
                "type": "stream_chunk",
                "content": event["content"],
                "step": event["step"],
            })
        elif etype == "final":
            full = event.get("full_content") or event.get("content") or ""
            await websocket.send_json({
                "type": "final",
                "content": "",
                "full_content": full,
                "step": event["step"],
            })
            conv_id = event.get("conversation_id", conv_id)
            break
        elif etype == "error":
            await websocket.send_json({
                "type": "error",
                "message": event["message"],
            })
            conv_id = event.get("conversation_id", conv_id)
            break

    await worker_future

    if _srv.msg_store.count_messages(session_id) > 100:
        _srv.msg_store.delete_old_messages(session_id, keep_last=50)
        _srv.log_output(f"[Compaction] Trimmed session {session_id} to last 50 messages")

    return conv_id
