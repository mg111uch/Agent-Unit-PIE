"""Signal -> subscriber list (single purpose).

Owns the subscribe registry that kernel_bus.subscribe writes to.
No engine logic, no persistence, no imports from engines (no cycles).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Union

SignalLike = Union[str, Any]

_SUBSCRIBERS: Dict[str, List[Callable]] = {}


def register(signal_type: str, handler: Callable) -> None:
    _SUBSCRIBERS.setdefault(signal_type, [])
    if handler not in _SUBSCRIBERS[signal_type]:
        _SUBSCRIBERS[signal_type].append(handler)


def unregister(signal_type: str, handler: Callable) -> None:
    handlers = _SUBSCRIBERS.get(signal_type, [])
    if handler in handlers:
        handlers.remove(handler)


def subscribers_for(signal: SignalLike) -> List[Callable]:
    """Return handlers for a signal object (by .signal_type) or type name."""
    if isinstance(signal, str):
        kinds = [signal]
    else:
        kinds = [getattr(signal, "signal_type", ""), "*"]
    out = []
    for kind in kinds:
        out.extend(_SUBSCRIBERS.get(kind, []))
    return out


def route(signal: SignalLike) -> List[Callable]:
    """Single-purpose lookup: signal -> subscriber list (bus invokes)."""
    return subscribers_for(signal)


def stats() -> Dict[str, int]:
    return {k: len(v) for k, v in _SUBSCRIBERS.items()}
