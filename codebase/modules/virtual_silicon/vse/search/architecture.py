"""
VSE - Virtual Silicon Engine
vse/architecture.py

Phase 6: declarative chip descriptions for hardware architecture search.

An `ArchitectureSpec` is a self-contained description of one candidate
chip plus its compile-time decisions. It can produce the `HardwareConfig`
and `CompileOptions` consumed by the compiler, and carries simple
area/power proxies used to build Pareto frontiers (Phase 7 replaces the
proxies with real models).

A `SearchSpace` declares which dimensions vary and over which values.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from itertools import product
from typing import Optional

from vse.compiler.compiler import CompileOptions
from vse.workload import HardwareConfig


# ---------------------------------------------------------------------------
# Chip description
# ---------------------------------------------------------------------------

@dataclass
class ArchitectureSpec:
    """
    One candidate chip + compile-time decisions.

    `to_hardware_config` / `to_compile_options` feed the existing
    compile-and-simulate pipeline; `area_proxy` / `power_proxy` are
    lightweight silicon cost estimates for ranking candidates.
    """

    num_pes: int = 4096
    macs_per_pe: int = 1
    frequency_hz: float = 1e9
    pipeline_latency: int = 0
    sram_bytes: int = 0
    hbm_bytes_per_cycle: int = 256
    sram_bytes_per_cycle: int = 256
    banks: int = 1
    weight_chunks: int = 4
    noc_topology: str = "ring"
    noc_nodes: int = 1
    noc_link_bw: int = 256

    weight_bits: Optional[int] = None
    activation_bits: Optional[int] = None
    kv_bits: Optional[int] = None
    fusion: bool = True
    expert_replicas: int = 1
    expert_placement: str = "round_robin"
    batch_tokens: Optional[int] = None
    node_nm: Optional[float] = None

    def to_hardware_config(self) -> HardwareConfig:
        return HardwareConfig(
            num_pes=self.num_pes,
            macs_per_pe_per_cycle=self.macs_per_pe,
            memory_bytes_per_cycle=self.hbm_bytes_per_cycle,
            frequency_hz=self.frequency_hz,
            pipeline_latency=self.pipeline_latency,
            sram_bytes=self.sram_bytes,
            banks=self.banks,
            hbm_bytes_per_cycle=self.hbm_bytes_per_cycle,
            sram_bytes_per_cycle=self.sram_bytes_per_cycle,
            weight_chunks=self.weight_chunks,
            noc_topology=self.noc_topology,
            noc_nodes=self.noc_nodes,
            noc_link_bw=self.noc_link_bw,
        )

    def to_compile_options(self) -> CompileOptions:
        return CompileOptions(
            weight_bits=self.weight_bits,
            activation_bits=self.activation_bits,
            kv_bits=self.kv_bits,
            fusion=self.fusion,
            expert_placement=self.expert_placement,
            replicas=self.expert_replicas,
        )

    @property
    def technology(self) -> "ProcessTechnology":
        """
        Process technology for this chip: scaled to `node_nm` when set,
        otherwise the DEFAULT (~7 nm) technology.
        """

        from vse.silicon.process import DEFAULT, ProcessTechnology

        if self.node_nm is None:
            return DEFAULT

        return ProcessTechnology.for_node(
            self.node_nm
        )

    @property
    def area_proxy(self) -> float:
        """
        Simple silicon-area proxy: PEs dominate; SRAM is large but dense
        (one unit per 4 KiB of capacity).
        """
        return float(self.num_pes) + self.sram_bytes / 4096.0

    @property
    def power_proxy(self) -> float:
        """
        Dynamic-power proxy: compute + memory + interconnect activity.
        Only relative ordering matters.
        """
        ghz = self.frequency_hz / 1e9
        compute = self.num_pes * self.macs_per_pe * ghz
        memory = self.hbm_bytes_per_cycle * ghz
        noc = self.noc_nodes * self.noc_link_bw * ghz
        return compute + memory + noc

    def label(self) -> str:
        return (
            f"{self.num_pes}PE x{self.macs_per_pe}MAC "
            f"{self.frequency_hz / 1e9:.1f}GHz "
            f"{self.sram_bytes // 1024**2}MB "
            f"{self.hbm_bytes_per_cycle}B/cy "
            f"w{self.weight_bits or 'm'}b"
        )


# ---------------------------------------------------------------------------
# Search space
# ---------------------------------------------------------------------------

def _sram_gb_to_bytes(value: str) -> int:
    return int(float(value) * 1024**3)


DIM_FIELDS: dict[str, tuple[str, callable]] = {
    "num_pes": ("num_pes", int),
    "macs_per_pe": ("macs_per_pe", int),
    "freq": ("frequency_hz", float),
    "pipeline": ("pipeline_latency", int),
    "sram_gb": ("sram_bytes", _sram_gb_to_bytes),
    "hbm_bw": ("hbm_bytes_per_cycle", int),
    "sram_bw": ("sram_bytes_per_cycle", int),
    "banks": ("banks", int),
    "double_buffer": ("weight_chunks", int),
    "noc_topology": ("noc_topology", str),
    "noc_nodes": ("noc_nodes", int),
    "noc_bw": ("noc_link_bw", int),
    "weight_bits": ("weight_bits", int),
    "activation_bits": ("activation_bits", int),
    "kv_bits": ("kv_bits", int),
    "fusion": ("fusion", bool),
    "replicas": ("expert_replicas", int),
    "placement": ("expert_placement", str),
    "tokens": ("batch_tokens", int),
    "node_nm": ("node_nm", float),
}


@dataclass
class SearchSpace:
    """
    Named dimensions, each expanded to an explicit list of values.

    Dimension keys use the names in `DIM_FIELDS` (e.g. "num_pes",
    "sram_gb", "hbm_bw", "weight_bits").
    """

    dims: dict[str, list] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, values in self.dims.items():
            if name not in DIM_FIELDS:
                raise ValueError(
                    f"unknown search dimension: {name}"
                )
            if not values:
                raise ValueError(
                    f"dimension {name} needs >= 1 value"
                )

    @property
    def size(self) -> int:
        total = 1
        for values in self.dims.values():
            total *= len(values)
        return total

    def specs(
        self,
        base: Optional[ArchitectureSpec] = None,
    ) -> list[ArchitectureSpec]:
        """
        Cross-product of every dimension over `base` → candidate specs.

        Raw values are converted through `DIM_FIELDS` (e.g. "sram_gb"
        values are bytes after conversion).
        """

        if base is None:
            base = ArchitectureSpec()

        overrides: dict[str, list] = {}

        for name, values in self.dims.items():
            field_name, converter = DIM_FIELDS[name]
            overrides[field_name] = [
                converter(value)
                for value in values
            ]

        if not overrides:
            return [replace(base)]

        candidates: list[ArchitectureSpec] = []

        for combo in product(*overrides.values()):
            kwargs = dict(zip(overrides.keys(), combo))
            candidates.append(
                replace(base, **kwargs)
            )

        return candidates

    def sample_specs(
        self,
        n: int,
        base: Optional[ArchitectureSpec] = None,
        seed: Optional[int] = None,
    ) -> list[ArchitectureSpec]:
        """
        Randomly sample `n` candidate specs from the space (uniform over
        each dimension). Lets searches scale well past the full grid.
        """

        if n < 1:
            raise ValueError("n must be >= 1")

        if base is None:
            base = ArchitectureSpec()

        rng = random.Random(seed)
        names = list(self.dims.keys())
        candidates: list[ArchitectureSpec] = []

        for _ in range(n):
            kwargs = {}

            for name in names:
                field_name, converter = DIM_FIELDS[name]
                kwargs[field_name] = converter(
                    rng.choice(self.dims[name])
                )

            candidates.append(
                replace(base, **kwargs)
            )

        return candidates


__all__ = [
    "ArchitectureSpec",
    "DIM_FIELDS",
    "SearchSpace",
]
