"""
Phase 9 tests: full RTL generator (vse/rtl.py).
"""

import pytest

from vse.fpga.spec import FPGASpec
from vse.rtl import (
    generate_accumulator,
    generate_activation,
    generate_dma,
    generate_expert_dispatch,
    generate_noc_router,
    generate_pe,
    generate_pe_array,
    generate_rtl,
    generate_sram_ctrl,
    generate_top,
)


ALL_MODULES = [
    "vse_pe",
    "vse_pe_array",
    "vse_sram_ctrl",
    "vse_noc_router",
    "vse_dma",
    "vse_expert_dispatch",
    "vse_accumulator",
    "vse_activation",
    "vse_asic_top",
]


def test_generate_rtl_contains_all_modules():
    sv = generate_rtl(FPGASpec())

    for module in ALL_MODULES:
        assert f"module {module}" in sv


def test_generate_rtl_is_plain_systemverilog():
    sv = generate_rtl(FPGASpec())

    assert "`timescale" in sv
    assert "module vse_asic_top" in sv
    assert "endmodule" in sv


def test_generate_pe_has_pipelined_accumulator():
    sv = generate_pe()

    assert "acc <= acc + $signed(a_in) * $signed(w_in);" in sv
    assert "FRAC_BITS" in sv


def test_generate_pe_array_instantiates_generate_loop():
    sv = generate_pe_array()

    assert "genvar g" in sv
    assert "for (g = 0; g < NUM_PES; g++)" in sv
    assert "vse_pe #(" in sv


def test_generate_sram_ctrl_banked_memory():
    sv = generate_sram_ctrl()

    assert "mem [NUM_BANKS][WORDS]" in sv
    assert "NUM_BANKS" in sv


def test_generate_noc_router_hop_latency():
    sv = generate_noc_router()

    assert "HOP_CYCLES" in sv
    assert "count <= HOP_CYCLES * hops;" in sv


def test_generate_dma_double_buffering():
    sv = generate_dma()

    assert "CHUNK_WORDS" in sv
    assert "MAX_CHUNKS" in sv
    assert "chunk_pos" in sv


def test_generate_expert_dispatch_topk():
    sv = generate_expert_dispatch()

    assert "TOP_K" in sv
    assert "topk[k_idx]" in sv


def test_generate_accumulator_combines_partials():
    sv = generate_accumulator()

    assert "partial [PORTS]" in sv
    assert "acc <= acc + partial[p];" in sv


def test_generate_activation_quantizes():
    sv = generate_activation()

    assert "FRAC_BITS" in sv
    assert "OUT_WIDTH" in sv


def test_generate_top_uses_spec_parameters():
    spec = FPGASpec(num_pes=8, sram_banks=4, noc_nodes=4)

    sv = generate_top(spec)

    assert "NUM_PES     = 8" in sv
    assert "NUM_BANKS   = 4" in sv
    assert "NUM_NODES   = 4" in sv
    assert "vse_pe_array" in sv
    assert "vse_sram_ctrl" in sv
    assert "vse_noc_router" in sv
    assert "vse_dma" in sv
    assert "vse_expert_dispatch" in sv
    assert "vse_accumulator" in sv
    assert "vse_activation" in sv


def test_generate_rtl_reflects_spec_widths():
    spec = FPGASpec(
        num_pes=16,
        weight_bits=8,
        activation_bits=12,
        frac_bits=6,
        pipeline_depth=4,
    )

    sv = generate_rtl(spec)

    assert "NUM_PES     = 16" in sv
    assert "DW          = 8" in sv
    assert "AW          = 12" in sv
    assert "FRAC_BITS   = 6" in sv
    assert "PIPE_DEPTH  = 4" in sv


def test_generate_rtl_parameterized_modules_stable():
    sv1 = generate_rtl(FPGASpec(num_pes=4))
    sv2 = generate_rtl(FPGASpec(num_pes=4))

    assert sv1 == sv2