"""
Phase 10 tests: physical estimation + closed-loop ASIC exploration.
"""

import pytest

from vse.asic.loop import (
    DesignLoopResult,
    LoopIteration,
    format_design_loop_report,
    run_design_loop,
)
from vse.asic.physical import (
    PhysicalEstimate,
    estimate_gates,
    estimate_physical,
)
from vse.fpga.spec import FPGASpec
from vse.search.architecture import ArchitectureSpec


# ---------------------------------------------------------------------------
# Physical estimation
# ---------------------------------------------------------------------------

def test_estimate_gates_scales_with_spec():
    small = estimate_gates(FPGASpec(num_pes=4))
    large = estimate_gates(FPGASpec(num_pes=256))

    assert large > small
    assert small > 0


def test_estimate_gates_counts_sram():
    no_sram = estimate_gates(
        FPGASpec(num_pes=4, sram_banks=1, sram_words_per_bank=1)
    )
    with_sram = estimate_gates(
        FPGASpec(num_pes=4, sram_banks=8, sram_words_per_bank=256)
    )

    assert with_sram > no_sram


def test_estimate_gates_works_for_arch_spec():
    spec = ArchitectureSpec(num_pes=64, sram_bytes=1024**3)

    assert estimate_gates(spec) > estimate_gates(
        ArchitectureSpec(num_pes=64, sram_bytes=0)
    )


def test_estimate_physical_returns_estimate():
    spec = FPGASpec(num_pes=8, frequency_hz=100e6)

    p = estimate_physical(spec)

    assert isinstance(p, PhysicalEstimate)
    assert p.gates > 0
    assert p.die_area_mm2 > 0
    assert p.achievable_freq_hz > 0


def test_timing_closes_at_reasonable_clock():
    slow = estimate_physical(
        FPGASpec(num_pes=8, frequency_hz=100e6)
    )
    fast = estimate_physical(
        FPGASpec(num_pes=64, frequency_hz=5e9)
    )

    assert slow.timing_closed is True
    assert fast.timing_closed is False
    assert slow.timing_slack_ps > 0
    assert fast.timing_slack_ps < 0


def test_pipeline_deepening_reduces_critical_path():
    flat = estimate_physical(
        ArchitectureSpec(num_pes=64, frequency_hz=1e9, pipeline_latency=1)
    )
    deep = estimate_physical(
        ArchitectureSpec(num_pes=64, frequency_hz=1e9, pipeline_latency=8)
    )

    assert deep.critical_path_ns < flat.critical_path_ns


def test_physical_report_fields():
    report = estimate_physical(
        FPGASpec(num_pes=4)
    ).report()

    for key in (
        "gates",
        "die_area_mm2",
        "critical_path_ns",
        "wire_delay_ns",
        "achievable_freq_hz",
        "requested_freq_hz",
        "timing_slack_ps",
        "timing_closed",
        "utilization",
    ):
        assert key in report


# ---------------------------------------------------------------------------
# Closed-loop exploration
# ---------------------------------------------------------------------------

def _build_program(spec):
    from vse.compiler.compiler import compile_transformer
    from vse.models.transformer import (
        TransformerConfig,
        TransformerModel,
    )

    model = TransformerModel(
        TransformerConfig(
            hidden_dim=128,
            num_heads=4,
            intermediate_dim=256,
        ),
        num_layers=2,
    )

    return compile_transformer(
        model,
        sequence_length=16,
        config=spec.to_hardware_config(),
        options=spec.to_compile_options(),
    )


def test_run_design_loop_converges():
    base = ArchitectureSpec(
        num_pes=256,
        frequency_hz=5e9,
        pipeline_latency=0,
    )

    result = run_design_loop(_build_program, base)

    assert isinstance(result, DesignLoopResult)
    assert result.converged
    assert result.final_spec is not None
    assert result.final_result is not None
    assert len(result.iterations) <= 6


def test_run_design_loop_stops_early_when_closed():
    base = ArchitectureSpec(
        num_pes=256,
        frequency_hz=100e6,
    )

    result = run_design_loop(_build_program, base)

    assert result.converged
    assert len(result.iterations) == 1
    assert result.iterations[0].updated is False


def test_run_design_loop_bounded_by_max_iterations():
    # A clock too fast to ever close timing within 2 iterations.
    base = ArchitectureSpec(
        num_pes=256,
        frequency_hz=1e12,
        pipeline_latency=0,
    )

    result = run_design_loop(
        _build_program,
        base,
        max_iterations=2,
        max_pipeline=1,
    )

    assert len(result.iterations) == 2
    assert result.converged is False


def test_loop_iteration_report_shape():
    base = ArchitectureSpec(num_pes=64, frequency_hz=100e6)

    result = run_design_loop(_build_program, base)

    report = result.report()

    assert report["converged"] is True
    assert len(report["iterations"]) == 1

    step = report["iterations"][0]
    for key in (
        "step",
        "arch",
        "tokens_per_second",
        "rtl_lines",
        "physical",
        "updated",
    ):
        assert key in step


def test_format_design_loop_report_output():
    base = ArchitectureSpec(num_pes=64, frequency_hz=100e6)

    result = run_design_loop(_build_program, base)

    text = format_design_loop_report(result)

    assert "VSE ASIC EXPLORATION" in text
    assert "timing" in text.lower()
    assert "physically plausible" in text


def test_loop_iteration_rtl_lines_present():
    base = ArchitectureSpec(num_pes=64, frequency_hz=100e6)

    result = run_design_loop(_build_program, base)

    assert result.iterations[0].rtl_lines > 0


def test_asic_cli_subcommand_registered():
    from vse.cli import build_parser

    parser = build_parser()

    args = parser.parse_args(
        ["asic", "--model", "transformer", "--hidden-dim", "64",
         "--heads", "4", "--layers", "1", "--intermediate", "128",
         "--sequence", "8"]
    )

    assert args.command == "asic"
    assert args.hidden_dim == 64


def test_asic_cli_runs_and_returns_zero():
    from vse.cli_cmds.asic import run_asic_command

    class _Args:
        model = "transformer"
        hidden_dim = 64
        heads = 4
        layers = 1
        intermediate = 128
        sequence = 8
        mode = "decode"
        num_pes = 64
        macs_per_pe = 1
        freq = 100e6
        pipeline = 0
        sram_gb = 0.0
        node_nm = 7.0
        max_iters = 3
        rtl = False
        json = True

    assert run_asic_command(_Args()) == 0