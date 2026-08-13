"""
VSE - Virtual Silicon Engine
vse/process.py

Phase 7: semiconductor process technology parameters.

A `ProcessTechnology` bundles the physical constants that the area and
power models need: per-MAC and per-bit energies, per-unit areas, and
overheads. The defaults are order-of-magnitude estimates for a ~7 nm
node, meant to make the models behave like real silicon; pass a custom
`ProcessTechnology` to any model to use your own numbers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProcessTechnology:
    """
    Physical constants for one semiconductor process.

    node_nm: lithography node.
    * Energy is dynamic (switching) energy per operation.
    * Area is per building block.
    """

    node_nm: float = 7.0

    # Energies (picojoules).
    mac_energy_pj: float = 1.0
    sram_energy_pj_per_bit: float = 0.005
    hbm_energy_pj_per_bit: float = 10.0
    noc_energy_pj_per_bit: float = 0.5

    # Areas (µm²).
    mac_area_um2: float = 1000.0
    sram_area_um2_per_bit: float = 0.05
    noc_area_um2_per_node: float = 50000.0

    # Overheads.
    routing_overhead: float = 1.2
    leakage_density_mw_per_mm2: float = 50.0
    thermal_limit_w_per_mm2: float = 1.0

    def __post_init__(self) -> None:
        if self.node_nm <= 0:
            raise ValueError("node_nm must be > 0")

        for name, value in {
            "mac_energy_pj": self.mac_energy_pj,
            "sram_energy_pj_per_bit": (
                self.sram_energy_pj_per_bit
            ),
            "hbm_energy_pj_per_bit": (
                self.hbm_energy_pj_per_bit
            ),
            "noc_energy_pj_per_bit": (
                self.noc_energy_pj_per_bit
            ),
            "mac_area_um2": self.mac_area_um2,
            "sram_area_um2_per_bit": (
                self.sram_area_um2_per_bit
            ),
            "noc_area_um2_per_node": (
                self.noc_area_um2_per_node
            ),
            "routing_overhead": (
                self.routing_overhead
            ),
            "leakage_density_mw_per_mm2": (
                self.leakage_density_mw_per_mm2
            ),
            "thermal_limit_w_per_mm2": (
                self.thermal_limit_w_per_mm2
            ),
        }.items():
            if value <= 0:
                raise ValueError(
                    f"{name} must be > 0"
                )

    @classmethod
    def for_node(
        cls,
        node_nm: float,
        base: "ProcessTechnology" = None,
    ) -> "ProcessTechnology":
        """
        Scale the DEFAULT technology to a different lithography node.

        First-order scaling only: dynamic energy per operation scales
        ~linearly with node (capacitance), and area scales ~with node².
        Not a substitute for real process data.
        """

        if base is None:
            base = DEFAULT

        ratio = node_nm / base.node_nm

        return cls(
            node_nm=node_nm,
            mac_energy_pj=(
                base.mac_energy_pj * ratio
            ),
            sram_energy_pj_per_bit=(
                base.sram_energy_pj_per_bit * ratio
            ),
            hbm_energy_pj_per_bit=(
                base.hbm_energy_pj_per_bit * ratio
            ),
            noc_energy_pj_per_bit=(
                base.noc_energy_pj_per_bit * ratio
            ),
            mac_area_um2=(
                base.mac_area_um2 * ratio**2
            ),
            sram_area_um2_per_bit=(
                base.sram_area_um2_per_bit
                * ratio**2
            ),
            noc_area_um2_per_node=(
                base.noc_area_um2_per_node
                * ratio**2
            ),
            routing_overhead=base.routing_overhead,
            leakage_density_mw_per_mm2=(
                base.leakage_density_mw_per_mm2
            ),
            thermal_limit_w_per_mm2=(
                base.thermal_limit_w_per_mm2
            ),
        )


DEFAULT = ProcessTechnology()

__all__ = [
    "ProcessTechnology",
    "DEFAULT",
]
