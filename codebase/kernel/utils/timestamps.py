from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

# CURRENT UTC TIME

def utc_now() -> str:
    """
    Returns ISO UTC timestamp.
    """
    return datetime.now(
        timezone.utc
    ).isoformat()

# CURRENT LOCAL TIME

def local_now() -> str:
    """
    Returns local timezone timestamp.
    """
    return datetime.now().astimezone().isoformat()

# UNIX TIMESTAMP

def unix_timestamp() -> int:
    """
    Returns unix timestamp in seconds.
    """
    return int(datetime.now(
        timezone.utc
    ).timestamp())

# PARSE ISO TIMESTAMP

def parse_timestamp(
    timestamp: str
) -> datetime:
    """
    Parse ISO timestamp string.
    """

    return datetime.fromisoformat(
        timestamp.replace("Z", "+00:00")
    )

# FORMAT DATETIME

def format_timestamp(
    dt: datetime
) -> str:
    """
    Convert datetime to ISO string.
    """

    return dt.astimezone(
        timezone.utc
    ).isoformat()

# TIME DIFFERENCE

def seconds_between(
    start: str,
    end: str
) -> float:
    """
    Difference in seconds.
    """

    start_dt = parse_timestamp(start)
    end_dt = parse_timestamp(end)

    return (end_dt - start_dt).total_seconds()

def minutes_between(
    start: str,
    end: str
) -> float:

    return seconds_between(
        start,
        end
    ) / 60.0

def hours_between(
    start: str,
    end: str
) -> float:

    return seconds_between(
        start,
        end
    ) / 3600.0

def days_between(
    start: str,
    end: str
) -> float:

    return seconds_between(
        start,
        end
    ) / 86400.0

# TIME SHIFTING

def add_seconds(
    timestamp: str,
    seconds: int
) -> str:

    dt = parse_timestamp(timestamp)

    return format_timestamp(
        dt + timedelta(seconds=seconds)
    )

def add_minutes(
    timestamp: str,
    minutes: int
) -> str:

    return add_seconds(
        timestamp,
        minutes * 60
    )

def add_hours(
    timestamp: str,
    hours: int
) -> str:

    return add_seconds(
        timestamp,
        hours * 3600
    )

def add_days(
    timestamp: str,
    days: int
) -> str:

    dt = parse_timestamp(timestamp)

    return format_timestamp(
        dt + timedelta(days=days)
    )

# COMPARISON

def is_before(
    timestamp_a: str,
    timestamp_b: str
) -> bool:

    return parse_timestamp(
        timestamp_a
    ) < parse_timestamp(
        timestamp_b
    )

def is_after(
    timestamp_a: str,
    timestamp_b: str
) -> bool:

    return parse_timestamp(
        timestamp_a
    ) > parse_timestamp(
        timestamp_b
    )

# RANGE CHECK

def is_between(
    timestamp: str,
    start: str,
    end: str
) -> bool:

    dt = parse_timestamp(timestamp)

    start_dt = parse_timestamp(start)

    end_dt = parse_timestamp(end)

    return start_dt <= dt <= end_dt

# HUMAN READABLE

def human_readable_delta(
    past_timestamp: str
) -> str:
    """
    Example:
        5 minutes ago
        2 hours ago
    """

    now = datetime.now(timezone.utc)

    past = parse_timestamp(past_timestamp)

    delta = now - past

    seconds = int(delta.total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"

    minutes = seconds // 60

    if minutes < 60:
        return f"{minutes} minutes ago"

    hours = minutes // 60

    if hours < 24:
        return f"{hours} hours ago"

    days = hours // 24

    return f"{days} days ago"