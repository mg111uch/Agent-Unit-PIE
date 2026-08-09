"""
VSE - Virtual Silicon Engine
vse/moe.py

Mixture-of-Experts (MoE) architectural model.

MVP responsibilities:
    - Expert configuration
    - Top-K routing
    - Active vs total parameters
    - Expert load distribution
    - Expert compute cost
    - Expert weight storage
    - MoE layer workload estimation

This module does NOT perform real neural-network inference.

It models the hardware workload created by an MoE Transformer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .compute import ComputeArray
from .memory import Memory
from .ops import OpCost, combine_costs, linear_cost


# ---------------------------------------------------------------------------
# MoE configuration
# ---------------------------------------------------------------------------

@dataclass
class MoEConfig:
    """
    Configuration for one MoE layer.

    hidden_dim:
        Transformer hidden dimension.

    intermediate_dim:
        Expert MLP intermediate dimension.

    num_experts:
        Total number of experts.

    top_k:
        Number of experts activated for each token.

    weight_bits:
        Expert weight precision.

    activation_bits:
        Activation precision.

    gated:
        Whether each expert uses a gated MLP.
    """

    hidden_dim: int
    intermediate_dim: int

    num_experts: int
    top_k: int = 1

    weight_bits: int = 4
    activation_bits: int = 16

    gated: bool = True

    def __post_init__(self) -> None:
        if self.hidden_dim <= 0:
            raise ValueError("hidden_dim must be > 0")

        if self.intermediate_dim <= 0:
            raise ValueError(
                "intermediate_dim must be > 0"
            )

        if self.num_experts <= 0:
            raise ValueError(
                "num_experts must be > 0"
            )

        if self.top_k <= 0:
            raise ValueError("top_k must be > 0")

        if self.top_k > self.num_experts:
            raise ValueError(
                "top_k cannot exceed num_experts"
            )

        if self.weight_bits <= 0:
            raise ValueError(
                "weight_bits must be > 0"
            )

        if self.activation_bits <= 0:
            raise ValueError(
                "activation_bits must be > 0"
            )


# ---------------------------------------------------------------------------
# Expert configuration
# ---------------------------------------------------------------------------

@dataclass
class Expert:
    """Metadata describing one MoE expert."""

    expert_id: int
    hidden_dim: int
    intermediate_dim: int
    weight_bits: int
    gated: bool = True

    @property
    def projection_count(self) -> int:
        return 3 if self.gated else 2

    @property
    def parameter_count(self) -> int:
        """
        Parameters contained in this expert's MLP.
        """

        return (
            self.projection_count
            * self.hidden_dim
            * self.intermediate_dim
        )

    @property
    def weight_bytes(self) -> int:
        return (
            self.parameter_count
            * self.weight_bits
            + 7
        ) // 8


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

@dataclass
class RoutingResult:
    """
    Result of routing tokens to experts.
    """

    num_tokens: int
    top_k: int

    assignments: list[list[int]]
    tokens_per_expert: list[int]

    @property
    def total_assignments(self) -> int:
        return self.num_tokens * self.top_k

    @property
    def max_tokens_per_expert(self) -> int:
        if not self.tokens_per_expert:
            return 0

        return max(self.tokens_per_expert)

    @property
    def min_tokens_per_expert(self) -> int:
        if not self.tokens_per_expert:
            return 0

        return min(self.tokens_per_expert)

    @property
    def average_tokens_per_expert(self) -> float:
        if not self.tokens_per_expert:
            return 0.0

        return (
            self.total_assignments
            / len(self.tokens_per_expert)
        )

    @property
    def load_imbalance(self) -> float:
        """
        Ratio of busiest expert to average expert.

        1.0 = perfectly balanced.

        Larger values indicate routing imbalance.
        """

        average = self.average_tokens_per_expert

        if average == 0:
            return 0.0

        return (
            self.max_tokens_per_expert
            / average
        )


# ---------------------------------------------------------------------------
# MoE cost
# ---------------------------------------------------------------------------

@dataclass
class MoECost:
    """
    Aggregate hardware cost of an MoE layer.
    """

    name: str

    tokens: int
    num_experts: int
    top_k: int

    routing_cost: Optional[OpCost]
    expert_costs: list[OpCost]

    tokens_per_expert: list[int]

    total_parameter_count: int
    active_parameter_count: int

    total_weight_bytes: int
    active_weight_bytes: int

    @property
    def macs(self) -> int:
        total = 0

        if self.routing_cost is not None:
            total += self.routing_cost.macs

        total += sum(
            cost.macs
            for cost in self.expert_costs
        )

        return total

    @property
    def input_bytes(self) -> int:
        total = 0

        if self.routing_cost is not None:
            total += self.routing_cost.input_bytes

        total += sum(
            cost.input_bytes
            for cost in self.expert_costs
        )

        return total

    @property
    def output_bytes(self) -> int:
        total = 0

        if self.routing_cost is not None:
            total += self.routing_cost.output_bytes

        total += sum(
            cost.output_bytes
            for cost in self.expert_costs
        )

        return total

    @property
    def total_memory_bytes(self) -> int:
        return (
            self.input_bytes
            + self.output_bytes
        )

    @property
    def arithmetic_intensity(self) -> float:
        if self.total_memory_bytes == 0:
            return 0.0

        return self.macs / self.total_memory_bytes

    @property
    def load_imbalance(self) -> float:
        if not self.tokens_per_expert:
            return 0.0

        average = (
            sum(self.tokens_per_expert)
            / len(self.tokens_per_expert)
        )

        if average == 0:
            return 0.0

        return (
            max(self.tokens_per_expert)
            / average
        )

    def report(self) -> dict:
        return {
            "name": self.name,
            "tokens": self.tokens,
            "num_experts": self.num_experts,
            "top_k": self.top_k,
            "macs": self.macs,
            "input_bytes": self.input_bytes,
            "output_bytes": self.output_bytes,
            "total_memory_bytes": self.total_memory_bytes,
            "total_parameter_count": (
                self.total_parameter_count
            ),
            "active_parameter_count": (
                self.active_parameter_count
            ),
            "total_weight_bytes": (
                self.total_weight_bytes
            ),
            "active_weight_bytes": (
                self.active_weight_bytes
            ),
            "tokens_per_expert": (
                self.tokens_per_expert
            ),
            "load_imbalance": self.load_imbalance,
            "arithmetic_intensity": (
                self.arithmetic_intensity
            ),
        }


# ---------------------------------------------------------------------------
# MoE model
# ---------------------------------------------------------------------------

class MoE:
    """
    Mixture-of-Experts workload model.

    Example:

        moe = MoE(
            MoEConfig(
                hidden_dim=4096,
                intermediate_dim=14336,
                num_experts=128,
                top_k=2,
            ),
            compute=compute,
            memory=memory,
        )

        cost = moe.cost(tokens=32)

    The model assumes balanced routing by default.
    """

    def __init__(
        self,
        config: MoEConfig,
        compute: Optional[ComputeArray] = None,
        memory: Optional[Memory] = None,
        name: str = "moe",
    ):
        self.config = config
        self.compute = compute
        self.memory = memory
        self.name = name

        self.experts = [
            Expert(
                expert_id=i,
                hidden_dim=config.hidden_dim,
                intermediate_dim=config.intermediate_dim,
                weight_bits=config.weight_bits,
                gated=config.gated,
            )
            for i in range(config.num_experts)
        ]

    # ------------------------------------------------------------------
    # Parameter statistics
    # ------------------------------------------------------------------

    @property
    def expert_parameter_count(self) -> int:
        return self.experts[0].parameter_count

    @property
    def total_parameter_count(self) -> int:
        return sum(
            expert.parameter_count
            for expert in self.experts
        )

    @property
    def active_parameter_count(self) -> int:
        """
        Parameters mathematically associated with top-K experts.

        For a token, top-K experts are active.
        """

        return (
            self.expert_parameter_count
            * self.config.top_k
        )

    @property
    def total_weight_bytes(self) -> int:
        return sum(
            expert.weight_bytes
            for expert in self.experts
        )

    @property
    def active_weight_bytes(self) -> int:
        return (
            self.experts[0].weight_bytes
            * self.config.top_k
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def balanced_routing(
        self,
        tokens: int,
    ) -> RoutingResult:
        """
        Generate deterministic approximately-balanced routing.

        This is NOT a learned router.

        It exists so the architectural simulator can model expert
        utilization before a real router is introduced.
        """

        if tokens <= 0:
            raise ValueError("tokens must be > 0")

        assignments: list[list[int]] = [
            []
            for _ in range(tokens)
        ]

        tokens_per_expert = [
            0
            for _ in range(self.config.num_experts)
        ]

        # Round-robin top-K assignment.
        for token_id in range(tokens):

            for k in range(self.config.top_k):
                expert_id = (
                    token_id * self.config.top_k
                    + k
                ) % self.config.num_experts

                assignments[token_id].append(
                    expert_id
                )

                tokens_per_expert[expert_id] += 1

        return RoutingResult(
            num_tokens=tokens,
            top_k=self.config.top_k,
            assignments=assignments,
            tokens_per_expert=tokens_per_expert,
        )

    # ------------------------------------------------------------------
    # Expert workload
    # ------------------------------------------------------------------

    def expert_cost(
        self,
        tokens: int,
        expert_id: int,
    ) -> OpCost:
        """
        Calculate workload for one expert.
        """

        if tokens < 0:
            raise ValueError(
                "tokens must be >= 0"
            )

        if not (
            0 <= expert_id
            < self.config.num_experts
        ):
            raise ValueError(
                "invalid expert_id"
            )

        if tokens == 0:
            return OpCost(
                name=f"expert_{expert_id}",
                op_type=__import__(
                    "vse.ops",
                    fromlist=["OpType"],
                ).OpType.CUSTOM,
            )

        # Expert MLP consists of:
        #
        # hidden -> intermediate
        # hidden -> intermediate   (gate)
        # intermediate -> hidden

        projection_count = (
            3 if self.config.gated else 2
        )

        macs_per_token = (
            projection_count
            * self.config.hidden_dim
            * self.config.intermediate_dim
        )

        macs = tokens * macs_per_token

        # Activations.
        input_bytes = (
            tokens
            * self.config.hidden_dim
            * self.config.activation_bits
            + 7
        ) // 8

        output_bytes = input_bytes

        # Expert weights.
        # We account for weight traffic separately at MoE level,
        # because real hardware may keep experts resident in SRAM/HBM.
        return OpCost(
            name=f"expert_{expert_id}",
            op_type=__import__(
                "vse.ops",
                fromlist=["OpType"],
            ).OpType.CUSTOM,
            macs=macs,
            input_bytes=input_bytes,
            output_bytes=output_bytes,
            compute_cycles=(
                self.compute.cycles_for_macs(macs)
                if self.compute is not None
                else 0
            ),
            memory_read_cycles=(
                (
                    input_bytes
                    + self.memory.read_bandwidth_bytes_per_cycle
                    - 1
                )
                // self.memory.read_bandwidth_bytes_per_cycle
                if self.memory is not None
                else 0
            ),
            memory_write_cycles=(
                (
                    output_bytes
                    + self.memory.write_bandwidth_bytes_per_cycle
                    - 1
                )
                // self.memory.write_bandwidth_bytes_per_cycle
                if self.memory is not None
                else 0
            ),
        )

    # ------------------------------------------------------------------
    # Complete MoE workload
    # ------------------------------------------------------------------

    def cost(
        self,
        tokens: int,
        routing: Optional[RoutingResult] = None,
    ) -> MoECost:
        """
        Calculate complete MoE workload.

        If routing is omitted, balanced routing is used.
        """

        if tokens <= 0:
            raise ValueError("tokens must be > 0")

        if routing is None:
            routing = self.balanced_routing(tokens)

        if routing.num_tokens != tokens:
            raise ValueError(
                "routing token count does not match tokens"
            )

        # Simple router cost.
        #
        # This represents producing top-K expert scores.
        routing_macs = (
            tokens
            * self.config.hidden_dim
            * self.config.num_experts
        )

        routing_cost = OpCost(
            name="moe_router",
            op_type=__import__(
                "vse.ops",
                fromlist=["OpType"],
            ).OpType.CUSTOM,
            macs=routing_macs,
            input_bytes=(
                tokens
                * self.config.hidden_dim
                * self.config.activation_bits
                + 7
            ) // 8,
            output_bytes=(
                tokens
                * self.config.top_k
                * 4
            ),
            compute_cycles=(
                self.compute.cycles_for_macs(
                    routing_macs
                )
                if self.compute is not None
                else 0
            ),
        )

        expert_costs: list[OpCost] = []

        for expert_id, expert_tokens in enumerate(
            routing.tokens_per_expert
        ):
            if expert_tokens == 0:
                continue

            expert_costs.append(
                self.expert_cost(
                    tokens=expert_tokens,
                    expert_id=expert_id,
                )
            )

        return MoECost(
            name=self.name,
            tokens=tokens,
            num_experts=self.config.num_experts,
            top_k=self.config.top_k,
            routing_cost=routing_cost,
            expert_costs=expert_costs,
            tokens_per_expert=(
                routing.tokens_per_expert
            ),
            total_parameter_count=(
                self.total_parameter_count
            ),
            active_parameter_count=(
                self.active_parameter_count
            ),
            total_weight_bytes=(
                self.total_weight_bytes
            ),
            active_weight_bytes=(
                self.active_weight_bytes
            ),
        )

    # ------------------------------------------------------------------
    # Architecture report
    # ------------------------------------------------------------------

    def architecture_report(self) -> dict:
        """
        Return model-level MoE statistics.
        """

        return {
            "num_experts": self.config.num_experts,
            "top_k": self.config.top_k,
            "hidden_dim": self.config.hidden_dim,
            "intermediate_dim": (
                self.config.intermediate_dim
            ),
            "total_parameters": (
                self.total_parameter_count
            ),
            "active_parameters": (
                self.active_parameter_count
            ),
            "total_weight_bytes": (
                self.total_weight_bytes
            ),
            "active_weight_bytes": (
                self.active_weight_bytes
            ),
            "total_weight_gb": (
                self.total_weight_bytes
                / 1024**3
            ),
            "active_weight_gb": (
                self.active_weight_bytes
                / 1024**3
            ),
            "activation_ratio": (
                self.active_parameter_count
                / self.total_parameter_count
            ),
        }

    def __repr__(self) -> str:
        return (
            f"MoE("
            f"experts={self.config.num_experts}, "
            f"top_k={self.config.top_k}, "
            f"total="
            f"{self.total_parameter_count / 1e9:.2f}B, "
            f"active="
            f"{self.active_parameter_count / 1e9:.2f}B)"
        )

