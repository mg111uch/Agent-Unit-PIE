"""
VSE - Virtual Silicon Engine
vse/cli_args.py

Shared command-line hardware-argument declarations used by the main
CLI entry points. Kept separate from cli.py to stay under the file
line budget.
"""

from __future__ import annotations

import argparse


def _add_common_hardware(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--num-pes",
        type=int,
        default=4096,
    )

    parser.add_argument(
        "--macs-per-pe",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--mem-bw",
        type=int,
        default=256,
        help="Memory bandwidth in bytes per cycle.",
    )

    parser.add_argument(
        "--freq",
        type=float,
        default=1e9,
        help="Clock frequency in Hz.",
    )

    parser.add_argument(
        "--pipeline",
        type=int,
        default=0,
        help="Compute pipeline latency in cycles.",
    )

    parser.add_argument(
        "--sram-gb",
        type=float,
        default=0.0,
        help="On-chip SRAM capacity in GiB.",
    )

    parser.add_argument(
        "--banks",
        type=int,
        default=1,
        help="Independent banks per memory level.",
    )

    parser.add_argument(
        "--hbm-bw",
        type=int,
        default=0,
        help="HBM bandwidth bytes/cycle (0 = --mem-bw).",
    )

    parser.add_argument(
        "--sram-bw",
        type=int,
        default=0,
        help="SRAM bandwidth bytes/cycle (0 = --mem-bw).",
    )

    parser.add_argument(
        "--dma-bw",
        type=int,
        default=0,
        help="DMA transfer bandwidth bytes/cycle (0 = --mem-bw).",
    )

    parser.add_argument(
        "--double-buffer",
        type=int,
        default=4,
        help="Weight streaming double-buffer depth (1 disables).",
    )

    parser.add_argument(
        "--noc-topology",
        type=str,
        default="ring",
        choices=["ring", "mesh"],
        help="NoC topology (used when --noc-nodes > 1).",
    )

    parser.add_argument(
        "--noc-nodes",
        type=int,
        default=1,
        help="NoC router nodes (1 disables cross-node traffic).",
    )

    parser.add_argument(
        "--noc-bw",
        type=int,
        default=256,
        help="NoC link bandwidth in bytes per cycle.",
    )

    parser.add_argument(
        "--noc-hop-cycles",
        type=int,
        default=4,
        help="NoC pipeline latency per hop.",
    )

    parser.add_argument(
        "--noc-broadcast",
        action="store_true",
        help="Broadcast tokens to all NoC nodes instead of per-expert sends.",
    )

    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile the model into a fixed graph (Phase 5).",
    )

    parser.add_argument(
        "--weight-bits",
        type=int,
        default=None,
        help="Compiled weight precision in bits.",
    )

    parser.add_argument(
        "--activation-bits",
        type=int,
        default=None,
        help="Compiled activation precision in bits.",
    )

    parser.add_argument(
        "--kv-bits",
        type=int,
        default=None,
        help="Compiled KV-cache precision in bits.",
    )

    parser.add_argument(
        "--no-fusion",
        action="store_true",
        help="Disable activation fusion when compiling.",
    )

    parser.add_argument(
        "--expert-placement",
        type=str,
        default="round_robin",
        choices=["round_robin", "contiguous"],
        help="Expert → NoC node placement strategy.",
    )

    parser.add_argument(
        "--expert-replicas",
        type=int,
        default=1,
        help="Replicate each expert across this many NoC nodes.",
    )

    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print the per-cycle activity trace.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
