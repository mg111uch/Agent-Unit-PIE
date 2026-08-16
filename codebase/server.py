"""
server.py - FastAPI WebSocket server for browser-based agent control.

Thin transport layer — application logic now lives in agent_core/server/ package.
This stub starts the server via agent_core.server.app.
"""

from __future__ import annotations

import os
import sys

CODEBASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CODEBASE_DIR)
sys.path.insert(0, os.path.join(CODEBASE_DIR, "agent_core", "server"))

from encrypt_env import setup_or_unlock_env

setup_or_unlock_env(
    env_file=os.path.join(CODEBASE_DIR, ".env"),
    encrypted_file=os.path.join(CODEBASE_DIR, ".env.enc"),
)

from agent_core.server import app, AGENT_PORT
from agent_core.server import log_output

if __name__ == "__main__":
    import uvicorn

    log_output(f"[Server] Starting on port {AGENT_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
