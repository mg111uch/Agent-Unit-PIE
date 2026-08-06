"""Gemini explicit context caching for the stateless generateContent path.

Caches the static prefix (system_instruction + tool schemas) once per
(model, system, tools) key and references it on subsequent calls so the
re-sent fixed overhead is billed at the discounted cached-input rate.

Two cache shapes:
  * full     — system + tools (turns where the model may call tools)
  * sys_only — system only (chained turns where schemas are intentionally
               skipped so the model answers from the data it already has)

Cache creation failure degrades gracefully to inline payloads (no cache).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional, Tuple


class GeminiContextCache:
    def __init__(self, client: Any, model: str, ttl: str = "600s"):
        self._client = client
        self._model = model
        self._ttl = ttl
        self._full: Optional[Tuple[str, Optional[str]]] = None
        self._sys_only: Optional[Tuple[str, Optional[str]]] = None

    @staticmethod
    def _key(model: str, system: str, tools: Any) -> str:
        raw = json.dumps(tools, sort_keys=True, default=str) if tools else ""
        return hashlib.sha256(f"{model}|{system}|{raw}".encode("utf-8")).hexdigest()

    def _create(self, system: str, tools: Any, sys_only: bool) -> str:
        config: dict[str, Any] = {"display_name": "pie-agent-cache", "ttl": self._ttl}
        if system:
            config["system_instruction"] = system
        if tools and not sys_only:
            config["tools"] = tools
        cache = self._client.caches.create(model=self._model, config=config)
        name = getattr(cache, "name", "") or ""
        if not name:
            raise RuntimeError("cache create returned no name")
        return name

    def ensure(self, system: str, tools: Any, sys_only: bool) -> Optional[str]:
        """Return a cache name for the key, or None when unavailable.

        A previously failed create for the same key is remembered (slot name is
        None) so we don't hammer caches.create on every call.
        """
        key = self._key(self._model, system, tools if not sys_only else None)
        slot = self._sys_only if sys_only else self._full
        if slot and slot[0] == key:
            return slot[1]
        try:
            name = self._create(system, tools, sys_only)
        except Exception:
            name = None
        if sys_only:
            self._sys_only = (key, name)
        else:
            self._full = (key, name)
        return name

    def existing(self, system: str, tools: Any, sys_only: bool = False) -> Optional[str]:
        """Return a previously created cache name for the key, without creating."""
        key = self._key(self._model, system, tools if not sys_only else None)
        slot = self._sys_only if sys_only else self._full
        if slot and slot[0] == key:
            return slot[1]
        return None

    def invalidate(self) -> None:
        self._full = None
        self._sys_only = None
