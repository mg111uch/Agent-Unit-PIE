"""
server.py - FastAPI WebSocket server for browser-based agent control.

Thin transport layer — application logic now lives in agent_core/server/ package.
This stub starts the server via agent_core.server.app.
"""

from __future__ import annotations

import base64
import getpass
import json
import os
import sys

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ENCRYPTED_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.enc")


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _try_unlock_env() -> None:
    if not os.path.exists(ENCRYPTED_ENV_FILE):
        return
    password = getpass.getpass("Enter password to unlock API keys: ")
    with open(ENCRYPTED_ENV_FILE, "rb") as f:
        salt = f.read(16)
        encrypted_data = f.read()
    key = _derive_key(password, salt)
    try:
        payload = json.loads(Fernet(key).decrypt(encrypted_data))
    except InvalidToken:
        print("Invalid password.")
        sys.exit(1)
    for k, v in payload.items():
        os.environ.setdefault(k, v)
    print("API keys unlocked.")


_try_unlock_env()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.server import app, AGENT_PORT
from agent_core.server import log_output

if __name__ == "__main__":
    import uvicorn

    log_output(f"[Server] Starting on port {AGENT_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
