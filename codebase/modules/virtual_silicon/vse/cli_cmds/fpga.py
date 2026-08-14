"""
VSE - Virtual Silicon Engine
vse/cli_cmds/fpga.py

`fpga` subcommand — validate a small FPGA prototype against the VSE
scheduler using the pure-Python RTL simulator.

Kept separate from vse/cli.py to stay within the 500-line file limit.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from vse.fpga.rtl import generate_rtl
from vse.fpga.validate import (
    format_fpga_report,
    validate_fpga,
)
from vse.workload import HardwareConfig


def add_fpga_subcommand(
    subparsers,
) -> argparse.ArgumentParser:
    fpga = subparsers.add_parser(
        "fpga",
        help=(
            "Validate an FPGA prototype (RTL sim) against the "
            "VSE scheduler."
        ),
    )

    fpga.add_argument(
        "--num-pes",
        type=int,
        default=4,
        help="PEs in the small prototype array.",
    )

    fpga.add_argument(
        "--macs-per-pe",
        type=int,
        default=1,
        help="MACs per PE per cycle.",
    )

    fpga.add_argument(
        "--pipeline",
        type=int,
        default=2,
        help="PE pipeline depth (cycles).",
    )

    fpga.add_argument(
        "--freq",
        type=float,
        default=100e6,
        help="Clock frequency in Hz.",
    )

    fpga.add_argument(
        "--weight-bits",
        type=int,
        default=None,
        help="Weight precision in bits (default 4).",
    )

    fpga.add_argument(
        "--activation-bits",
        type=int,
        default=None,
        help="Activation precision in bits (default 16).",
    )

    fpga.add_argument(
        "--frac-bits",
        type=int,
        default=8,
        help="Fixed-point fractional bits for activations.",
    )

    fpga.add_argument(
        "--macs",
        type=int,
        default=256,
        help="MACs in the validation workload.",
    )

    fpga.add_argument(
        "--banks",
        type=int,
        default=4,
        help="SRAM banks in the prototype.",
    )

    fpga.add_argument(
        "--noc-nodes",
        type=int,
        default=4,
        help="NoC router nodes in the prototype.",
    )

    fpga.add_argument(
        "--noc-topology",
        type=str,
        default="ring",
        choices=["ring", "mesh"],
        help="NoC topology.",
    )

    fpga.add_argument(
        "--rtl",
        action="store_true",
        help="Also print the generated SystemVerilog RTL.",
    )

    fpga.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )

    return fpga


def run_fpga_command(args) -> Optional[int]:
    config = HardwareConfig(
        num_pes=args.num_pes,
        macs_per_pe_per_cycle=args.macs_per_pe,
        pipeline_latency=args.pipeline,
        frequency_hz=args.freq,
        noc_topology=args.noc_topology,
        noc_nodes=args.noc_nodes,
    )

    result = validate_fpga(
        config,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        frac_bits=args.frac_bits,
        macs=args.macs,
        banks=args.banks,
    )

    if args.json:
        payload = result.report()

        if args.rtl:
            payload["rtl"] = generate_rtl(result.spec)

        print(json.dumps(payload, indent=2))
    else:
        print(format_fpga_report(result))

        if args.rtl:
            print()
            print(generate_rtl(result.spec))

    return 0


__all__ = [
    "add_fpga_subcommand",
    "run_fpga_command",
]