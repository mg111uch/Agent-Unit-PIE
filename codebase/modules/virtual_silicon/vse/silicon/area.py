"""
VSE - Virtual Silicon Engine
vse/area.py

Phase 7: silicon area estimation.

Estimates the die area of a candidate chip from its PE array, SRAM
capacity, and NoC router count using a `ProcessTechnology`. Replaces the
crude `ArchitectureSpec.area_proxy` with an area model grounded in
process constants.
"""

from __future__ import annotations

from dataclasses import dataclass

from vse.silicon.process import DEFAULT, ProcessTechnology


@dataclass
class AreaEstimate:
    """Area breakdown of one chip, in mm²."""

    compute_area_mm2: float
    sram_area_mm2: float
    noc_area_mm2: float
    total_area_mm2: float

    def report(self) -> dict:
        return {
            "compute_area_mm2": (
                self.compute_area_mm2
            ),
            "sram_area_mm2": self.sram_area_mm2,
            "noc_area_mm2": self.noc_area_mm2,
            "total_area_mm2": self.total_area_mm2,
        }


def estimate_area(
    chip,
    tech: ProcessTechnology = DEFAULT,
) -> AreaEstimate:
    """
    Estimate die area for any chip description exposing `num_pes`,
    `macs_per_pe`, `sram_bytes`, and `noc_nodes` (e.g. an
    `ArchitectureSpec` or `HardwareConfig`).
    """

    compute_um2 = (
        chip.num_pes
        * getattr(
            chip,
            "macs_per_pe",
            getattr(
                chip,
                "macs_per_pe_per_cycle",
                1,
            ),
        )
        * tech.mac_area_um2
    )

    sram_um2 = (
        chip.sram_bytes
        * 8
        * tech.sram_area_um2_per_bit
    )

    noc_um2 = (
        chip.noc_nodes
        * tech.noc_area_um2_per_node
    )

    total_um2 = (
        compute_um2 + sram_um2 + noc_um2
    ) * tech.routing_overhead

    return AreaEstimate(
        compute_area_mm2=compute_um2 / 1e6,
        sram_area_mm2=sram_um2 / 1e6,
        noc_area_mm2=noc_um2 / 1e6,
        total_area_mm2=total_um2 / 1e6,
    )


__all__ = [
    "AreaEstimate",
    "estimate_area",
]
