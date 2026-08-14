"""
Phase 8 tests: FPGA prototype toolchain (spec, RTL, sim, validation).
"""

import pytest

from vse.fpga.spec import FPGASpec
from vse.fpga.rtl import (
    generate_pe,
    generate_router,
    generate_rtl,
    generate_sram,
    generate_top,
)
from vse.fpga.sim import (
    ComputeArraySim,
    NoCSim,
    PEDatapath,
    PipelineSim,
    SRAMSim,
    vse_cycles_for,
)
from vse.fpga.validate import (
    FpgaValidationResult,
    format_fpga_report,
    validate_fpga,
)
from vse.workload import HardwareConfig


# ---------------------------------------------------------------------------
# Spec
# ---------------------------------------------------------------------------

def test_spec_from_hardware_small_array():
    config = HardwareConfig(
        num_pes=8,
        macs_per_pe_per_cycle=2,
        pipeline_latency=3,
    )

    spec = FPGASpec.from_hardware(config)

    assert spec.num_pes == 8
    assert spec.macs_per_pe == 2
    assert spec.pipeline_depth == 3
    assert spec.pe_throughput_macs_per_cycle == 16
    assert spec.noc_nodes == 1


def test_spec_from_hardware_caps_pe_count():
    config = HardwareConfig(num_pes=4096)

    spec = FPGASpec.from_hardware(config)

    assert spec.num_pes == 64
    assert spec.label().startswith("64PE")


def test_spec_accumulator_growth():
    spec = FPGASpec(weight_bits=4, activation_bits=16)

    growth = FPGASpec._accumulator_bits(4, 16, 4)

    assert growth == 4 + 16 + 2


def test_spec_quantize_rounds_and_saturates():
    spec = FPGASpec(activation_bits=8, frac_bits=0)

    assert spec.quantize(0.5) == 1
    assert spec.quantize(0.4) == 0
    assert spec.quantize(-0.4) == 0
    assert spec.quantize(-1.2) == -1
    assert spec.quantize(200.0) == 127
    assert spec.quantize(-200.0) == -128


def test_spec_validates_invalid_values():
    with pytest.raises(ValueError):
        FPGASpec(num_pes=0)

    with pytest.raises(ValueError):
        FPGASpec(noc_topology="torus")

    with pytest.raises(ValueError):
        FPGASpec(sram_banks=0)


def test_spec_report_fields():
    report = FPGASpec().report()

    assert report["quantization"]["weight_bits"] == 4
    assert report["memory"]["sram_banks"] == 4
    assert report["noc"]["topology"] == "ring"


# ---------------------------------------------------------------------------
# RTL codegen
# ---------------------------------------------------------------------------

def test_generate_rtl_contains_all_modules():
    sv = generate_rtl(FPGASpec())

    for module in (
        "module vse_pe",
        "module vse_sram_bank",
        "module vse_router",
        "module vse_soc_top",
    ):
        assert module in sv


def test_generate_pe_combinational_when_depth_zero():
    sv = generate_pe(FPGASpec(pipeline_depth=0))

    assert "Combinational MAC (depth 0)." in sv


def test_generate_pe_pipelined_when_depth_positive():
    sv = generate_pe(FPGASpec(pipeline_depth=3))

    assert "acc_pipe [DEPTH]" in sv
    assert "DEPTH" in sv


def test_generate_sram_word_count():
    sv = generate_sram(FPGASpec(sram_words_per_bank=128))

    assert "WORDS = 128" in sv
    assert "logic [WIDTH-1:0] mem [WORDS];" in sv


def test_generate_router_hop_arithmetic():
    sv = generate_router(FPGASpec(noc_nodes=4, noc_per_hop_cycles=4))

    assert "NODES = 4" in sv
    assert "HOP_CYCLES = 4" in sv


def test_generate_top_instantiates_pes_and_sram():
    sv = generate_top(FPGASpec(num_pes=4, sram_banks=4))

    assert "NUM_PES = 4" in sv
    assert "pe_0" in sv and "pe_3" in sv
    assert "vse_sram_bank" in sv


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

def test_vse_cycles_for_matches_engine_arithmetic():
    # ceil(256 / (4*1)) + 2 pipeline = 64 + 2 = 66
    assert vse_cycles_for(256, 4, 1, 2) == 66
    assert vse_cycles_for(0, 4, 1, 2) == 2
    assert vse_cycles_for(257, 4, 1, 0) == 65


def test_compute_array_run_macs_occupancy_and_drain():
    sim = ComputeArraySim(FPGASpec(num_pes=4, pipeline_depth=2))

    result = sim.run_macs(256)

    assert result["occupancy_cycles"] == 64
    assert result["pipeline_drain_cycles"] == 2
    assert result["cycles"] == 66
    assert result["macs_issued"] == 256
    assert result["throughput_per_cycle"] == 4


def test_compute_array_matmul_mac_count():
    sim = ComputeArraySim(FPGASpec())

    _, report = sim.matmul([[1, 2], [3, 4]], [[1, 0], [0, 1]])

    assert report["macs"] == 8
    assert report["output_shape"] == (2, 2)


def test_pe_datapath_accumulates_and_drains():
    pe = PEDatapath(depth=2)

    acc, drain = pe.accumulate([3, 5, 7], accumulate=True)

    assert acc == 15
    assert drain == 2


def test_sram_parallel_vs_conflict():
    sim = SRAMSim(FPGASpec(sram_banks=4, sram_bw_words_per_cycle=1))

    parallel = sim.parallel_access([(0, 4), (1, 4), (2, 4), (3, 4)])
    conflict = sim.parallel_access([(0, 4), (0, 4), (0, 4), (0, 4)])

    assert parallel["cycles"] == 4
    assert conflict["cycles"] == 16
    assert parallel["peak_banks_used"] == 4


def test_noc_ring_hops_match_vse_noc():
    from vse.core.noc import NoC, NoCConfig

    spec = FPGASpec(noc_topology="ring", noc_nodes=8)
    sim = NoCSim(spec)

    vse_noc = NoC(NoCConfig(topology="ring", nodes=8))

    for src in range(8):
        for dst in range(8):
            assert sim.hops(src, dst) == vse_noc.distance(src, dst)


def test_noc_mesh_hops_match_vse_noc():
    from vse.core.noc import NoC, NoCConfig

    spec = FPGASpec(noc_topology="mesh", noc_nodes=9)
    sim = NoCSim(spec)

    vse_noc = NoC(NoCConfig(topology="mesh", nodes=9))

    for src in range(9):
        for dst in range(9):
            assert sim.hops(src, dst) == vse_noc.distance(src, dst)


def test_noc_transfer_latency():
    sim = NoCSim(FPGASpec(noc_topology="ring", noc_nodes=4, noc_per_hop_cycles=4))

    transfer = sim.transfer(0, 2)

    assert transfer["hops"] == 2
    assert transfer["latency_cycles"] == 8


def test_pipeline_fill_and_steady_throughput():
    sim = PipelineSim(FPGASpec(num_pes=4, pipeline_depth=2))

    result = sim.run(100)

    assert result["fill_cycles"] == 2
    assert result["steady_throughput"] == 4


# ---------------------------------------------------------------------------
# Validation harness
# ---------------------------------------------------------------------------

def test_validate_fpga_all_concerns_pass():
    config = HardwareConfig(
        num_pes=4,
        macs_per_pe_per_cycle=1,
        pipeline_latency=2,
    )

    result = validate_fpga(config, macs=256, banks=4)

    assert isinstance(result, FpgaValidationResult)
    assert result.all_passed
    assert len(result.concerns) == 6

    names = {c.name for c in result.concerns}
    assert names == {
        "scheduler",
        "datapath",
        "memory",
        "routing",
        "quantization",
        "pipeline",
    }


def test_validate_fpga_report_shape():
    result = validate_fpga(HardwareConfig(num_pes=8), macs=128)

    report = result.report()

    assert report["all_passed"] is True
    assert report["macs"] == 128
    assert len(report["concerns"]) == 6
    assert all(c["passed"] for c in report["concerns"])
    assert {c["name"] for c in report["concerns"]} == {
        "scheduler",
        "datapath",
        "memory",
        "routing",
        "quantization",
        "pipeline",
    }


def test_validate_fpga_scheduler_matches_engine():
    config = HardwareConfig(
        num_pes=4,
        macs_per_pe_per_cycle=1,
        pipeline_latency=2,
    )

    result = validate_fpga(config, macs=256)

    scheduler = next(
        c for c in result.concerns if c.name == "scheduler"
    )

    assert scheduler.expected == 66
    assert scheduler.measured == 66


def test_format_fpga_report_mentions_all_concerns():
    result = validate_fpga(HardwareConfig(num_pes=4), macs=64)

    text = format_fpga_report(result)

    for name in (
        "scheduler",
        "datapath",
        "memory",
        "routing",
        "quantization",
        "pipeline",
    ):
        assert name in text

    assert "all assumptions validated" in text


def test_format_fpga_report_shows_failures():
    from vse.fpga.validate import _Concern

    result = FpgaValidationResult(
        spec=FPGASpec(),
        macs=10,
        concerns=[
            _Concern(
                name="scheduler",
                passed=False,
                expected=5,
                measured=9,
            ),
        ],
    )

    text = format_fpga_report(result)

    assert "FAIL" in text
    assert "FAILURE" in text


def test_fpga_cli_subcommand_registered():
    from vse.cli import build_parser

    parser = build_parser()

    args = parser.parse_args(
        ["fpga", "--num-pes", "8", "--macs", "128"]
    )

    assert args.command == "fpga"
    assert args.num_pes == 8
    assert args.macs == 128


def test_fpga_cli_runs_and_returns_zero():
    from vse.cli_cmds.fpga import run_fpga_command

    class _Args:
        num_pes = 4
        macs_per_pe = 1
        pipeline = 2
        freq = 100e6
        weight_bits = None
        activation_bits = None
        frac_bits = 8
        macs = 128
        banks = 4
        noc_nodes = 4
        noc_topology = "ring"
        rtl = False
        json = True

    assert run_fpga_command(_Args()) == 0