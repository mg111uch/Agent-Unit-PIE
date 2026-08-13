"""
Phase 7 tests: power and area modeling.
"""

import pytest

from vse.silicon.area import AreaEstimate, estimate_area
from vse.silicon.power import PowerEstimate, estimate_power
from vse.silicon.process import DEFAULT, ProcessTechnology
from vse.search.architecture import ArchitectureSpec
from vse.workload import HardwareConfig


class _Result:
    """Stub EndToEndResult-like object for power estimation."""

    total_macs = 10**9
    memory_traffic = {
        "hbm_read_bytes": 1024,
        "hbm_write_bytes": 0,
        "sram_read_bytes": 2048,
        "sram_write_bytes": 0,
    }
    noc = {"bytes": 256}
    tokens = 10
    latency_seconds = 1e-3
    tokens_per_second = 1e4


def test_default_process_validates():
    tech = ProcessTechnology()
    assert tech.node_nm == 7.0
    assert DEFAULT.node_nm == tech.node_nm


def test_process_validates_negative():
    with pytest.raises(ValueError):
        ProcessTechnology(mac_energy_pj=-1)


def test_estimate_area_sram_dominates():
    spec = ArchitectureSpec(
        num_pes=4096,
        sram_bytes=1024**3,
        noc_nodes=16,
    )

    area = estimate_area(spec)

    assert isinstance(area, AreaEstimate)
    assert area.compute_area_mm2 == pytest.approx(4.096)
    assert area.sram_area_mm2 == pytest.approx(429.4967, rel=1e-3)
    assert area.noc_area_mm2 == pytest.approx(0.8)
    assert area.total_area_mm2 == pytest.approx(521.2713, rel=1e-3)
    assert area.sram_area_mm2 > 10 * area.compute_area_mm2


def test_estimate_area_duck_typed_hardware_config():
    config = HardwareConfig(
        num_pes=1024,
        sram_bytes=0,
        noc_nodes=4,
    )

    area = estimate_area(config)

    expected = (
        1024 * 1000 + 4 * 50000
    ) / 1e6 * 1.2
    assert area.total_area_mm2 == pytest.approx(expected)


def test_estimate_area_scales_with_sram():
    base = estimate_area(ArchitectureSpec(sram_bytes=0))
    big = estimate_area(ArchitectureSpec(sram_bytes=2 * 1024**3))

    assert big.total_area_mm2 > base.total_area_mm2


def test_estimate_power_breakdown():
    estimate = estimate_power(_Result())

    assert isinstance(estimate, PowerEstimate)
    assert estimate.compute_energy_uj == pytest.approx(1000.0)
    assert estimate.noc_energy_uj == pytest.approx(0.001024)
    assert estimate.total_energy_uj == pytest.approx(
        estimate.compute_energy_uj
        + estimate.memory_energy_uj
        + estimate.noc_energy_uj
    )
    assert estimate.average_power_watts == pytest.approx(
        estimate.total_energy_uj * 1e-6 / 1e-3
    )
    assert estimate.energy_per_token_uj == pytest.approx(
        estimate.total_energy_uj / 10
    )
    assert estimate.tokens_per_watt == pytest.approx(
        1e4 / estimate.average_power_watts
    )


def test_estimate_power_empty_traffic():
    class Empty:
        total_macs = 0
        memory_traffic = {}
        noc = {}
        tokens = 1
        latency_seconds = 0.0
        tokens_per_second = 0.0

    estimate = estimate_power(Empty())

    assert estimate.total_energy_uj == 0.0
    assert estimate.average_power_watts == 0.0
    assert estimate.tokens_per_watt == 0.0


def test_simulate_populates_power_and_area():
    from vse.models.moe import MoE, MoEConfig
    from vse.workload import simulate_moe

    moe = MoE(
        MoEConfig(
            hidden_dim=512,
            intermediate_dim=1024,
            num_experts=8,
            top_k=2,
        )
    )

    result = simulate_moe(moe, tokens=8)

    assert result.power["total_energy_uj"] > 0
    assert result.power["energy_per_token_uj"] > 0
    assert result.area["total_area_mm2"] > 0
    assert result.area["compute_area_mm2"] == pytest.approx(
        4096 * 1000 / 1e6
    )


def test_process_for_node_scales():
    coarser = ProcessTechnology.for_node(14.0)

    assert coarser.node_nm == 14.0
    assert coarser.mac_area_um2 == pytest.approx(
        1000.0 * (14.0 / 7.0) ** 2
    )
    assert coarser.mac_energy_pj == pytest.approx(
        1.0 * (14.0 / 7.0)
    )
    assert coarser.sram_area_um2_per_bit == pytest.approx(
        0.05 * 4
    )


def test_estimate_power_static_and_thermal_with_chip():
    spec = ArchitectureSpec(num_pes=1024, sram_bytes=0)

    estimate = estimate_power(_Result(), chip=spec)

    area_mm2 = estimate_area(spec).total_area_mm2
    expected_static = (
        area_mm2 * DEFAULT.leakage_density_mw_per_mm2 / 1e3
    )
    dynamic = estimate.total_energy_uj * 1e-6 / _Result().latency_seconds

    assert estimate.static_power_watts == pytest.approx(
        expected_static
    )
    assert estimate.average_power_watts == pytest.approx(
        dynamic + expected_static
    )
    assert estimate.thermal_density_w_per_mm2 == pytest.approx(
        estimate.average_power_watts / area_mm2
    )
    assert estimate.thermally_feasible is True


def test_thermal_infeasible_when_limit_exceeded():
    spec = ArchitectureSpec(
        num_pes=1,
        sram_bytes=16 * 1024**3,
    )
    tech = ProcessTechnology(
        thermal_limit_w_per_mm2=1e-6,
    )

    estimate = estimate_power(_Result(), tech=tech, chip=spec)

    assert estimate.thermally_feasible is False


def test_node_nm_technology_property():
    spec = ArchitectureSpec(node_nm=14.0)
    assert spec.technology.node_nm == pytest.approx(14.0)

    default = ArchitectureSpec()
    assert default.technology is DEFAULT


def test_search_result_real_metrics():
    from vse.search.search import SearchResult

    spec = ArchitectureSpec(num_pes=512, sram_bytes=1024**3)
    item = SearchResult(spec=spec, result=_Result())

    assert item.area_mm2 == estimate_area(spec).total_area_mm2
    assert item.power_watts == estimate_power(
        _Result(),
        chip=spec,
        tech=spec.technology,
    ).average_power_watts
    assert item.tokens_per_watt > 0
    assert item.power_watts > estimate_power(
        _Result()
    ).average_power_watts  # leakage on the 1 GiB SRAM is included
