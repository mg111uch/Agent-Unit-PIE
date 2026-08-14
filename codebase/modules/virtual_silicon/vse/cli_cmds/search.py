"""
VSE - Virtual Silicon Engine
vse/cli_cmds/search.py

`search` subcommand — explore a design space of candidate chips
for a fixed model, rank by tokens/sec, and report the Pareto frontier.

Kept separate from `vse/cli.py` to stay within the 500-line file limit.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from vse.search.architecture import ArchitectureSpec, SearchSpace
from vse.compiler.compiler import (
    compile_moe,
    compile_transformer,
)
from vse.report.formatting import format_search
from vse.models.moe import MoE, MoEConfig
from vse.search.search import (
    pareto_frontier,
    run_random_search,
    run_search,
)
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)


def add_search_subcommand(
    subparsers,
) -> argparse.ArgumentParser:
    search = subparsers.add_parser(
        "search",
        help="Search hardware architectures for a fixed model.",
    )

    search.add_argument(
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
        search.add_argument(
            f"--{name}",
            type=int,
            default=None,
        )

    search.add_argument(
        "--mode",
        choices=["decode", "prefill"],
        default="decode",
    )

    search.add_argument(
        "--no-gated",
        action="store_true",
        help="Disable the gated (swiglu) MLP.",
    )

    search.add_argument(
        "--dim",
        action="append",
        default=[],
        metavar="NAME=V1,V2,...",
        help=(
            "Search dimension (repeatable), e.g. "
            "--dim num_pes=1024,2048,4096 --dim sram_gb=0,1"
        ),
    )

    search.add_argument(
        "--sample",
        type=int,
        default=0,
        help=(
            "If > 0, sample this many random candidates "
            "instead of the full grid."
        ),
    )

    search.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for --sample random sampling.",
    )

    search.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of best candidates to show.",
    )

    search.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )

    _add_search_hardware(search)

    return search


def _add_search_hardware(
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
        "--freq",
        type=float,
        default=1e9,
        help="Clock frequency in Hz.",
    )

    parser.add_argument(
        "--sram-gb",
        type=float,
        default=0.0,
        help="On-chip SRAM capacity in GiB.",
    )

    parser.add_argument(
        "--hbm-bw",
        type=int,
        default=256,
        help="HBM bandwidth bytes/cycle.",
    )

    parser.add_argument(
        "--sram-bw",
        type=int,
        default=256,
        help="SRAM bandwidth bytes/cycle.",
    )

    parser.add_argument(
        "--banks",
        type=int,
        default=1,
        help="Independent banks per memory level.",
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
        "--pipeline",
        type=int,
        default=0,
        help="Compute pipeline latency in cycles.",
    )

    parser.add_argument(
        "--double-buffer",
        type=int,
        default=4,
        help="Weight streaming double-buffer depth.",
    )

    parser.add_argument(
        "--noc-topology",
        type=str,
        default="ring",
        choices=["ring", "mesh"],
        help="NoC topology (used when --noc-nodes > 1).",
    )

    parser.add_argument(
        "--expert-replicas",
        type=int,
        default=1,
        help="Replicate each expert across this many NoC nodes.",
    )

    parser.add_argument(
        "--expert-placement",
        type=str,
        default="round_robin",
        choices=["round_robin", "contiguous"],
        help="Expert → NoC node placement strategy.",
    )

    parser.add_argument(
        "--node-nm",
        type=float,
        default=None,
        help="Process node in nm (scales area/power; default ~7 nm).",
    )

    for name in (
        "weight-bits",
        "activation-bits",
        "kv-bits",
    ):
        parser.add_argument(
            f"--{name}",
            type=int,
            default=None,
            help="Compiled precision in bits.",
        )

    parser.add_argument(
        "--no-fusion",
        action="store_true",
        help="Disable activation fusion when compiling.",
    )


def run_search_command(args) -> Optional[int]:
    if args.model == "transformer":
        missing = [
            name
            for name in (
                "hidden_dim",
                "heads",
                "layers",
                "intermediate",
                "sequence",
            )
            if getattr(args, name) is None
        ]
    else:
        missing = [
            name
            for name in (
                "hidden_dim",
                "intermediate",
                "experts",
                "top_k",
                "tokens",
            )
            if getattr(args, name) is None
        ]

    if missing:
        raise SystemExit(
            "vse: error: search --model "
            f"{args.model} requires: "
            + ", ".join(
                f"--{name.replace('_', '-')}"
                for name in missing
            )
        )

    base = _search_base_spec(args)

    space = SearchSpace(
        {
            name: raw.split(",")
            for name, raw in (
                entry.split("=", 1)
                for entry in args.dim
            )
        }
    )

    if args.model == "transformer":
        build_program = _build_transformer_program(args)
    else:
        build_program = _build_moe_program(args)

    if args.sample > 0:
        results = run_random_search(
            space,
            build_program,
            args.sample,
            base=base,
            seed=args.seed,
        )
    else:
        results = run_search(space, build_program, base=base)

    frontier = pareto_frontier(results)

    if args.json:
        print(
            json.dumps(
                {
                    "model": args.model,
                    "candidates": [
                        item.report()
                        for item in results
                    ],
                    "frontier": [
                        item.report()
                        for item in frontier
                    ],
                },
                indent=2,
            )
        )
    else:
        print(
            format_search(
                results,
                space=space,
                frontier=frontier,
                top_n=args.top_n,
            )
        )

    return 0


def _search_base_spec(args) -> ArchitectureSpec:
    return ArchitectureSpec(
        num_pes=args.num_pes,
        macs_per_pe=args.macs_per_pe,
        frequency_hz=args.freq,
        pipeline_latency=args.pipeline,
        sram_bytes=int(args.sram_gb * 1024**3),
        hbm_bytes_per_cycle=args.hbm_bw,
        sram_bytes_per_cycle=args.sram_bw,
        banks=args.banks,
        weight_chunks=args.double_buffer,
        noc_topology=args.noc_topology,
        noc_nodes=args.noc_nodes,
        noc_link_bw=args.noc_bw,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        kv_bits=args.kv_bits,
        fusion=not args.no_fusion,
        expert_replicas=args.expert_replicas,
        expert_placement=args.expert_placement,
        node_nm=args.node_nm,
    )


def _build_transformer_program(args):
    def build(spec: ArchitectureSpec):
        model = TransformerModel(
            TransformerConfig(
                hidden_dim=args.hidden_dim,
                num_heads=args.heads,
                intermediate_dim=args.intermediate,
                gated_mlp=not args.no_gated,
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


def _build_moe_program(args):
    def build(spec: ArchitectureSpec):
        moe = MoE(
            MoEConfig(
                hidden_dim=args.hidden_dim,
                intermediate_dim=args.intermediate,
                num_experts=args.experts,
                top_k=args.top_k,
                gated=not args.no_gated,
            )
        )

        return compile_moe(
            moe,
            tokens=(
                spec.batch_tokens
                or args.tokens
            ),
            config=spec.to_hardware_config(),
            options=spec.to_compile_options(),
        )

    return build


__all__ = [
    "add_search_subcommand",
    "run_search_command",
]
