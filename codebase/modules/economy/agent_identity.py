"""Agent identity + actor stamping (INT-02).

PIE must act as an *agent*, never as a shared human operator: a scoped key,
an explicit actor on every mutation, and no privilege to approve or move money.

    agent = load()                      # from data/agents/*.json + env key
    require(agent, "prospects:import")  # raises ScopeDenied
    actor_fields(agent)                 # {"actor_type": "agent", ...}

The key itself is never stored in the repo or in docs (OPS-03): the identity
file names the env var, the value comes from the environment.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_ACTOR_TYPE = "agent"
DEFAULT_SCOPES: Tuple[str, ...] = (
    "prospects:import", "proposals:draft", "jobs:import", "receipts:write",
)
FORBIDDEN_SCOPES: Tuple[str, ...] = (
    "outreach:approve", "outreach:send", "ledger:write", "payout:destination",
    "money:approve",
)


class ScopeDenied(PermissionError):
    """Raised when an actor attempts an action outside its scopes."""


@dataclass(frozen=True)
class Actor:
    actor_id: str
    actor_type: str = DEFAULT_ACTOR_TYPE
    scopes: Tuple[str, ...] = DEFAULT_SCOPES
    display: str = ""
    expires_at: str = ""
    extra: Dict[str, str] = field(default_factory=dict)

    def can(self, scope: str) -> bool:
        return scope in self.scopes

    def to_dict(self) -> Dict[str, str]:
        return {"actor_id": self.actor_id, "actor_type": self.actor_type}


def _identity_path(identity_path: Optional[str] = None) -> Path:
    if identity_path:
        return Path(identity_path)
    root = Path(os.environ.get("PIE_DATA_ROOT",
                              Path(__file__).resolve().parents[3] / "data"))
    return root / "agents" / "pie_revenue_agent.json"


def load(identity_path: Optional[str] = None) -> Actor:
    """Load the PIE agent identity. Missing file -> least-privilege default."""
    p = _identity_path(identity_path)
    if not p.exists():
        return Actor(actor_id="pie_revenue_agent", actor_type="agent",
                     scopes=DEFAULT_SCOPES,
                     display="PIE revenue agent (default identity)")
    data = json.loads(p.read_text() or "{}")
    scopes = tuple(data.get("scopes") or DEFAULT_SCOPES)
    bad = [s for s in scopes if s in FORBIDDEN_SCOPES]
    if bad:
        raise ScopeDenied(f"identity requests forbidden scopes: {bad}")
    return Actor(
        actor_id=str(data.get("actor_id", "pie_revenue_agent")),
        actor_type=str(data.get("actor_type", DEFAULT_ACTOR_TYPE)),
        scopes=scopes,
        display=str(data.get("display", "")),
        expires_at=str(data.get("expires_at", "")),
        extra={k: str(v) for k, v in (data.get("extra") or {}).items()},
    )


def require(actor: Actor, scope: str) -> None:
    if not actor.can(scope):
        raise ScopeDenied(
            f"{actor.actor_id} lacks scope {scope}; has {sorted(actor.scopes)}")


def actor_fields(actor: Optional[Actor]) -> Dict[str, str]:
    """The two columns every mutating table carries."""
    if actor is None:
        return {"actor_type": "system", "actor_id": "unattributed"}
    return {"actor_type": actor.actor_type, "actor_id": actor.actor_id}


def api_key() -> str:
    """The scoped key value — env only, never a file in the repo."""
    return os.environ.get("PIE_AGENT_KEY", "")


def headers() -> Dict[str, str]:
    key = api_key()
    return {"X-Agent-Api-Key": key} if key else {}
