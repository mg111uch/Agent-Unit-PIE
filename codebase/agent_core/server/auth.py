"""JWT authentication helpers."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt as pyjwt

from agent_core.config import JWT_SECRET

SKIP_AUTH = os.getenv("AGENT_SKIP_AUTH", "").lower() in ("1", "true", "yes")

security = HTTPBearer(auto_error=False)


def verify_token(token: str) -> Optional[dict]:
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if SKIP_AUTH:
        return {"id": "local", "username": "local"}
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    user = verify_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
