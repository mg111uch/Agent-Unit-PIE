"""
vse/cli_cmds/codesign.py - model ↔ hardware co-search CLI.

    python -m vse.cli codesign --model-dim layers=12,16 --dim num_pes=1024,2048 --sample 20
"""
from __future__ import annotations

import argparse
import json
from typing import Optional

from vse.search.architecture import ArchitectureSpec, SearchSpace
from vse.search.model_space import ModelArchSpec, ModelSearchSpace
from vse.search.co_search import pareto_frontier_models, run_co_search, run_random_co_search
from vse.compiler.compiler import compile_transformer
from vse.models.transformer import TransformerConfig, TransformerModel


def add_codesign_subcommand(subparsers) -> argparse.ArgumentParser:
    p = subparsers.add_parser("codesign", help="Model↔hardware co-search (Pareto).")
    p.add_argument("--model-dim", action="append", default=[], metavar="NAME=V1,V2",
                   help="Model dimension e.g. --model-dim layers=12,16 --model-dim hidden_dim=1024,2048")
    p.add_argument("--dim", action="append", default=[], metavar="NAME=V1,V2",
                   help="Hardware dimension e.g. --dim num_pes=1024,2048")
    p.add_argument("--sample", type=int, default=0, help="Random sample count (0=full grid)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--sequence", type=int, default=128)
    p.add_argument("--top-n", type=int, default=5)
    p.add_argument("--maximize", action="append", default=[], help="Maximize attrs (repeatable)")
    p.add_argument("--minimize", action="append", default=[], help="Minimize attrs (repeatable)")
    p.add_argument("--json", action="store_true")
    # base hardware
    p.add_argument("--num-pes", type=int, default=4096)
    p.add_argument("--freq", type=float, default=1e9)
    # base model
    p.add_argument("--layers", type=int, default=16)
    p.add_argument("--hidden-dim", type=int, default=1024)
    p.add_argument("--heads", type=int, default=16)
    p.add_argument("--intermediate", type=int, default=2816)
    p.add_argument("--physics", choices=["off", "warn", "fail"], default="off",
                   help="Physics gate mode: off/warn/fail (default off).")
    return p


def _parse_dims(entries):
    d = {}
    for e in entries:
        if "=" not in e:
            raise SystemExit(f"bad dim '{e}' expected NAME=V1,V2")
        k, v = e.split("=", 1)
        d[k] = v.split(",")
    return d


def run_codesign_command(args) -> Optional[int]:
    model_space = ModelSearchSpace(_parse_dims(args.model_dim))
    hw_space = SearchSpace(_parse_dims(args.dim))
    base_model = ModelArchSpec(layers=args.layers, hidden_dim=args.hidden_dim, num_heads=args.heads, intermediate_dim=args.intermediate)
    base_arch = ArchitectureSpec(num_pes=args.num_pes, frequency_hz=args.freq)

    def build_fn(m_spec: ModelArchSpec, a_spec: ArchitectureSpec):
        model = m_spec.to_transformer_model()
        return compile_transformer(model, sequence_length=args.sequence, config=a_spec.to_hardware_config(), options=a_spec.to_compile_options())

    if args.sample > 0:
        results = run_random_co_search(model_space, hw_space, build_fn, n=args.sample, base_model=base_model, base_arch=base_arch, seed=args.seed)
    else:
        results = run_co_search(model_space, hw_space, build_fn, base_model=base_model, base_arch=base_arch)

    # physics gate attach/filter
    physics = getattr(args, "physics", "off") or "off"
    if physics != "off":
        try:
            from vse.physics.gate import PhysicsGate  # lazy
            filtered = []
            for r in results:
                try:
                    gate = PhysicsGate.check(r.result, r.arch_spec)
                    r.result.gate = gate  # type: ignore
                    r.result.gate_result = gate  # type: ignore
                    plausible = bool(getattr(gate, "plausible", True))
                except Exception:
                    plausible = True
                if physics == "fail" and not plausible:
                    continue
                filtered.append(r)
            if physics == "fail":
                results = filtered
        except Exception:
            pass

    maximize = args.maximize if args.maximize else ["tokens_per_second", "accuracy_score"]
    minimize = args.minimize if args.minimize else ["area_mm2"]
    frontier = pareto_frontier_models(results, maximize=maximize, minimize=minimize)

    if args.json:
        print(json.dumps({"candidates": [r.report() for r in results], "frontier": [r.report() for r in frontier], "physics": physics}, indent=2))
    else:
        print(f"candidates: {len(results)} frontier: {len(frontier)}")
        for r in frontier[: args.top_n]:
            print(f"  {r.label()} tok/s={r.tokens_per_second:.1f} acc={r.accuracy_score:.3f} area={r.area_mm2:.2f}mm2")
        if not frontier:
            for r in sorted(results, key=lambda x: x.tokens_per_second, reverse=True)[: args.top_n]:
                print(f"  {r.label()} tok/s={r.tokens_per_second:.1f}")
    return 0


__all__ = ["add_codesign_subcommand", "run_codesign_command"]
