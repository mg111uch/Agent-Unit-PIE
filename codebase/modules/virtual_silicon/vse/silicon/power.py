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


def _sram_energy_with_array(
    sram_bits: int,
    chip: object,
    tech: ProcessTechnology,
) -> tuple[float, Optional[float]]:
    """
    Compute SRAM energy using physical SRAMArray when possible.

    Physical bandwidth equation enforced via SRAMArray:
        bandwidth = banks * ports/bank * bits/access * frequency
    subject to area / wire-delay / port-limit / energy.

    Per-access vs per-byte distinction:
        energy_per_access_uj = bits_per_access * sram_energy_pj_per_bit / 1e6
        energy_per_byte_uj   = 8 * sram_energy_pj_per_bit / 1e6
    Array model validates bits/ports and returns per-byte energy
    consistent with the linear scaling but grounded in physical banking.

    Returns (sram_energy_uj, sram_physical_energy_uj_or_None).
    Falls back to bits*energy if chip lacks physical fields.
    """

    if sram_bits <= 0:
        return 0.0, None
    if chip is None:
        return (sram_bits * tech.sram_energy_pj_per_bit) / 1e6, None
    try:
        from vse.silicon.sram.sram_array import SRAMArray

        banks = getattr(
            chip, "sram_banks", getattr(chip, "banks", 1)
        )
        ports = getattr(
            chip,
            "sram_ports",
            getattr(
                chip,
                "ports_per_bank",
                getattr(
                    chip, "sram_ports_per_bank", 1
                ),
            ),
        )
        bits = getattr(
            chip,
            "sram_word_bits",
            getattr(
                chip,
                "bits_per_access",
                getattr(
                    chip, "sram_bits_per_access", 32
                ),
            ),
        )
        freq = getattr(chip, "frequency_hz", 1e9)
        cap = getattr(chip, "sram_bytes", None)
        if cap is not None and cap > 0:
            cap_bytes = int(cap)
        else:
            cap_bytes = sram_bits // 8
        arr = SRAMArray(
            banks=int(banks),
            ports_per_bank=int(ports),
            bits_per_access=int(bits),
            frequency_hz=float(freq),
            capacity_bytes_total=int(cap_bytes)
            if cap_bytes
            else None,
        )
        # physical per-byte energy validated via array
        per_byte = arr.energy_per_byte_uj(tech)
        sram_bytes = sram_bits // 8
        # handle odd bits remainder via proportional energy
        remainder_bits = sram_bits % 8
        energy = sram_bytes * per_byte
        if remainder_bits:
            energy += (
                remainder_bits
                * tech.sram_energy_pj_per_bit
                / 1e6
            )
        return energy, energy
    except Exception:
        return (
            sram_bits * tech.sram_energy_pj_per_bit
        ) / 1e6, None


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
    # physical SRAM array energy (if computed via SRAMArray)
    sram_physical_energy_uj: Optional[float] = None

    def report(self) -> dict:
        out = {
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
        if self.sram_physical_energy_uj is not None:
            out["sram_physical_energy_uj"] = (
                self.sram_physical_energy_uj
            )
        return out


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

    def _sram_bytes_from_traffic(tr: dict) -> tuple[int, int]:
        if not tr:
            return 0, 0
        # aggregated keys present and non-zero -> use them (already sum tiles)
        r_agg = tr.get("sram_read_bytes")
        w_agg = tr.get("sram_write_bytes")
        if r_agg is not None or w_agg is not None:
            r = int(r_agg or 0)
            w = int(w_agg or 0)
            if r != 0 or w != 0:
                return r, w
            # if zero, fall through to tile sum
        # nested traffic dict (tiled hierarchy levels)
        nested = tr.get("traffic")
        if isinstance(nested, dict):
            rs = ws = 0
            found = False
            for lvl, vals in nested.items():
                if not isinstance(vals, dict):
                    continue
                if "sram" in lvl.lower():
                    found = True
                    rs += int(vals.get("read_bytes", 0) or 0)
                    ws += int(vals.get("write_bytes", 0) or 0)
            if found and (rs != 0 or ws != 0):
                return rs, ws
        # sum all keys containing sram or tile
        r = w = 0
        for k, v in tr.items():
            if not isinstance(v, (int, float)):
                continue
            lk = k.lower()
            if "sram" in lk or "tile" in lk:
                if "read" in lk:
                    r += int(v)
                elif "write" in lk:
                    w += int(v)
        if r != 0 or w != 0:
            return r, w
        return int(r_agg or 0), int(w_agg or 0)

    _r, _w = _sram_bytes_from_traffic(traffic)
    sram_bits = (_r + _w) * 8

    # SRAM-array-aware: prefer physical per-byte energy if chip
    # provides banking/ports info; fallback to linear bits*energy.
    sram_energy_uj, sram_physical = (
        _sram_energy_with_array(sram_bits, chip, tech)
    )
    hbm_energy_uj = (
        hbm_bits * tech.hbm_energy_pj_per_bit
    ) / 1e6
    memory_energy_uj = hbm_energy_uj + sram_energy_uj

    # CIM / near-memory path: weight never leaves array -> lower memory energy
    def _chip_is_cim(c) -> bool:
        if c is None:
            return False
        try:
            from vse.core.pe_families import ArchFamily  # noqa: WPS433

            for attr in ("arch_family", "family", "pe_family", "pe_arch"):
                v = getattr(c, attr, None)
                if isinstance(v, ArchFamily) and v in (ArchFamily.cim, ArchFamily.near_memory):
                    return True
        except Exception:
            pass
        for attr in ("arch_family", "family", "pe_family", "pe_arch", "cim"):
            v = getattr(c, attr, None)
            if v is None:
                continue
            if isinstance(v, bool) and attr == "cim" and v:
                return True
            try:
                s = str(v).lower()
            except Exception:
                continue
            if s in ("cim", "near_memory", "near-memory", "near_memory_cim"):
                return True
        return False

    if _chip_is_cim(chip):
        # sram_cim_energy_per_mac ~ 0.5 * sram_energy per bit * 8 bits per byte
        # or 0.2 * mac_energy; use min for conservative lower bound
        sram_cim_per_mac_pj = tech.sram_energy_pj_per_bit * 8 * 0.5
        alt_per_mac_pj = tech.mac_energy_pj * 0.2
        per_mac_pj = min(sram_cim_per_mac_pj, alt_per_mac_pj)
        cim_sram_uj = (result.total_macs * per_mac_pj) / 1e6
        # HBM traffic reduced (weights resident in array)
        hbm_scaled_uj = hbm_energy_uj * 0.2
        memory_energy_uj = cim_sram_uj + hbm_scaled_uj
        sram_physical = cim_sram_uj

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
        sram_physical_energy_uj=sram_physical,
    )


__all__ = [
    "PowerEstimate",
    "estimate_power",
]
