"""
VSE - Virtual Silicon Engine
vse/workload.py

End-to-end simulation: model → costs → task graph → cycle schedule →
benchmark report, on a configurable virtual chip.

Example:
    config = TransformerConfig(
        hidden_dim=4096,
        num_heads=32,
        intermediate_dim=11008,
    )

    model = TransformerModel(config, num_layers=32)

    result = simulate_transformer(
        model,
        sequence_length=4096,
    )

    print(result.report())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.benchmark.benchmark import Benchmark
from vse.core.compute import ComputeArray, ComputeConfig
from vse.core.core import Simulator
from vse.silicon.area import estimate_area
from vse.graphs.graph import (
    build_moe_tasks,
    build_transformer_tasks,
)
from vse.core.memory import Memory, MemoryConfig
from vse.core.memory_hierarchy import MemoryHierarchy
from vse.models.moe import MoE
from vse.core.noc import NoC, NoCConfig
from vse.silicon.power import estimate_power
from vse.report.result import EndToEndResult
from vse.scheduler import (
    Resource,
    ResourceType,
    ScheduleResult,
    Scheduler,
)
from vse.models.transformer import (
    TransformerModel,
)


# ---------------------------------------------------------------------------
# Hardware configuration
# ---------------------------------------------------------------------------

@dataclass
class HardwareConfig:
    """
    Virtual hardware definition for an end-to-end run.

    num_pes: processing elements in the compute array.
    macs_per_pe_per_cycle: MACs per PE per cycle.
    memory_bytes_per_cycle: aggregate read/write bandwidth.
    frequency_hz: clock frequency.
    sram_bytes: on-chip SRAM capacity.
    banks: independent banks per memory level.
    hbm/sram/dma_bytes_per_cycle: per-level bandwidth (None inherits
        memory_bytes_per_cycle).
    weight_chunks: double-buffer depth for weight streaming.
    noc_topology/noc_nodes/noc_link_bw/noc_per_hop_cycles/noc_links:
        interconnect; noc_nodes == 1 disables cross-node traffic.
    """

    num_pes: int = 4096
    macs_per_pe_per_cycle: int = 1
    memory_bytes_per_cycle: int = 256
    frequency_hz: float = 1e9
    sram_bytes: int = 0
    pipeline_latency: int = 0
    banks: int = 1
    hbm_bytes_per_cycle: Optional[int] = None
    sram_bytes_per_cycle: Optional[int] = None
    dma_bytes_per_cycle: Optional[int] = None
    weight_chunks: int = 4
    noc_topology: str = "ring"
    noc_nodes: int = 1
    noc_link_bw: int = 256
    noc_per_hop_cycles: int = 4
    noc_links: int = 1
    noc_broadcast: bool = False

    def __post_init__(self) -> None:
        if self.num_pes <= 0:
            raise ValueError("num_pes must be > 0")

        if self.macs_per_pe_per_cycle <= 0:
            raise ValueError(
                "macs_per_pe_per_cycle must be > 0"
            )

        if self.memory_bytes_per_cycle <= 0:
            raise ValueError(
                "memory_bytes_per_cycle must be > 0"
            )

        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")

        if self.sram_bytes < 0:
            raise ValueError("sram_bytes must be >= 0")

        if self.pipeline_latency < 0:
            raise ValueError(
                "pipeline_latency must be >= 0"
            )

        if self.banks <= 0:
            raise ValueError("banks must be > 0")

        if self.hbm_bytes_per_cycle is not None:
            if self.hbm_bytes_per_cycle <= 0:
                raise ValueError(
                    "hbm_bytes_per_cycle must be > 0"
                )

        if self.sram_bytes_per_cycle is not None:
            if self.sram_bytes_per_cycle <= 0:
                raise ValueError(
                    "sram_bytes_per_cycle must be > 0"
                )

        if self.dma_bytes_per_cycle is not None:
            if self.dma_bytes_per_cycle <= 0:
                raise ValueError(
                    "dma_bytes_per_cycle must be > 0"
                )

        if self.weight_chunks <= 0:
            raise ValueError(
                "weight_chunks must be > 0"
            )

        if self.noc_nodes < 1:
            raise ValueError("noc_nodes must be >= 1")

        if self.noc_link_bw <= 0:
            raise ValueError("noc_link_bw must be > 0")

        if self.noc_per_hop_cycles < 0:
            raise ValueError(
                "noc_per_hop_cycles must be >= 0"
            )

        if self.noc_links <= 0:
            raise ValueError("noc_links must be > 0")

# ---------------------------------------------------------------------------
# Memory hierarchy construction
# ---------------------------------------------------------------------------

def build_memory_hierarchy(
    config: HardwareConfig,
) -> MemoryHierarchy:
    return MemoryHierarchy.default(
        sram_bytes=config.sram_bytes,
        memory_bytes_per_cycle=config.memory_bytes_per_cycle,
        sram_bw_bytes_per_cycle=(
            config.sram_bytes_per_cycle or 0
        ),
        hbm_bw_bytes_per_cycle=(
            config.hbm_bytes_per_cycle or 0
        ),
        banks=config.banks,
    )


# ---------------------------------------------------------------------------
# Virtual machine
# ---------------------------------------------------------------------------

class VirtualMachine:
    """
    The virtual chip used by end-to-end simulations.

    Owns the compute array, memory subsystem, and the scheduler that
    executes workload task graphs on them.
    """

    def __init__(
        self,
        config: HardwareConfig,
    ):
        self.config = config

        self.simulator = Simulator(
            frequency_hz=config.frequency_hz
        )

        self.compute = ComputeArray(
            self.simulator,
            "compute",
            ComputeConfig(
                num_pes=config.num_pes,
                macs_per_pe_per_cycle=(
                    config.macs_per_pe_per_cycle
                ),
                frequency_hz=config.frequency_hz,
            ),
        )

        self.memory = Memory(
            self.simulator,
            "sram",
            MemoryConfig(
                capacity_bytes=max(
                    config.sram_bytes,
                    1,
                ),
                read_bandwidth_bytes_per_cycle=(
                    config.memory_bytes_per_cycle
                ),
                write_bandwidth_bytes_per_cycle=(
                    config.memory_bytes_per_cycle
                ),
                read_latency_cycles=1,
                write_latency_cycles=1,
            ),
        )

        self.scheduler = Scheduler(
            frequency_hz=config.frequency_hz
        )

        self.scheduler.add_resource(
            Resource(
                name="compute",
                resource_type=ResourceType.COMPUTE,
                capacity=config.num_pes,
                throughput=config.macs_per_pe_per_cycle,
                pipeline_latency=config.pipeline_latency,
            )
        )

        self.memory_hierarchy = (
            build_memory_hierarchy(config)
        )

        self.memory_hierarchy.add_resources(
            self.scheduler
        )

        self.scheduler.add_resource(
            Resource(
                name="dma",
                resource_type=ResourceType.DMA,
                capacity=1,
                throughput=(
                    config.dma_bytes_per_cycle
                    or config.memory_bytes_per_cycle
                ),
            )
        )

        self.scheduler.add_resource(
            Resource(
                name="router",
                resource_type=ResourceType.ROUTER,
                capacity=1,
                throughput=config.memory_bytes_per_cycle,
            )
        )

        self.noc = NoC(
            NoCConfig(
                topology=config.noc_topology,
                nodes=config.noc_nodes,
                link_bw=config.noc_link_bw,
                per_hop_cycles=config.noc_per_hop_cycles,
                links=config.noc_links,
                broadcast=config.noc_broadcast,
            )
        )

        self.noc.add_resources(
            self.scheduler
        )

    def run(self) -> ScheduleResult:
        return self.scheduler.schedule()


# ---------------------------------------------------------------------------
# End-to-end simulation entry points
# ---------------------------------------------------------------------------

def _attach_physical_estimates(
    result: EndToEndResult,
    chip,
) -> None:
    """
    Populate the Phase-7 power and area estimates on a result.
    """

    result.power = estimate_power(
        result,
        chip=chip,
    ).report()
    result.area = estimate_area(chip).report()


def simulate_transformer(
    model: TransformerModel,
    sequence_length: int,
    config: Optional[HardwareConfig] = None,
    mode: str = "decode",
    target_tokens_per_second: Optional[float] = None,
) -> EndToEndResult:
    """
    Run an end-to-end Transformer simulation.

    mode:
        "decode" — generate one new token.
        "prefill" — process an entire prompt.
    """

    if mode == "decode":
        workload = model.decode_cost(sequence_length)
        tokens = 1
    elif mode == "prefill":
        workload = model.prefill_cost(sequence_length)
        tokens = sequence_length
    else:
        raise ValueError(
            "mode must be 'decode' or 'prefill'"
        )

    if config is None:
        config = HardwareConfig()

    machine = VirtualMachine(config)

    kv_bytes = (
        workload.layer_cost.kv_read_bytes
        + workload.layer_cost.kv_write_bytes
    ) * model.num_layers

    kv_level = machine.memory_hierarchy.on_chip_level(
        kv_bytes
    )

    machine.scheduler.add_tasks(
        build_transformer_tasks(
            workload.layer_cost,
            model.num_layers,
            kv_level=kv_level,
        )
    )

    schedule = machine.run()

    benchmark = Benchmark(
        compute=machine.compute,
        memory=machine.memory,
        frequency_hz=config.frequency_hz,
    )

    if mode == "decode":
        benchmark_result = benchmark.transformer_decode(
            model,
            sequence_length=sequence_length,
            target_tokens_per_second=(
                target_tokens_per_second
            ),
        )
    else:
        benchmark_result = benchmark.transformer_prefill(
            model,
            sequence_length=sequence_length,
        )

    result = EndToEndResult(
        name="transformer",
        tokens=tokens,
        sequence_length=sequence_length,
        schedule=schedule,
        benchmark=benchmark_result,
        total_macs=workload.macs,
        total_memory_bytes=workload.memory_bytes,
        memory_traffic=machine.memory_hierarchy.report(
            schedule,
            weight_bytes=0,
        ),
    )

    _attach_physical_estimates(result, config)

    return result


def simulate_moe(
    moe: MoE,
    tokens: int,
    config: Optional[HardwareConfig] = None,
    target_tokens_per_second: Optional[float] = None,
) -> EndToEndResult:
    """
    Run an end-to-end MoE layer simulation.
    """

    if config is None:
        config = HardwareConfig()

    cost = moe.cost(tokens=tokens)

    machine = VirtualMachine(config)

    active_experts = len(cost.expert_costs)

    weight_bytes_per_expert = (
        cost.total_weight_bytes // cost.num_experts
        if cost.num_experts
        else 0
    )

    weight_traffic = (
        weight_bytes_per_expert
        * active_experts
    )

    resident = (
        machine.memory_hierarchy.weights_resident(
            weight_traffic
        )
    )

    machine.scheduler.add_tasks(
        build_moe_tasks(
            cost.routing_cost,
            cost.expert_costs,
            expert_units=(
                max(
                    1,
                    config.num_pes // active_experts,
                )
                if active_experts
                else None
            ),
            weight_bytes_per_expert=(
                weight_bytes_per_expert
            ),
            resident=resident,
            chunks=config.weight_chunks,
            noc=(
                machine.noc
                if machine.noc.config.enabled
                else None
            ),
        )
    )

    schedule = machine.run()

    benchmark = Benchmark(
        compute=machine.compute,
        memory=machine.memory,
        frequency_hz=config.frequency_hz,
    )

    benchmark_result = benchmark.moe(
        moe,
        tokens=tokens,
        target_tokens_per_second=(
            target_tokens_per_second
        ),
    )

    result = EndToEndResult(
        name="moe",
        tokens=tokens,
        sequence_length=0,
        schedule=schedule,
        benchmark=benchmark_result,
        total_macs=cost.macs,
        total_memory_bytes=cost.total_memory_bytes,
        memory_traffic=machine.memory_hierarchy.report(
            schedule,
            weight_bytes=weight_traffic,
        ),
        noc=machine.noc.report(schedule),
    )

    _attach_physical_estimates(result, config)

    return result
