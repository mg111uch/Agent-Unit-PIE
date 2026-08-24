"""MoE routing — split from moe.py."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RoutingResult:
    num_tokens: int
    top_k: int
    assignments: list[list[int]]
    tokens_per_expert: list[int]

    @property
    def total_assignments(self) -> int:
        return self.num_tokens * self.top_k

    @property
    def max_tokens_per_expert(self) -> int:
        return max(self.tokens_per_expert) if self.tokens_per_expert else 0

    @property
    def min_tokens_per_expert(self) -> int:
        return min(self.tokens_per_expert) if self.tokens_per_expert else 0

    @property
    def average_tokens_per_expert(self) -> float:
        return self.total_assignments / len(self.tokens_per_expert) if self.tokens_per_expert else 0.0

    @property
    def load_imbalance(self) -> float:
        avg = self.average_tokens_per_expert
        return self.max_tokens_per_expert / avg if avg else 0.0
