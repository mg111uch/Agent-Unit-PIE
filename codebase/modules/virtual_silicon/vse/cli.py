"""
VSE - Virtual Silicon Engine
vse/cli.py

Command-line interface for end-to-end VSE simulation.

    python -m vse.cli transformer --hidden-dim 4096 --heads 32 \
        --layers 32 --intermediate 11008 --sequence 4096

    python -m vse.cli moe --hidden-dim 4096 --intermediate 14336 \
        --experts 128 --top-k 2 --tokens 32

Common hardware options are shared across both commands; the `search`,
`fpga`, and `asic` subcommands live in vse/cli_cmds/. Use --json for
machine-readable output.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from vse.report.formatting import (
    format_report,
    format_trace,
)
from vse.models.moe import MoE, MoEConfig
from vse.models.transformer import (
    TransformerConfig,
    TransformerModel,
)
from vse.compiler.compiler import (
    CompileOptions,
    compile_moe,
    compile_transformer,
    execute,
)
from vse.cli_cmds.args import _add_common_hardware
from vse.cli_cmds.asic import (
    add_asic_subcommand,
    run_asic_command,
)
from vse.cli_cmds.fpga import (
    add_fpga_subcommand,
    run_fpga_command,
)
from vse.cli_cmds.search import (
    add_search_subcommand,
    run_search_command,
)
try:
    from vse.cli_cmds.codesign import (
        add_codesign_subcommand,
        run_codesign_command,
    )
except Exception:
    add_codesign_subcommand = None  # type: ignore
    run_codesign_command = None  # type: ignore
from vse.workload import (
    EndToEndResult,
    HardwareConfig,
    simulate_moe,
    simulate_transformer,
)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vse",
        description=(
            "VSE - Virtual Silicon Engine end-to-end simulation"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    _add_common_hardware(parser)

    transformer = subparsers.add_parser(
        "transformer",
        help="Simulate a decoder-only Transformer.",
    )

    transformer.add_argument(
        "--hidden-dim",
        type=int,
        required=True,
    )

    transformer.add_argument(
        "--heads",
        type=int,
        required=True,
    )

    transformer.add_argument(
        "--layers",
        type=int,
        required=True,
    )

    transformer.add_argument(
        "--intermediate",
        type=int,
        required=True,
    )

    transformer.add_argument(
        "--sequence",
        type=int,
        required=True,
    )

    transformer.add_argument(
        "--mode",
        choices=["decode", "prefill"],
        default="decode",
    )

    transformer.add_argument(
        "--no-gated",
        action="store_true",
        help="Disable the gated (swiglu) MLP.",
    )

    transformer.add_argument(
        "--target",
        type=float,
        default=None,
        help="Target tokens/sec feasibility check.",
    )

    _add_common_hardware(transformer)

    moe = subparsers.add_parser(
        "moe",
        help="Simulate one Mixture-of-Experts layer.",
    )

    moe.add_argument(
        "--hidden-dim",
        type=int,
        required=True,
    )

    moe.add_argument(
        "--intermediate",
        type=int,
        required=True,
    )

    moe.add_argument(
        "--experts",
        type=int,
        required=True,
    )

    moe.add_argument(
        "--top-k",
        type=int,
        required=True,
    )

    moe.add_argument(
        "--tokens",
        type=int,
        required=True,
    )

    moe.add_argument(
        "--no-gated",
        action="store_true",
        help="Disable the gated (swiglu) expert MLP.",
    )

    moe.add_argument(
        "--target",
        type=float,
        default=None,
        help="Target tokens/sec feasibility check.",
    )

    _add_common_hardware(moe)

    add_search_subcommand(subparsers)

    add_fpga_subcommand(subparsers)

    add_asic_subcommand(subparsers)

    if add_codesign_subcommand is not None:
        add_codesign_subcommand(subparsers)

    return parser


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def _maybe_gate_result(result, args) -> None:
    phys = getattr(args, "physics", "off") or "off"
    if phys == "off":
        return
    try:
        from vse.physics.gate import PhysicsGate  # lazy
        gate = PhysicsGate.check(result, _hardware_config(args))
        result.gate = gate
        result.gate_result = gate
    except Exception:
        pass


def run_transformer(args) -> Optional[int]:
    model = TransformerModel(
        TransformerConfig(
            hidden_dim=args.hidden_dim,
            num_heads=args.heads,
            intermediate_dim=args.intermediate,
            gated_mlp=not args.no_gated,
        ),
        num_layers=args.layers,
    )

    phys = getattr(args, "physics", "off") or "off"
    if args.compile:
        result = execute(
            compile_transformer(
                model,
                sequence_length=args.sequence,
                config=_hardware_config(args),
                options=_compile_options(args),
                mode=args.mode,
            ),
            target_tokens_per_second=args.target,
        )
        _maybe_gate_result(result, args)
    else:
        result = simulate_transformer(
            model,
            sequence_length=args.sequence,
            mode=args.mode,
            config=_hardware_config(args),
            target_tokens_per_second=args.target,
            physics=phys,
        )

    _emit(result, args)

    return 0


def run_moe(args) -> Optional[int]:
    moe = MoE(
        MoEConfig(
            hidden_dim=args.hidden_dim,
            intermediate_dim=args.intermediate,
            num_experts=args.experts,
            top_k=args.top_k,
            gated=not args.no_gated,
        )
    )

    phys = getattr(args, "physics", "off") or "off"
    if args.compile:
        result = execute(
            compile_moe(
                moe,
                tokens=args.tokens,
                config=_hardware_config(args),
                options=_compile_options(args),
            ),
            target_tokens_per_second=args.target,
        )
        _maybe_gate_result(result, args)
    else:
        result = simulate_moe(
            moe,
            tokens=args.tokens,
            config=_hardware_config(args),
            target_tokens_per_second=args.target,
            physics=phys,
        )

    _emit(result, args)

    return 0


def _hardware_config(args) -> HardwareConfig:
    # tile sram per-tile bytes conversion
    spt = getattr(args, "sram_per_tile_gb", None)
    spt_bytes = int(spt * 1024**3) if spt is not None else None
    # also support legacy alias sram_per_tile_bytes direct
    if spt_bytes is None:
        spt_bytes = getattr(args, "sram_per_tile_bytes", None)
    return HardwareConfig(
        num_pes=args.num_pes,
        macs_per_pe_per_cycle=args.macs_per_pe,
        memory_bytes_per_cycle=args.mem_bw,
        frequency_hz=args.freq,
        sram_bytes=int(args.sram_gb * 1024**3),
        pipeline_latency=args.pipeline,
        banks=args.banks,
        hbm_bytes_per_cycle=(args.hbm_bw if args.hbm_bw else None),
        sram_bytes_per_cycle=(args.sram_bw if args.sram_bw else None),
        dma_bytes_per_cycle=(args.dma_bw if args.dma_bw else None),
        weight_chunks=args.double_buffer,
        noc_topology=args.noc_topology,
        noc_nodes=args.noc_nodes,
        noc_link_bw=args.noc_bw,
        noc_per_hop_cycles=args.noc_hop_cycles,
        noc_broadcast=args.noc_broadcast,
        sram_model=getattr(args, "sram_model", "analytical"),
        sram_ports=getattr(args, "sram_ports", 1),
        sram_bits_per_access=getattr(args, "sram_bits_per_access", 32),
        num_tiles=getattr(args, "num_tiles", 1) or 1,
        sram_per_tile_bytes=spt_bytes,
        pes_per_tile=getattr(args, "pes_per_tile", None),
        tile_sram_banks=getattr(args, "tile_sram_banks", None),
        tile_sram_ports=getattr(args, "tile_sram_ports", None),
        tile_sram_bits=getattr(args, "tile_sram_bits", None),
        arch_family=getattr(args, "arch_family", "scalar"),
        vector_width=getattr(args, "vector_width", 1) or 1,
        systolic_dim=getattr(args, "systolic_dim", 0) or 0,
        simd_lanes=getattr(args, "simd_lanes", 1) or 1,
        dataflow=getattr(args, "dataflow", "weight_stationary"),
    )


def _compile_options(args) -> CompileOptions:
    # Parse precision-map if supplied (lazy import to avoid cycles).
    pm = getattr(args, "precision_map", None)
    if isinstance(pm, str):
        try:
            from vse.compiler.precision import parse_precision_map

            pm = parse_precision_map(pm)
        except Exception:
            pm = None
    # CompileOptions may or may not have precision_map field (B2/B3 compat).
    base_kwargs = dict(
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        kv_bits=args.kv_bits,
        fusion=not args.no_fusion,
        expert_placement=args.expert_placement,
        replicas=args.expert_replicas,
    )
    # If CompileOptions supports precision_map, include it.
    try:
        from vse.compiler.compiler import CompileOptions as _CO

        if "precision_map" in _CO.__dataclass_fields__:
            base_kwargs["precision_map"] = pm
        elif pm is not None:
            # Store via object attribute if field missing (best-effort)
            opts = _CO(**base_kwargs)
            object.__setattr__(opts, "precision_map", pm)
            # attach arch_family for CIM graph flag (lazy)
            if getattr(args, "arch_family", None):
                object.__setattr__(opts, "arch_family", getattr(args, "arch_family"))
            return opts
    except Exception:
        pass
    opts = CompileOptions(**base_kwargs)
    # attach arch_family for CIM graph flag if present (lazy, no field required)
    try:
        if getattr(args, "arch_family", None) is not None:
            object.__setattr__(opts, "arch_family", getattr(args, "arch_family"))
    except Exception:
        pass
    return opts


def _emit(
    result: EndToEndResult,
    args,
) -> None:
    if args.json:
        print(
            json.dumps(
                result.report(),
                indent=2,
            )
        )
    else:
        print(format_report(result))

        if args.trace:
            print()
            print(format_trace(result))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()

    args = parser.parse_args(argv)

    if args.command == "transformer":
        return run_transformer(args)

    if args.command == "moe":
        return run_moe(args)

    if args.command == "search":
        return run_search_command(args)

    if args.command == "fpga":
        return run_fpga_command(args)

    if args.command == "asic":
        return run_asic_command(args)

    if args.command == "codesign" and run_codesign_command is not None:
        return run_codesign_command(args)

    parser.error(
        f"unknown command: {args.command}"
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
