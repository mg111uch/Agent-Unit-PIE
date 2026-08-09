"""Lightweight token counting (PlanPhases2 Phase 7).

Uses OpenAI's tiktoken encoder (cl100k_base) when available — the same
tokenizer as atlas_tools/token_count.py — and falls back to a chars/4
heuristic so the pipeline never hard-depends on tiktoken being installed.

Reuses the shared encoding cache (codebase/encoding_cache) via
TIKTOKEN_CACHE_DIR so the encoder files are downloaded only once.
"""

from __future__ import annotations

import os
import threading
from typing import Any, Optional

from agent_core.config import CODEBASE_ROOT

_ENCODING_CACHE_DIR = os.path.join(CODEBASE_ROOT, "encoding_cache")

# Point tiktoken at the shared cache BEFORE the encoder is first loaded.
# Guarded so a missing/unwritable cache dir never breaks the runtime — tiktoken
# will then fall back to its own cache and a network fetch.
try:
    os.makedirs(_ENCODING_CACHE_DIR, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = _ENCODING_CACHE_DIR
except OSError:
    pass

_encoding: object = None
_encoding_lock = threading.Lock()


def _get_encoding():
    global _encoding
    if _encoding is not None:
        return _encoding
    with _encoding_lock:
        if _encoding is None:
            try:
                import tiktoken  # type: ignore

                _encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                _encoding = False
    return _encoding


def _fallback(text: str) -> int:
    return max(1, len(text) // 4)


def count_tokens(text: Any) -> int:
    """Token estimate for a string, or the chars/4 fallback on any failure."""
    if text is None:
        return 0
    if not isinstance(text, str):
        text = str(text)
    if not text:
        return 0
    enc = _get_encoding()
    if not enc:
        return _fallback(text)
    try:
        return len(enc.encode(text, disallowed_special=()))  # type: ignore
    except Exception:
        return _fallback(text)