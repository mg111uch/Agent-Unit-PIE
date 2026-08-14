"""
VSE - Virtual Silicon Engine
vse/cli_cmds/asic.py

`asic` subcommand — generate the full RTL and run the closed-loop
physical exploration (simulate → RTL → physical → update).

Kept separate from vse/cli.py to stay within the 500-line file limit.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from vse.asic.loop import (
    format_design_loop_report,
    run_design_loop,
)
from vse.fpga.spec import FPGASpec
from vse.rtl import generate_rtl
from vse.search.architecture import ArchitectureSpec
from vse.compiler.compiler import (
    compile_moe,
    compile_transformer,
)
from vse.models.moe import MoE, MoEConfig
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)


def add_asic_subcommand(
    subparsers,
) -> argparse.ArgumentParser:
    asic = subparsers.add_parser(
        "asic",
        help=(
            "Generate RTL and run closed-loop physical exploration "
            "(Phase 9/10)."
        ),
    )

    asic.add_argument(
        "--model",
        choices=["transformer", "moe"],
        required=True,
    )

    for name in (
        "hidden-dim",
        "heads",
        "layers",
        "intermediate",
        "sequence",
        "experts",
        "top-k",
        "tokens",
    ):
        asic.add_argument(
            f"--{name}",
            type=int,
            default=None,
        )

    asic.add_argument(
        "--mode",
        choices=["decode", "prefill"],
        default="decode",
    )

    asic.add_argument(
        "--num-pes",
        type=int,
        default=256,
    )

    asic.add_argument(
        "--macs-per-pe",
        type=int,
        default=1,
    )

    asic.add_argument(
        "--freq",
        type=float,
        default=5e9,
        help="Requested clock (Hz) — the loop must close timing at it.",
    )

    asic.add_argument(
        "--pipeline",
        type=int,
        default=0,
        help="Initial pipeline latency (the loop may deepen it).",
    )

    asic.add_argument(
        "--sram-gb",
        type=float,
        default=0.0,
        help="On-chip SRAM capacity in GiB.",
    )

    asic.add_argument(
        "--node-nm",
        type=float,
        default=7.0,
        help="Process node in nm (scales timing/area).",
    )

    asic.add_argument(
        "--max-iters",
        type=int,
        default=6,
        help="Max closed-loop iterations.",
    )

    asic.add_argument(
        "--rtl",
        action="store_true",
        help="Also print the generated SystemVerilog RTL.",
    )

    asic.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )

    return asic


def run_asic_command(args) -> Optional[int]:
    base = ArchitectureSpec(
        num_pes=args.num_pes,
        macs_per_pe=args.macs_per_pe,
        frequency_hz=args.freq,
        pipeline_latency=args.pipeline,
        sram_bytes=int(args.sram_gb * 1024**3),
        node_nm=args.node_nm,
    )

    if args.model == "transformer":
        build = _build_transformer(args)
    else:
        build = _build_moe(args)

    result = run_design_loop(
        build,
        base,
        max_iterations=args.max_iters,
    )

    if args.json:
        payload = result.report()

        if args.rtl:
            final = result.final_spec
            fpgaspec = FPGASpec.from_hardware(
                final.to_hardware_config(),
                weight_bits=final.weight_bits,
                activation_bits=final.activation_bits,
            )
            payload["rtl"] = generate_rtl(fpgaspec)

        print(json.dumps(payload, indent=2))
    else:
        print(format_design_loop_report(result))

        if args.rtl:
            final = result.final_spec
            fpgaspec = FPGASpec.from_hardware(
                final.to_hardware_config(),
                weight_bits=final.weight_bits,
                activation_bits=final.activation_bits,
            )
            print()
            print(generate_rtl(fpgaspec))

    return 0


def _build_transformer(args):
    def build(spec: ArchitectureSpec):
        model = TransformerModel(
            TransformerConfig(
                hidden_dim=args.hidden_dim,
                num_heads=args.heads,
                intermediate_dim=args.intermediate,
            ),
            num_layers=args.layers,
        )

        return compile_transformer(
            model,
            sequence_length=args.sequence,
            config=spec.to_hardware_config(),
            options=spec.to_compile_options(),
            mode=args.mode,
        )

    return build


def _build_moe(args):
    def build(spec: ArchitectureSpec):
        moe = MoE(
            MoEConfig(
                hidden_dim=args.hidden_dim,
                intermediate_dim=args.intermediate,
                num_experts=args.experts,
                top_k=args.top_k,
            )
        )

        return compile_moe(
            moe,
            tokens=args.tokens,
            config=spec.to_hardware_config(),
            options=spec.to_compile_options(),
        )

    return build


__all__ = [
    "add_asic_subcommand",
    "run_asic_command",
]