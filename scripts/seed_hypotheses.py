#!/usr/bin/env python3
"""Parse system_devpt_reports/*/status.md and seed capability/gap hypotheses."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.hypothesis.hypothesis_engine import hypothesis_engine
from scripts.lib.citations import (
    extract_section,
    parse_capabilities_from_lines,
    parse_gaps_from_lines,
    discover_status_files,
    extract_module_name,
)


def seed_all(engine=None):
    if engine is None:
        engine = hypothesis_engine

    stats = {"capabilities": 0, "gaps": 0}
    status_files = discover_status_files()

    for sf in status_files:
        module = extract_module_name(sf)
        text = sf.read_text(encoding="utf-8")

        caps_text = extract_section(text, "Current Capability")
        gaps_text = extract_section(text, "Known Gaps")

        caps = parse_capabilities_from_lines(caps_text)
        gaps = parse_gaps_from_lines(gaps_text)

        cap_prefix = f"cap_{module}"
        for i, (desc, filepath, funcname) in enumerate(caps, 1):
            hid = f"{cap_prefix}_{i}"
            metadata = {"source_file": str(sf.relative_to(PROJECT_ROOT))}
            if filepath:
                metadata["evidence_path"] = filepath
            if funcname:
                metadata["evidence_symbol"] = funcname
            existing = engine.get_hypothesis(hid)
            if existing:
                existing.title = desc
                existing.metadata.update(metadata)
            else:
                engine.create_hypothesis(
                    hypothesis_id=hid,
                    title=desc,
                    description=desc,
                    hypothesis_type="capability_claim",
                    category="system_status",
                    metadata=metadata,
                )
            stats["capabilities"] += 1

        gap_prefix = f"gap_{module}"
        for i, (desc, severity) in enumerate(gaps, 1):
            hid = f"{gap_prefix}_{i}"
            metadata = {
                "severity": severity,
                "source_file": str(sf.relative_to(PROJECT_ROOT)),
            }
            existing = engine.get_hypothesis(hid)
            if existing:
                existing.title = desc
                existing.metadata.update(metadata)
            else:
                h = engine.create_hypothesis(
                    hypothesis_id=hid,
                    title=desc,
                    description=desc,
                    hypothesis_type="known_gap",
                    category="system_status",
                    metadata=metadata,
                )
                h.status = "uncertain"
            stats["gaps"] += 1

    return stats


def main():
    stats = seed_all()
    total = hypothesis_engine.stats()
    print(f"Seeded {stats['capabilities']} capability claims, {stats['gaps']} known gaps from {len(discover_status_files())} files")
    print(f"Engine total: {total['total_hypotheses']} hypotheses")
    for hid in sorted(hypothesis_engine.hypotheses):
        h = hypothesis_engine.hypotheses[hid]
        ev = h.metadata.get("evidence_symbol", "")
        extra = h.metadata.get("evidence_path", "")
        print(f"  {hid:20s}  [{h.hypothesis_type:17s}]  {h.status:10s}  {h.title[:60]}")
        if ev:
            print(f"  {'':20s}  evidence: {extra}:{ev}()")


if __name__ == "__main__":
    main()
