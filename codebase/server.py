"""
server.py - FastAPI WebSocket server for browser-based agent control.

Thin transport layer — application logic now lives in agent_core/server/ package.
This stub starts the server via agent_core.server.app.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.server import app, AGENT_PORT
from agent_core.server import log_output

if __name__ == "__main__":
    import uvicorn

    log_output(f"[Server] Starting on port {AGENT_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
