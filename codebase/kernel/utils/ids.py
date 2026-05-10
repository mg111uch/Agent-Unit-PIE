from __future__ import annotations

import uuid
import hashlib
from typing import Optional


# =========================================================
# GENERIC RANDOM ID
# =========================================================

def generate_id(
    prefix: str = "id",
    length: int = 12
) -> str:
    """
    Generate short random ID.

    Example:
        unit_a1b2c3d4e5f6
    """

    uid = uuid.uuid4().hex[:length]

    return f"{prefix}_{uid}"


# =========================================================
# DETERMINISTIC HASH ID
# =========================================================

def generate_hash_id(
    content: str,
    prefix: str = "hash",
    length: int = 16
) -> str:
    """
    Generate deterministic ID from content.

    Same input -> same ID.
    """

    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    return f"{prefix}_{digest[:length]}"


# =========================================================
# TIMESTAMPED ID
# =========================================================

def generate_time_id(
    timestamp: str,
    prefix: str = "time",
    length: int = 10
) -> str:
    """
    Generate ID using timestamp hash.
    """

    digest = hashlib.md5(
        timestamp.encode("utf-8")
    ).hexdigest()

    return f"{prefix}_{digest[:length]}"


# =========================================================
# ENTITY IDS
# =========================================================

def generate_unit_id(
    unit_type: str,
    length: int = 12
) -> str:

    return generate_id(
        prefix=unit_type,
        length=length
    )


def generate_signal_id(
    signal_type: str,
    length: int = 12
) -> str:

    return generate_id(
        prefix=signal_type,
        length=length
    )


def generate_event_id(
    event_type: str,
    length: int = 12
) -> str:

    return generate_id(
        prefix=event_type,
        length=length
    )


def generate_pattern_id(
    pattern_type: str,
    length: int = 12
) -> str:

    return generate_id(
        prefix=pattern_type,
        length=length
    )


def generate_relation_id(
    relation_type: str,
    length: int = 12
) -> str:

    return generate_id(
        prefix=relation_type,
        length=length
    )


def generate_hypothesis_id(
    hypothesis_type: str = "hypothesis",
    length: int = 12
) -> str:

    return generate_id(
        prefix=hypothesis_type,
        length=length
    )


# =========================================================
# SESSION IDS
# =========================================================

def generate_session_id(
    agent_name: Optional[str] = None
) -> str:

    prefix = "session"

    if agent_name:
        prefix = f"{agent_name}_session"

    return generate_id(prefix=prefix)


# =========================================================
# VALIDATION
# =========================================================

def is_valid_id(value: str) -> bool:
    """
    Minimal validation check.
    """

    if not isinstance(value, str):
        return False

    if "_" not in value:
        return False

    prefix, suffix = value.split("_", 1)

    if not prefix or not suffix:
        return False

    return True


# =========================================================
# PARSING
# =========================================================

def extract_prefix(entity_id: str) -> Optional[str]:

    if not is_valid_id(entity_id):
        return None

    return entity_id.split("_", 1)[0]


def extract_suffix(entity_id: str) -> Optional[str]:

    if not is_valid_id(entity_id):
        return None

    return entity_id.split("_", 1)[1]