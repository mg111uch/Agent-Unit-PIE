from __future__ import annotations

import re
from agent_core.config import SECRETS_PATTERNS


_REDACTED = "[REDACTED]"


def redact(text: str, patterns: list[str] | None = None) -> str:
    if not text:
        return text
    patterns = patterns or SECRETS_PATTERNS
    result = text
    for pattern in patterns:
        try:
            result = re.sub(pattern, _REDACTED, result)
        except re.error:
            pass
    return result
