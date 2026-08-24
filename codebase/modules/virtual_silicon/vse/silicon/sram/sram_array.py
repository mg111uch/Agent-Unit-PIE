"""Physical SRAM array — Phase A physics.

Bandwidth = banks × ports/bank × bits/access × frequency
subject to area / wire-delay / port-limit / energy / thermal.

Scaling via :class:`ProcessTechnology` (energy ∝ node, area ∝ node²).

Wire model:
    wire_delay_ns = 0.1 * sqrt(capacity_bytes / 4096) * (tech.node_nm / 7)

Latency:
    decode(1) + wordline/bitline(2) + ceil(wire_delay_ns * freq / 1e9)

Area per bank:
    capacity_bits * tech.sram_area_um2_per_bit / 1e6 * routing_overhead
    + ports * 0.01 mm²  (port decode/routing overhead)

Energy:
    per_access = bits_per_access * tech.sram_energy_pj_per_bit / 1e6  (µJ)
    per_byte   = 8 * tech.sram_energy_pj_per_bit / 1e6
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from vse.core.memory_hierarchy import MemoryLevel

from vse.silicon.process import DEFAULT, ProcessTechnology

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_PORT_MIN, _PORT_MAX = 1, 4
_BITS_MIN, _BITS_MAX = 8, 512
_PORT_OVERHEAD_MM2 = 0.01  # per port, mm²


def _resolve_tech(tech: Optional[ProcessTechnology]) -> ProcessTechnology:
    return tech if tech is not None else DEFAULT


def _wire_delay_ns(capacity_bytes: int, tech: ProcessTechnology) -> float:
    if capacity_bytes <= 0:
        return 0.0
    return 0.1 * math.sqrt(capacity_bytes / 4096.0) * (tech.node_nm / 7.0)


# ---------------------------------------------------------------------------
# SRAMBank
# ---------------------------------------------------------------------------

@dataclass
class SRAMBank:
    """One physical SRAM bank."""

    capacity_bytes: int
    ports: int = 1
    bits_per_access: int = 32
    frequency_hz: float = 1e9

    def __post_init__(self) -> None:
        self.validate()

    # -- validation -------------------------------------------------------
    def validate(self) -> None:
        if self.capacity_bytes < 0:
            raise ValueError("capacity_bytes must be >= 0")
        if not (_PORT_MIN <= self.ports <= _PORT_MAX):
            raise ValueError(f"ports must be {_PORT_MIN}..{_PORT_MAX}, got {self.ports}")
        if not (_BITS_MIN <= self.bits_per_access <= _BITS_MAX):
            raise ValueError(f"bits_per_access must be {_BITS_MIN}..{_BITS_MAX}, got {self.bits_per_access}")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")

    # -- bandwidth --------------------------------------------------------
    def bandwidth_bytes_per_cycle(self) -> float:
        return self.ports * self.bits_per_access / 8.0

    def bandwidth_bytes_per_second(self) -> float:
        return self.bandwidth_bytes_per_cycle() * self.frequency_hz

    def bandwidth_bits_per_cycle(self) -> float:
        return self.ports * self.bits_per_access

    # -- geometry / wire --------------------------------------------------
    def wire_delay_ns(self, tech: Optional[ProcessTechnology] = None) -> float:
        return _wire_delay_ns(self.capacity_bytes, _resolve_tech(tech))

    @property
    def wire_len_mm(self) -> float:
        """Derived wire length ~ sqrt(area) feedback (mm)."""
        # use DEFAULT tech for derived estimate
        area = self.area_mm2()
        return math.sqrt(max(area, 0.0))

    @property
    def bank_dimensions_mm(self) -> tuple[float, float]:
        side = math.sqrt(max(self.area_mm2(), 0.0))
        return (side, side)

    # -- area -------------------------------------------------------------
    def area_mm2(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = _resolve_tech(tech)
        if self.capacity_bytes <= 0:
            return self.ports * _PORT_OVERHEAD_MM2
        cell_um2 = self.capacity_bytes * 8 * t.sram_area_um2_per_bit
        cell_mm2 = cell_um2 / 1e6
        return cell_mm2 * t.routing_overhead + self.ports * _PORT_OVERHEAD_MM2

    # -- latency ----------------------------------------------------------
    def latency_cycles(
        self,
        tech: Optional[ProcessTechnology] = None,
        frequency_hz: Optional[float] = None,
    ) -> int:
        t = _resolve_tech(tech)
        freq = frequency_hz if frequency_hz is not None else self.frequency_hz
        base = 1 + 2  # decode + wordline/bitline
        wd_ns = _wire_delay_ns(self.capacity_bytes, t)
        if wd_ns <= 0 or freq <= 0:
            return base
        wire_cycles = math.ceil(wd_ns * freq / 1e9)
        return base + wire_cycles

    def latency_ns(
        self,
        tech: Optional[ProcessTechnology] = None,
        frequency_hz: Optional[float] = None,
    ) -> float:
        freq = frequency_hz if frequency_hz is not None else self.frequency_hz
        cycles = self.latency_cycles(tech=tech, frequency_hz=freq)
        return cycles * 1e9 / freq if freq > 0 else 0.0

    # -- energy -----------------------------------------------------------
    def energy_per_access_uj(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = _resolve_tech(tech)
        return self.bits_per_access * t.sram_energy_pj_per_bit / 1e6

    def energy_per_byte_uj(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = _resolve_tech(tech)
        return 8 * t.sram_energy_pj_per_bit / 1e6

    def energy_per_access_pj(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = _resolve_tech(tech)
        return self.bits_per_access * t.sram_energy_pj_per_bit

    # -- report -----------------------------------------------------------
    def report(self, tech: Optional[ProcessTechnology] = None) -> Dict:
        t = _resolve_tech(tech)
        return {
            "capacity_bytes": self.capacity_bytes,
            "ports": self.ports,
            "bits_per_access": self.bits_per_access,
            "frequency_hz": self.frequency_hz,
            "bandwidth_bytes_per_cycle": self.bandwidth_bytes_per_cycle(),
            "bandwidth_bytes_per_second": self.bandwidth_bytes_per_second(),
            "area_mm2": self.area_mm2(t),
            "wire_delay_ns": self.wire_delay_ns(t),
            "latency_cycles": self.latency_cycles(t),
            "latency_ns": self.latency_ns(t),
            "energy_per_access_uj": self.energy_per_access_uj(t),
            "energy_per_byte_uj": self.energy_per_byte_uj(t),
        }


# ---------------------------------------------------------------------------
# SRAMArray
# ---------------------------------------------------------------------------

@dataclass
class SRAMArray:
    """Array of banks — bandwidth = banks × ports × bits × freq."""

    banks: int = 1
    ports_per_bank: int = 1
    bits_per_access: int = 32
    frequency_hz: float = 1e9
    capacity_bytes_total: Optional[int] = None
    tech: Optional[ProcessTechnology] = None
    # legacy compat: single bank instance (stub field)
    bank: Optional[SRAMBank] = None
    # optional explicit capacity alias
    capacity_bytes: Optional[int] = None

    # internal list built lazily
    _banks_cache: Optional[List[SRAMBank]] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        # handle capacity alias
        if self.capacity_bytes_total is None and self.capacity_bytes is not None:
            self.capacity_bytes_total = self.capacity_bytes
        # legacy bank -> infer capacity
        if self.capacity_bytes_total is None and self.bank is not None:
            try:
                self.capacity_bytes_total = self.bank.capacity_bytes * self.banks
            except Exception:
                pass
        self.validate()

    # -- validation -------------------------------------------------------
    def validate(self) -> None:
        if self.banks <= 0:
            raise ValueError("banks must be > 0")
        if not (_PORT_MIN <= self.ports_per_bank <= _PORT_MAX):
            raise ValueError(f"ports_per_bank must be {_PORT_MIN}..{_PORT_MAX}, got {self.ports_per_bank}")
        if not (_BITS_MIN <= self.bits_per_access <= _BITS_MAX):
            raise ValueError(f"bits_per_access must be {_BITS_MIN}..{_BITS_MAX}, got {self.bits_per_access}")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")
        if self.capacity_bytes_total is not None and self.capacity_bytes_total < 0:
            raise ValueError("capacity_bytes_total must be >= 0")
        if self.capacity_bytes is not None and self.capacity_bytes < 0:
            raise ValueError("capacity_bytes must be >= 0")

    def _tech(self, override: Optional[ProcessTechnology] = None) -> ProcessTechnology:
        return _resolve_tech(override if override is not None else self.tech)

    @property
    def capacity_bytes_effective(self) -> int:
        if self.capacity_bytes_total is not None:
            return self.capacity_bytes_total
        if self.capacity_bytes is not None:
            return self.capacity_bytes
        if self.bank is not None:
            return self.bank.capacity_bytes * self.banks
        return 0

    @property
    def capacity_per_bank(self) -> int:
        total = self.capacity_bytes_effective
        if total <= 0 or self.banks <= 0:
            return 0
        return total // self.banks

    def _build_banks(self) -> List[SRAMBank]:
        if self._banks_cache is not None:
            return self._banks_cache
        per_bank = self.capacity_per_bank
        # if total==0 but legacy bank present, reuse
        if per_bank == 0 and self.bank is not None:
            # expand legacy bank
            banks = [
                SRAMBank(
                    capacity_bytes=self.bank.capacity_bytes,
                    ports=self.ports_per_bank,
                    bits_per_access=self.bits_per_access,
                    frequency_hz=self.frequency_hz,
                )
                for _ in range(self.banks)
            ]
        elif per_bank == 0:
            # zero-capacity banks (still valid for bw calc)
            banks = [
                SRAMBank(
                    capacity_bytes=0,
                    ports=self.ports_per_bank,
                    bits_per_access=self.bits_per_access,
                    frequency_hz=self.frequency_hz,
                )
                for _ in range(self.banks)
            ]
        else:
            # split evenly; remainder goes to first banks
            total = self.capacity_bytes_effective
            base = total // self.banks
            rem = total % self.banks
            banks = []
            for i in range(self.banks):
                cap = base + (1 if i < rem else 0)
                banks.append(
                    SRAMBank(
                        capacity_bytes=cap,
                        ports=self.ports_per_bank,
                        bits_per_access=self.bits_per_access,
                        frequency_hz=self.frequency_hz,
                    )
                )
        self._banks_cache = banks
        return banks

    @property
    def bank_list(self) -> List[SRAMBank]:
        return self._build_banks()

    @property
    def banks_list(self) -> List[SRAMBank]:
        return self.bank_list

    # -- bandwidth --------------------------------------------------------
    def bandwidth_bytes_per_cycle(self) -> float:
        return self.banks * self.ports_per_bank * self.bits_per_access / 8.0

    def bandwidth_bytes_per_second(self) -> float:
        return self.bandwidth_bytes_per_cycle() * self.frequency_hz

    def bandwidth_bits_per_cycle(self) -> float:
        return self.banks * self.ports_per_bank * self.bits_per_access

    # -- area -------------------------------------------------------------
    def area_mm2(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = self._tech(tech)
        # if we have explicit banks cache with real capacities, sum
        if self.capacity_bytes_effective > 0:
            return sum(b.area_mm2(t) for b in self._build_banks())
        if self.bank is not None:
            return sum(b.area_mm2(t) for b in self._build_banks())
        # fallback: capacity split evenly estimate without building
        per_bank_cap = self.capacity_per_bank
        if per_bank_cap > 0:
            tmp = SRAMBank(
                capacity_bytes=per_bank_cap,
                ports=self.ports_per_bank,
                bits_per_access=self.bits_per_access,
                frequency_hz=self.frequency_hz,
            )
            return self.banks * tmp.area_mm2(t)
        # no capacity known -> at least port overhead
        return self.banks * self.ports_per_bank * _PORT_OVERHEAD_MM2

    # -- latency ----------------------------------------------------------
    def latency_cycles(self, tech: Optional[ProcessTechnology] = None) -> int:
        t = self._tech(tech)
        banks = self._build_banks()
        if not banks:
            return 3
        return max(b.latency_cycles(t) for b in banks)

    def latency_ns(self, tech: Optional[ProcessTechnology] = None) -> float:
        return self.latency_cycles(tech) * 1e9 / self.frequency_hz

    def wire_delay_ns(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = self._tech(tech)
        banks = self._build_banks()
        if not banks:
            return 0.0
        return max(b.wire_delay_ns(t) for b in banks)

    # -- energy -----------------------------------------------------------
    def energy_per_access_uj(self, tech: Optional[ProcessTechnology] = None) -> float:
        # per-bank access energy
        t = self._tech(tech)
        return self.bits_per_access * t.sram_energy_pj_per_bit / 1e6

    def energy_per_byte_uj(self, tech: Optional[ProcessTechnology] = None) -> float:
        t = self._tech(tech)
        return 8 * t.sram_energy_pj_per_bit / 1e6

    def total_energy_per_cycle_uj(self, tech: Optional[ProcessTechnology] = None) -> float:
        """All banks firing one access per port per cycle."""
        return self.banks * self.ports_per_bank * self.energy_per_access_uj(tech)

    def power_watts(self, tech: Optional[ProcessTechnology] = None, activity: float = 1.0) -> float:
        """Dynamic power at given activity (0..1)."""
        e_per_cycle = self.total_energy_per_cycle_uj(tech) * 1e-6  # J
        return e_per_cycle * self.frequency_hz * activity

    # -- report -----------------------------------------------------------
    def report(self, tech: Optional[ProcessTechnology] = None) -> Dict:
        t = self._tech(tech)
        return {
            "banks": self.banks,
            "ports_per_bank": self.ports_per_bank,
            "bits_per_access": self.bits_per_access,
            "frequency_hz": self.frequency_hz,
            "capacity_bytes_total": self.capacity_bytes_effective,
            "capacity_per_bank": self.capacity_per_bank,
            "bandwidth_bytes_per_cycle": self.bandwidth_bytes_per_cycle(),
            "bandwidth_bytes_per_second": self.bandwidth_bytes_per_second(),
            "area_mm2": self.area_mm2(t),
            "latency_cycles": self.latency_cycles(t),
            "latency_ns": self.latency_ns(t),
            "wire_delay_ns": self.wire_delay_ns(t),
            "energy_per_access_uj": self.energy_per_access_uj(t),
            "energy_per_byte_uj": self.energy_per_byte_uj(t),
            "total_energy_per_cycle_uj": self.total_energy_per_cycle_uj(t),
        }

    # -- helpers ----------------------------------------------------------
    @classmethod
    def from_memory_level(
        cls,
        level: "MemoryLevel",
        tech: Optional[ProcessTechnology] = None,
        frequency_hz: float = 1e9,
        ports_per_bank: int = 1,
        bits_per_access: int = 32,
    ) -> "SRAMArray":
        """Convert a :class:`MemoryLevel` to an :class:`SRAMArray`.

        Bandwidth of the level is treated as derived; the array parameters
        are chosen to approximate it when possible. Defaults keep the
        conversion simple (ports=1, bits=32) and preserve capacity/banks.
        """
        cap = getattr(level, "capacity_bytes", 0) or 0
        banks = getattr(level, "banks", 1) or 1
        # try to infer bits/ports if caller wants exact bw match — not required
        return cls(
            banks=banks,
            ports_per_bank=ports_per_bank,
            bits_per_access=bits_per_access,
            frequency_hz=frequency_hz,
            capacity_bytes_total=cap if cap > 0 else None,
            tech=tech,
        )

    def to_memory_level(self, name: str = "sram") -> "MemoryLevel":
        """Back-convert to :class:`MemoryLevel` with derived bandwidth."""
        from vse.core.memory_hierarchy import MemoryLevel

        bw = int(self.bandwidth_bytes_per_cycle())
        return MemoryLevel(
            name=name,
            capacity_bytes=self.capacity_bytes_effective,
            read_bw_bytes_per_cycle=bw,
            write_bw_bytes_per_cycle=bw,
            banks=self.banks,
        )


__all__ = ["SRAMBank", "SRAMArray"]
