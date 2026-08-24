"""VSE workload: model → costs → graph → schedule → benchmark."""

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


@dataclass
class HardwareConfig:
    """Virtual hardware definition for an end-to-end run."""

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
    sram_model: str = "analytical"
    sram_ports: int = 1
    sram_bits_per_access: int = 32
    tech: Optional[object] = None
    num_tiles: int = 1
    sram_per_tile_bytes: Optional[int] = None
    pes_per_tile: Optional[int] = None
    tile_sram_banks: Optional[int] = None
    tile_sram_ports: Optional[int] = None
    tile_sram_bits: Optional[int] = None
    arch_family: str = "scalar"
    vector_width: int = 1
    systolic_dim: int = 0
    simd_lanes: int = 1
    dataflow: str = "weight_stationary"

    def __post_init__(self) -> None:
        def _pos(v, msg):  # local helper
            if v <= 0: raise ValueError(msg)
        _pos(self.num_pes, "num_pes must be > 0"); _pos(self.macs_per_pe_per_cycle, "macs_per_pe_per_cycle must be > 0"); _pos(self.memory_bytes_per_cycle, "memory_bytes_per_cycle must be > 0")
        if self.frequency_hz <= 0: raise ValueError("frequency_hz must be > 0")
        if self.sram_bytes < 0: raise ValueError("sram_bytes must be >= 0")
        if self.pipeline_latency < 0: raise ValueError("pipeline_latency must be >= 0")
        _pos(self.banks, "banks must be > 0")
        if self.hbm_bytes_per_cycle is not None and self.hbm_bytes_per_cycle <= 0: raise ValueError("hbm_bytes_per_cycle must be > 0")
        if self.sram_bytes_per_cycle is not None and self.sram_bytes_per_cycle <= 0: raise ValueError("sram_bytes_per_cycle must be > 0")
        if self.dma_bytes_per_cycle is not None and self.dma_bytes_per_cycle <= 0: raise ValueError("dma_bytes_per_cycle must be > 0")
        _pos(self.weight_chunks, "weight_chunks must be > 0")
        if self.noc_nodes < 1: raise ValueError("noc_nodes must be >= 1")
        _pos(self.noc_link_bw, "noc_link_bw must be > 0")
        if self.noc_per_hop_cycles < 0: raise ValueError("noc_per_hop_cycles must be >= 0")
        _pos(self.noc_links, "noc_links must be > 0")
        if self.sram_model not in ("analytical","physical"): raise ValueError("sram_model must be 'analytical' or 'physical'")
        if not 1 <= self.sram_ports <= 4: raise ValueError("sram_ports must be 1..4")
        if not 8 <= self.sram_bits_per_access <= 512: raise ValueError("sram_bits_per_access must be 8..512")
        if not 1 <= self.num_tiles <= 64: raise ValueError("num_tiles must be 1..64")
        if self.sram_per_tile_bytes is not None and self.sram_per_tile_bytes < 0: raise ValueError("sram_per_tile_bytes must be >= 0")
        if self.pes_per_tile is not None and self.pes_per_tile <= 0: raise ValueError("pes_per_tile must be > 0")
        if self.tile_sram_banks is not None and not 1 <= self.tile_sram_banks <= 512: raise ValueError("tile_sram_banks must be 1..512")
        if self.tile_sram_ports is not None and not 1 <= self.tile_sram_ports <= 4: raise ValueError("tile_sram_ports must be 1..4")
        if self.tile_sram_bits is not None and not 8 <= self.tile_sram_bits <= 512: raise ValueError("tile_sram_bits must be 8..512")
        _fam = self.arch_family.value if hasattr(self.arch_family, "value") else self.arch_family
        _allowed = {"scalar","simd","vector","systolic","weight_stationary","output_stationary","cim","near_memory"}
        if _fam not in _allowed: raise ValueError(f"arch_family must be one of {sorted(_allowed)}, got {_fam!r}")
        self.arch_family = str(_fam)
        if not 1 <= self.vector_width <= 16: raise ValueError("vector_width must be 1..16")
        if not 0 <= self.systolic_dim <= 64: raise ValueError("systolic_dim must be 0..64")
        if not 1 <= self.simd_lanes <= 8: raise ValueError("simd_lanes must be 1..8")
        if self.dataflow not in ("weight_stationary","output_stationary"): raise ValueError(f"dataflow must be weight/output_stationary, got {self.dataflow!r}")

# ---------------------------------------------------------------------------
# Memory hierarchy construction
# ---------------------------------------------------------------------------

def build_memory_hierarchy(config: HardwareConfig) -> MemoryHierarchy:
    if getattr(config, "num_tiles", 1) > 1:
        try:
            from vse.core.tile import TiledHierarchy  # lazy
            th = TiledHierarchy.build_tiled_hierarchy(config)
            return th.to_hierarchy() if hasattr(th, "to_hierarchy") else MemoryHierarchy(th.to_memory_levels())  # type: ignore
        except Exception:
            pass
    return MemoryHierarchy.default(
        sram_bytes=config.sram_bytes,
        memory_bytes_per_cycle=config.memory_bytes_per_cycle,
        sram_bw_bytes_per_cycle=(config.sram_bytes_per_cycle or 0),
        hbm_bw_bytes_per_cycle=(config.hbm_bytes_per_cycle or 0),
        banks=config.banks,
        sram_model=config.sram_model,
        sram_ports=config.sram_ports,
        sram_bits_per_access=config.sram_bits_per_access,
        frequency_hz=config.frequency_hz,
        tech=getattr(config, "tech", None),
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
                family=getattr(config, "arch_family", "scalar"),
                vector_width=getattr(config, "vector_width", 1),
                systolic_dim=getattr(config, "systolic_dim", 0),
                simd_lanes=getattr(config, "simd_lanes", 1),
                dataflow=getattr(config, "dataflow", "weight_stationary"),
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

        # effective throughput from PE family (vector/systolic etc.)
        _eff = config.macs_per_pe_per_cycle
        try:
            from vse.core.pe_families import ArchFamily, PEFamilyConfig
            fam = getattr(config, "arch_family", "scalar")
            vw = int(getattr(config, "vector_width", 1))
            sd = int(getattr(config, "systolic_dim", 0))
            lanes = int(getattr(config, "simd_lanes", 1))
            pf = PEFamilyConfig(family=ArchFamily(fam) if isinstance(fam, str) else fam, vector_width=vw, systolic_dim=sd, simd_lanes=lanes, dataflow=getattr(config, "dataflow", "weight_stationary"))
            _eff = PEFamilyConfig.effective_macs_per_cycle(_eff, pf) if hasattr(PEFamilyConfig, "effective_macs_per_cycle") else _eff
            # fallback static helper name
            if _eff == config.macs_per_pe_per_cycle:
                try:
                    _eff = pf.effective_macs_per_cycle() if hasattr(pf, "effective_macs_per_cycle") else _eff
                except Exception:
                    pass
        except Exception:
            pass
        # direct family factor fallback
        if _eff == config.macs_per_pe_per_cycle:
            fam = str(getattr(config, "arch_family", "scalar"))
            if fam == "vector":
                _eff = config.macs_per_pe_per_cycle * max(1, int(getattr(config, "vector_width", 1)))
            elif fam == "simd":
                _eff = config.macs_per_pe_per_cycle * max(1, int(getattr(config, "simd_lanes", 1)))
            elif fam in ("systolic", "weight_stationary", "output_stationary"):
                sd = int(getattr(config, "systolic_dim", 0))
                if sd > 0:
                    _eff = config.macs_per_pe_per_cycle * sd * sd
        self.scheduler.add_resource(
            Resource(
                name="compute",
                resource_type=ResourceType.COMPUTE,
                capacity=config.num_pes,
                throughput=_eff,
                pipeline_latency=config.pipeline_latency + (int(getattr(config, "systolic_dim", 0)) if str(getattr(config, "arch_family", "")) in ("systolic","weight_stationary","output_stationary") else 0) + (1 if str(getattr(config, "arch_family", "")) == "vector" else 0),
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
                num_tiles=config.num_tiles,
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


def _maybe_attach_gate(result: EndToEndResult, chip, physics: str = "off") -> None:
    if physics == "off":
        return
    try:
        from vse.physics.gate import PhysicsGate  # lazy
        gate = PhysicsGate.check(result, chip)
        result.gate = gate
        result.gate_result = gate
    except Exception:
        pass


def simulate_transformer(
    model: TransformerModel,
    sequence_length: int,
    config: Optional[HardwareConfig] = None,
    mode: str = "decode",
    target_tokens_per_second: Optional[float] = None,
    physics: str = "off",
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
            arch_family=getattr(config, "arch_family", "scalar"),
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
    _maybe_attach_gate(result, config, physics)

    return result


def simulate_moe(
    moe: MoE,
    tokens: int,
    config: Optional[HardwareConfig] = None,
    target_tokens_per_second: Optional[float] = None,
    physics: str = "off",
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

    tile_hierarchy = None
    if getattr(config, "num_tiles", 1) > 1:
        try:
            from vse.core.tile import TiledHierarchy
            tile_hierarchy = TiledHierarchy.build_tiled_hierarchy(config)
        except Exception:
            tile_hierarchy = None
    machine.scheduler.add_tasks(
        build_moe_tasks(
            cost.routing_cost,
            cost.expert_costs,
            expert_units=(max(1, config.num_pes // active_experts) if active_experts else None),
            weight_bytes_per_expert=weight_bytes_per_expert,
            resident=resident,
            chunks=config.weight_chunks,
            noc=(machine.noc if machine.noc.config.enabled else None),
            tile_hierarchy=tile_hierarchy,
            arch_family=getattr(config, "arch_family", "scalar"),
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
    _maybe_attach_gate(result, config, physics)

    return result
