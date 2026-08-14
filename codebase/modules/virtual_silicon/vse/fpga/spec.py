"""
VSE - Virtual Silicon Engine
vse/fpga/spec.py

Phase 8: hardware specification (the "Python VSE → Hardware
specification" step of the FPGA prototype pipeline).

An `FPGASpec` turns a `HardwareConfig` + compile-time precision into a
concrete, RTL-ready description of a small prototype chip: PE array,
datapath bit widths, quantization, SRAM banks, and NoC. It is the input
to both the SystemVerilog code generator (rtl.py) and the pure-Python
cycle-accurate simulator (sim.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from vse.workload import HardwareConfig


@dataclass
class FPGASpec:
    """
    One small FPGA prototype chip, concrete enough for RTL generation.

    The FPGA does not implement the full giant model: it starts with a
    small model, small number of experts, and a small PE array, and
    scales conceptually (roadmap Phase 8).
    """

    # Compute array.
    num_pes: int = 4
    macs_per_pe: int = 1
    pipeline_depth: int = 2

    # Datapath quantization.
    weight_bits: int = 4
    activation_bits: int = 16
    accumulator_bits: int = 24
    frac_bits: int = 8

    # Memory architecture (SRAM banks).
    sram_banks: int = 4
    sram_words_per_bank: int = 256
    sram_word_bits: int = 32
    sram_bw_words_per_cycle: int = 1

    # NoC.
    noc_topology: str = "ring"
    noc_nodes: int = 1
    noc_per_hop_cycles: int = 4
    noc_link_bw_words: int = 1

    frequency_hz: float = 100e6

    def __post_init__(self) -> None:
        if self.num_pes <= 0:
            raise ValueError("num_pes must be > 0")

        if self.macs_per_pe <= 0:
            raise ValueError("macs_per_pe must be > 0")

        if self.pipeline_depth < 0:
            raise ValueError("pipeline_depth must be >= 0")

        for name in ("weight_bits", "activation_bits", "accumulator_bits"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be > 0")

        if self.frac_bits < 0:
            raise ValueError("frac_bits must be >= 0")

        if self.sram_banks <= 0:
            raise ValueError("sram_banks must be > 0")

        if self.sram_words_per_bank <= 0:
            raise ValueError("sram_words_per_bank must be > 0")

        if self.noc_topology not in ("ring", "mesh"):
            raise ValueError(
                f"unknown NoC topology '{self.noc_topology}'"
            )

        if self.noc_nodes < 1:
            raise ValueError("noc_nodes must be >= 1")

        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")

    # ------------------------------------------------------------------
    # Construction from VSE hardware + compile-time decisions
    # ------------------------------------------------------------------

    @classmethod
    def from_hardware(
        cls,
        config: HardwareConfig,
        weight_bits: Optional[int] = None,
        activation_bits: Optional[int] = None,
        frac_bits: int = 8,
    ) -> "FPGASpec":
        """Build a small FPGA prototype spec from a VSE chip config."""

        wb = weight_bits or 4
        ab = activation_bits or 16
        accum = cls._accumulator_bits(
            wb,
            ab,
            config.num_pes,
        )

        return cls(
            num_pes=min(config.num_pes, 64),
            macs_per_pe=config.macs_per_pe_per_cycle,
            pipeline_depth=config.pipeline_latency,
            weight_bits=wb,
            activation_bits=ab,
            accumulator_bits=accum,
            frac_bits=frac_bits,
            sram_banks=config.banks,
            sram_bw_words_per_cycle=1,
            noc_topology=config.noc_topology,
            noc_nodes=config.noc_nodes,
            noc_per_hop_cycles=config.noc_per_hop_cycles,
            frequency_hz=config.frequency_hz,
        )

    @staticmethod
    def _accumulator_bits(
        weight_bits: int,
        activation_bits: int,
        accumulation_depth: int,
    ) -> int:
        """Widest product + growth over `accumulation_depth` terms."""

        if accumulation_depth <= 0:
            accumulation_depth = 1

        growth = int(
            math.ceil(math.log2(accumulation_depth))
        )

        return (
            weight_bits
            + activation_bits
            + growth
        )

    # ------------------------------------------------------------------
    # Derived datapath properties
    # ------------------------------------------------------------------

    @property
    def pe_throughput_macs_per_cycle(self) -> int:
        return self.num_pes * self.macs_per_pe

    @property
    def sram_words(self) -> int:
        return self.sram_words_per_bank * self.sram_banks

    def quantize(
        self,
        value: float,
        bits: Optional[int] = None,
    ) -> int:
        """Round `value` to the datapath's fixed-point grid."""

        width = bits or self.activation_bits
        scale = 2 ** self.frac_bits
        scaled = value * scale
        rounded = int(math.floor(scaled + 0.5))
        return self._saturate(rounded, width)

    def quantize_weight(self, value: float) -> int:
        return self._saturate(
            int(math.floor(value * (2 ** self.frac_bits) + 0.5)),
            self.weight_bits,
        )

    @staticmethod
    def _saturate(value: int, bits: int) -> int:
        limit = 2 ** (bits - 1)
        return max(-limit, min(limit - 1, value))

    def label(self) -> str:
        return (
            f"{self.num_pes}PE x{self.macs_per_pe}MAC "
            f"w{self.weight_bits}b a{self.activation_bits}b "
            f"{self.sram_banks} banks "
            f"{self.noc_topology}/{self.noc_nodes} nodes"
        )

    def report(self) -> dict:
        return {
            "num_pes": self.num_pes,
            "macs_per_pe": self.macs_per_pe,
            "pe_throughput_macs_per_cycle": (
                self.pe_throughput_macs_per_cycle
            ),
            "pipeline_depth": self.pipeline_depth,
            "quantization": {
                "weight_bits": self.weight_bits,
                "activation_bits": self.activation_bits,
                "accumulator_bits": self.accumulator_bits,
                "frac_bits": self.frac_bits,
            },
            "memory": {
                "sram_banks": self.sram_banks,
                "sram_words_per_bank": self.sram_words_per_bank,
                "sram_word_bits": self.sram_word_bits,
                "sram_total_words": self.sram_words,
            },
            "noc": {
                "topology": self.noc_topology,
                "nodes": self.noc_nodes,
                "per_hop_cycles": self.noc_per_hop_cycles,
            },
            "frequency_hz": self.frequency_hz,
        }


__all__ = ["FPGASpec"]