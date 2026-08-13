"""
VSE - Virtual Silicon Engine
vse/formatting.py

Text formatting for CLI reports.
"""

from __future__ import annotations

from vse.core.memory_hierarchy import format_memory_report
from vse.report.result import EndToEndResult


def _utilization_percent(value: float) -> str:
    return f"{value * 100:6.2f}%"


def _compact_number(value: float) -> str:
    if value >= 1e6:
        return f"{value / 1e6:.3f}M"
    if value >= 1e3:
        return f"{value / 1e3:.3f}K"
    return f"{value:.3f}"


def format_report(result: EndToEndResult) -> str:
    """
    Produce a compact textual report.
    """

    benchmark = result.benchmark.report()

    lines = [
        "VSE END-TO-END SIMULATION",
        "=" * 60,
        f"Model            : {result.name}",
        f"Tokens           : {result.tokens:,}",
        f"Sequence length  : {result.sequence_length:,}",
        "",
        "EXECUTION",
        "-" * 60,
        f"Total cycles     : {result.total_cycles:,}",
        f"Latency          : {result.latency_us:,.3f} us",
        f"Throughput       : {_compact_number(result.tokens_per_second)} tok/s",
        "",
        "WORKLOAD",
        "-" * 60,
        f"Total MACs       : {_compact_number(result.total_macs)}",
        f"Memory bytes     : {_compact_number(result.total_memory_bytes)}",
        f"Arithmetic inten : {benchmark['total_macs'] / benchmark['memory_bytes']:.3f} MAC/B"
        if benchmark["memory_bytes"]
        else "Arithmetic inten : n/a",
        "",
        "UTILIZATION",
        "-" * 60,
        f"Compute          : {_utilization_percent(result.compute_utilization)}",
        f"Memory           : {_utilization_percent(result.memory_utilization)}",
    ]

    if result.memory_traffic:
        lines.append("")
        lines.append(
            format_memory_report(
                result.memory_traffic
            )
        )

    if result.noc.get("transfers", 0) > 0:
        lines.extend(
            [
                "",
                "NETWORK (NoC)",
                "-" * 60,
                f"Transfers       : {result.noc['transfers']:,}",
                f"Bytes           : {_compact_number(result.noc['bytes'])}",
                f"Hops            : {result.noc['hops']:,}",
                f"Latency        : {result.noc['latency_cycles']:,} cyc",
            ]
        )

        if result.noc.get("broadcasts", 0) > 0:
            lines.append(
                f"Broadcasts      : "
                f"{result.noc['broadcasts']:,}"
            )

        congestion = result.noc.get("congestion", {})
        if congestion:
            lines.append(
                f"Congestion      : "
                f"{_utilization_percent(congestion.get('utilization', 0))} "
                f"link util, "
                f"{congestion.get('peak_concurrency', 0)} "
                f"peak transfers"
            )

        deadlock = result.noc.get("deadlock", {})
        if deadlock:
            lines.append(
                "Deadlock        : "
                f"{'none (acyclic)' if deadlock.get('acyclic') else 'CYCLE DETECTED'}"
            )

    if result.plan:
        plan = result.plan

        lines.extend(["", "COMPILE PLAN (model-specific)", "-" * 60])

        precision = plan.get("precision", {})
        lines.append(
            "Precision       : "
            f"w{precision.get('weight_bits', '?')}b "
            f"a{precision.get('activation_bits', '?')}b"
            + (
                f" kv{precision['kv_bits']}b"
                if "kv_bits" in precision
                else ""
            )
        )

        pe = plan.get("pe_allocation", {})
        lines.append(
            f"PE allocation   : "
            f"{pe.get('total_pes', '?'):,} PEs total, "
            f"{pe.get('expert_pes', 0):,} per expert"
        )

        mem = plan.get("memory_placement", {})
        lines.append(
            f"Memory plan     : "
            f"weights {mem.get('weights', '?')}, "
            f"KV {mem.get('kv', 'n/a')}"
        )

        placement = plan.get("expert_placement", {})
        if placement.get("nodes", 1) > 1:
            lines.append(
                f"Expert placement: "
                f"{placement.get('strategy', '?')} "
                f"across {placement.get('nodes')} nodes "
                f"({placement.get('topology')}), "
                f"{plan.get('routing', {}).get('transfers', 0)} "
                f"transfers, "
                f"{plan.get('routing', {}).get('hops', 0)} hops"
            )

        pipeline = plan.get("pipeline", {})
        lines.append(
            f"Pipeline        : "
            f"{pipeline.get('stages', 1)} stage(s), "
            f"{pipeline.get('layers', 'n/a')} layers, "
            f"double-buffer "
            f"{pipeline.get('double_buffer_depth', 'n/a')}"
        )

        fusion = plan.get("fusion", {})
        lines.append(
            f"Fusion          : "
            f"{'on' if fusion.get('enabled') else 'off'} "
            f"(saved "
            f"{fusion.get('saved_sram_round_trips', 0)} "
            f"SRAM round-trips)"
        )

    if (
        benchmark["target_tokens_per_second"]
        is not None
    ):
        lines.extend(
            [
                "",
                "TARGET ANALYSIS",
                "-" * 60,
                f"Target           : "
                f"{benchmark['target_tokens_per_second']:,.0f} tok/s",
                f"Reached          : "
                f"{'yes' if benchmark['target_reached'] else 'no'}",
            ]
        )

    if result.power:
        power = result.power
        lines.extend(
            [
                "",
                "ENERGY & POWER (est.)",
                "-" * 60,
                f"Energy          : "
                f"{power['total_energy_uj'] / 1e3:.3f} mJ",
                f"  compute       : "
                f"{_compact_number(power['compute_energy_uj'])} µJ",
                f"  memory        : "
                f"{_compact_number(power['memory_energy_uj'])} µJ",
                f"  NoC           : "
                f"{_compact_number(power['noc_energy_uj'])} µJ",
                f"Energy/token    : "
                f"{power['energy_per_token_uj']:.3f} µJ",
                f"Power           : "
                f"{power['average_power_watts']:.3f} W",
                f"  static        : "
                f"{power['static_power_watts']:.3f} W",
                f"Tokens/Watt     : "
                f"{_compact_number(power['tokens_per_watt'])}",
            ]
        )

        thermal = power.get("thermal_density_w_per_mm2")
        if thermal is not None and thermal > 0:
            feasible = power.get("thermally_feasible")
            lines.extend(
                [
                    f"Thermal density : "
                    f"{thermal:.3f} W/mm²",
                    f"Thermally fit   : "
                    f"{'yes' if feasible else 'NO (limit exceeded)'}",
                ]
            )

    if result.area:
        area = result.area
        lines.extend(
            [
                "",
                "AREA (est.)",
                "-" * 60,
                f"Compute         : "
                f"{area['compute_area_mm2']:.2f} mm²",
                f"SRAM            : "
                f"{area['sram_area_mm2']:.2f} mm²",
                f"NoC             : "
                f"{area['noc_area_mm2']:.2f} mm²",
                f"Total           : "
                f"{area['total_area_mm2']:.2f} mm²",
            ]
        )

    return "\n".join(lines)


def format_search(
    results: list,
    space: "object",
    frontier: list = None,
    top_n: int = 5,
) -> str:
    """
    Compact report of an architecture search: the best candidates and
    the Pareto frontier (tokens/sec vs die area).
    """

    if frontier is None:
        frontier = []

    frontier_ids = {
        id(item) for item in frontier
    }

    ranked = sorted(
        results,
        key=lambda item: item.tokens_per_second,
        reverse=True,
    )

    dims = ", ".join(
        f"{name}={','.join(map(str, values))}"
        for name, values in space.dims.items()
    )

    lines = [
        "VSE ARCHITECTURE SEARCH",
        "=" * 60,
        f"Candidates        : {len(results):,}",
        f"Search space      : {dims or '(single fixed chip)'}",
    ]

    lines.extend(["", f"TOP {top_n} BY TOKENS/SEC", "-" * 60])
    lines.append(
        "  #  tok/s      cycles     area(mm²)  W       "
        "cmp   mem   arch"
    )

    for index, item in enumerate(ranked[:top_n], start=1):
        mark = "*" if id(item) in frontier_ids else " "
        lines.append(
            f"{mark}{index:>2} "
            f"{_compact_number(item.tokens_per_second):>10} "
            f"{_compact_number(item.total_cycles):>11} "
            f"{item.area_mm2:>10.3f} "
            f"{item.power_watts:>8.3f} "
            f"{item.result.compute_utilization * 100:>5.1f} "
            f"{item.result.memory_utilization * 100:>5.1f} "
            f"{item.spec.label()}"
        )

    lines.extend(
        [
            "",
            "PARETO FRONTIER (tokens/sec vs die area)",
            "-" * 60,
        ]
    )
    lines.append("  #  tok/s      cycles     area(mm²)  arch")

    frontier_ranked = sorted(
        frontier,
        key=lambda item: item.tokens_per_second,
        reverse=True,
    )

    for index, item in enumerate(frontier_ranked, start=1):
        lines.append(
            f"{index:>3} "
            f"{_compact_number(item.tokens_per_second):>10} "
            f"{_compact_number(item.total_cycles):>11} "
            f"{item.area_mm2:>10.3f} "
            f"{item.spec.label()}"
        )

    if len(frontier) == len(results) and len(results) > 1:
        lines.append(
            "  (all candidates are Pareto-optimal: "
            "objectives do not trade off)"
        )

    lines.append("")
    lines.append(
        "* = candidate is on the Pareto frontier"
    )

    return "\n".join(lines)


def format_trace(
    result: EndToEndResult,
    limit: int = 40,
) -> str:
    """
    Compact per-cycle activity trace for each resource.
    """

    by_resource: dict[str, list] = {}

    for entry in result.schedule.trace:
        by_resource.setdefault(
            entry.resource,
            []
        ).append(entry)

    lines = ["CYCLE TRACE (activity at cycle boundaries)", "-" * 60]

    for resource_name, entries in by_resource.items():
        lines.append("")
        lines.append(resource_name)
        lines.append("-" * 60)

        shown = 0
        last_cycle = -1
        last_busy = -1
        last_active = -1

        for entry in entries:
            if shown >= limit:
                break

            if (
                entry.cycle == last_cycle
                and entry.busy_units == last_busy
                and entry.active_tasks == last_active
            ):
                continue

            lines.append(
                f"cycle {entry.cycle:>9,} "
                f"| busy {entry.busy_units:>6,}/{entry.capacity:>6,} "
                f"| tasks {entry.active_tasks}"
            )

            last_cycle = entry.cycle
            last_busy = entry.busy_units
            last_active = entry.active_tasks
            shown += 1

        if shown == limit and len(entries) > limit:
            lines.append("... (truncated)")

    lines.append("")
    lines.append(
        "PEAK CONCURRENCY"
        " (max busy units per resource)"
    )
    lines.append("-" * 60)

    for name, peak in result.schedule.peak_concurrency.items():
        lines.append(
            f"{name:<20}{peak:>8,}"
        )

    return "\n".join(lines)
