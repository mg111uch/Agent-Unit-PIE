"""Declarative spec for composite tool chains.

A chain exposes ONE tool to the LLM; internally it runs a sequence of existing
registered tools locally and returns a single combined, budget-capped result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Step:
    """One step in a chain: call *tool* with *args*, keep result under *key*.

    args values bind:
      - `$input.<key>`      -> the chain tool's top-level param <key>
      - `$step.<key>.<path>`-> field <path> (dotted) of a prior step's stored result
      - `$step.<key>.$`     -> the prior step's whole stored result
      - anything else       -> literal (lists/dicts are resolved recursively)

    collect maps alias -> dotted field path of this step's result to keep in the
    final output (and in the store for later steps). When empty, the whole result
    is kept. A step marked optional is skipped (not failed) when its inputs are
    missing.
    """

    tool: str
    args: Dict[str, Any] = field(default_factory=dict)
    name: str = ""
    collect: Dict[str, str] = field(default_factory=dict)
    optional: bool = False

    @property
    def key(self) -> str:
        return self.name or self.tool


@dataclass
class ChainSpec:
    """A named, registered composite tool built from existing tools."""

    name: str
    category: str
    description: str
    steps: list
    params: Dict[str, Any] = field(default_factory=dict)
    budget_tokens: int = 16000
    step_cap_chars: int = 8000
