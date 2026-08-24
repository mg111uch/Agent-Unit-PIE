"""
VSE - Virtual Silicon Engine
vse/cli_cmds/args.py

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
        "--sram-model",
        type=str,
        default="analytical",
        choices=["analytical", "physical"],
        help="SRAM bandwidth model",
    )

    parser.add_argument(
        "--sram-ports",
        type=int,
        default=1,
        help="SRAM ports per bank (1..4, physical model).",
    )

    parser.add_argument(
        "--sram-bits-per-access",
        type=int,
        default=32,
        help="SRAM bits per access (8..512, physical model).",
    )

    # Distributed tiles (idempotent)
    _existing = {a.dest for a in parser._actions}
    if "num_tiles" not in _existing:
        parser.add_argument(
            "--num-tiles",
            type=int,
            default=1,
            help="Distributed tiles (1=single, 1..64).",
        )
    if "tile_sram_banks" not in _existing:
        parser.add_argument(
            "--tile-banks",
            dest="tile_sram_banks",
            type=int,
            default=None,
            help="Banks per tile (None inherits --banks).",
        )
    if "tile_sram_ports" not in _existing:
        parser.add_argument(
            "--tile-sram-ports",
            dest="tile_sram_ports",
            type=int,
            default=None,
            help="Ports per tile (1..4).",
        )
        # alias --tile-ports
        try:
            parser.add_argument(
                "--tile-ports",
                dest="tile_sram_ports",
                type=int,
                default=None,
                help="Alias for --tile-sram-ports.",
            )
        except Exception:
            pass
    if "tile_sram_bits" not in _existing:
        parser.add_argument(
            "--tile-sram-bits",
            dest="tile_sram_bits",
            type=int,
            default=None,
            help="Bits per tile SRAM access (8..512).",
        )
        try:
            parser.add_argument(
                "--tile-bits",
                dest="tile_sram_bits",
                type=int,
                default=None,
                help="Alias for --tile-sram-bits.",
            )
        except Exception:
            pass
    if "sram_per_tile_gb" not in _existing:
        # store GB as float, convert later; dest holds GB float
        parser.add_argument(
            "--sram-per-tile-gb",
            dest="sram_per_tile_gb",
            type=float,
            default=None,
            help="SRAM per tile in GiB.",
        )
    if "pes_per_tile" not in _existing:
        parser.add_argument(
            "--pes-per-tile",
            type=int,
            default=None,
            help="PEs per tile (None=even split).",
        )

    # Arch family / dataflow (idempotent)
    _arch_existing = {a.dest for a in parser._actions}
    if "arch_family" not in _arch_existing:
        parser.add_argument(
            "--arch-family",
            dest="arch_family",
            type=str,
            default="scalar",
            choices=["scalar", "simd", "vector", "systolic", "weight_stationary", "output_stationary", "cim", "near_memory"],
            help="PE architecture family.",
        )
    if "vector_width" not in _arch_existing:
        parser.add_argument(
            "--vector-width",
            type=int,
            default=1,
            help="Vector width (1..16).",
        )
    if "systolic_dim" not in _arch_existing:
        parser.add_argument(
            "--systolic-dim",
            type=int,
            default=0,
            help="Systolic array dimension (0..64).",
        )
    if "simd_lanes" not in _arch_existing:
        parser.add_argument(
            "--simd-lanes",
            type=int,
            default=1,
            help="SIMD lanes (1..8).",
        )
    if "dataflow" not in _arch_existing:
        parser.add_argument(
            "--dataflow",
            type=str,
            default="weight_stationary",
            choices=["weight_stationary", "output_stationary"],
            help="Dataflow for systolic/PE array.",
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

    # physics gate (idempotent)
    _phys_existing = {a.dest for a in parser._actions}
    if "physics" not in _phys_existing:
        parser.add_argument(
            "--physics",
            choices=["off", "warn", "fail"],
            default="off",
            help="Physics gate mode: off/warn/fail (default off).",
        )

    _add_precision_args(parser)


def _add_precision_args(parser: argparse.ArgumentParser) -> None:
    """Idempotent precision-map args (coexists with B2)."""
    existing = {a.dest for a in parser._actions}
    if "precision_map" not in existing:
        parser.add_argument(
            "--precision-map",
            type=str,
            default=None,
            help='Per-tensor precision map JSON, e.g. \'{"attn":2,"mlp":4}\'',
        )
    if "q2_group_size" not in existing:
        parser.add_argument(
            "--q2-group-size",
            type=int,
            default=32,
            help="Q2 group size (weights per scale).",
        )
    if "q2_scale_bits" not in existing:
        parser.add_argument(
            "--q2-scale-bits",
            type=int,
            default=8,
            help="Bits per Q2 scale.",
        )
