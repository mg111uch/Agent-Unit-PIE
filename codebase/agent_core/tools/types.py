"""Shared tool types — extracted from __init__.py to break circular imports."""

import json
from dataclasses import dataclass, asdict


def _parse_arg(input_data, default=None):
    if isinstance(input_data, str):
        try:
            return json.loads(input_data)
        except json.JSONDecodeError:
            return default
    return input_data if input_data is not None else default


class ToolError(Exception):
    def __init__(self, error_type: str, message: str, suggestion: str = ""):
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


@dataclass
class ToolResult:
    ok: bool
    data: str = ""
    error_type: str = ""
    message: str = ""
    suggestion: str = ""

    def to_string(self) -> str:
        if self.ok:
            return self.data
        parts = [f"Error: {self.message}"]
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return asdict(self)
