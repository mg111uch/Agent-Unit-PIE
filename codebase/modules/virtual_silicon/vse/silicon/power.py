"""
VSE - Virtual Silicon Engine
vse/power.py

Phase 7: power and energy estimation.

Computes dynamic energy and power for a simulated end-to-end result from
the actual activity: total MACs, per-level memory traffic, NoC bytes,
and the measured latency. Replaces the crude `ArchitectureSpec.power_proxy`
and provides the Phase-7 metrics — energy/token, tokens/Watt,
tokens/Joule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from vse.silicon.area import estimate_area
from vse.silicon.process import DEFAULT, ProcessTechnology


@dataclass
class PowerEstimate:
    """Energy / power breakdown of one simulation result."""

    compute_energy_uj: float
    memory_energy_uj: float
    noc_energy_uj: float
    total_energy_uj: float
    average_power_watts: float
    energy_per_token_uj: float
    tokens_per_watt: float
    static_power_watts: float = 0.0
    thermal_density_w_per_mm2: float = 0.0
    thermally_feasible: Optional[bool] = None

    def report(self) -> dict:
        return {
            "compute_energy_uj": self.compute_energy_uj,
            "memory_energy_uj": self.memory_energy_uj,
            "noc_energy_uj": self.noc_energy_uj,
            "total_energy_uj": self.total_energy_uj,
            "average_power_watts": (
                self.average_power_watts
            ),
            "energy_per_token_uj": (
                self.energy_per_token_uj
            ),
            "tokens_per_watt": (
                self.tokens_per_watt
            ),
            "static_power_watts": (
                self.static_power_watts
            ),
            "thermal_density_w_per_mm2": (
                self.thermal_density_w_per_mm2
            ),
            "thermally_feasible": (
                self.thermally_feasible
            ),
        }


def estimate_power(
    result,
    tech: ProcessTechnology = DEFAULT,
    chip: object = None,
) -> PowerEstimate:
    """
    Estimate energy/power for an `EndToEndResult` (or anything exposing
    `total_macs`, `memory_traffic`, `noc`, `tokens`, `latency_seconds`,
    `tokens_per_second`).

    `chip` (an `ArchitectureSpec` or `HardwareConfig`) is optional and
    enables static (leakage) power and thermal density: leakage is
    area × leakage density, and the average-power density W/mm² is
    checked against the technology's thermal limit.
    """

    compute_energy_uj = (
        result.total_macs * tech.mac_energy_pj
    ) / 1e6

    traffic = result.memory_traffic or {}

    hbm_bits = (
        traffic.get("hbm_read_bytes", 0)
        + traffic.get("hbm_write_bytes", 0)
    ) * 8

    sram_bits = (
        traffic.get("sram_read_bytes", 0)
        + traffic.get("sram_write_bytes", 0)
    ) * 8

    memory_energy_uj = (
        hbm_bits * tech.hbm_energy_pj_per_bit
        + sram_bits * tech.sram_energy_pj_per_bit
    ) / 1e6

    noc_bits = (
        (result.noc or {}).get("bytes", 0) * 8
    )

    noc_energy_uj = (
        noc_bits * tech.noc_energy_pj_per_bit
    ) / 1e6

    total_energy_uj = (
        compute_energy_uj
        + memory_energy_uj
        + noc_energy_uj
    )

    latency_seconds = result.latency_seconds

    average_power_watts = (
        total_energy_uj * 1e-6 / latency_seconds
        if latency_seconds > 0
        else 0.0
    )

    tokens = max(int(result.tokens), 1)

    energy_per_token_uj = (
        total_energy_uj / tokens
    )

    static_power_watts = 0.0
    thermal_density_w_per_mm2 = 0.0
    thermally_feasible: Optional[bool] = None

    if chip is not None:
        area_mm2 = estimate_area(
            chip,
            tech=tech,
        ).total_area_mm2

        static_power_watts = (
            area_mm2
            * tech.leakage_density_mw_per_mm2
            / 1e3
        )

        average_power_watts += static_power_watts

        if area_mm2 > 0:
            thermal_density_w_per_mm2 = (
                average_power_watts / area_mm2
            )

        thermally_feasible = (
            thermal_density_w_per_mm2
            <= tech.thermal_limit_w_per_mm2
        )

    tokens_per_watt = (
        result.tokens_per_second / average_power_watts
        if average_power_watts > 0
        else 0.0
    )

    return PowerEstimate(
        compute_energy_uj=compute_energy_uj,
        memory_energy_uj=memory_energy_uj,
        noc_energy_uj=noc_energy_uj,
        total_energy_uj=total_energy_uj,
        average_power_watts=average_power_watts,
        energy_per_token_uj=energy_per_token_uj,
        tokens_per_watt=tokens_per_watt,
        static_power_watts=static_power_watts,
        thermal_density_w_per_mm2=(
            thermal_density_w_per_mm2
        ),
        thermally_feasible=thermally_feasible,
    )


__all__ = [
    "PowerEstimate",
    "estimate_power",
]
