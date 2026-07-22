#!/usr/bin/env python3
"""Parse system_devpt_reports/*/status.md and seed capability/gap hypotheses into kernel HypothesisEngine."""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from kernel.hypothesis.hypothesis_engine import hypothesis_engine

FILE_FUNC_RE = re.compile(r'([\w/.-]+\.py):(\w+)\(\)')
FILE_ONLY_RE = re.compile(r'([\w/.-]+\.py)')
EM_DASH = ' \u2014 '


def extract_file_func(text):
    m = FILE_FUNC_RE.search(text)
    if m:
        return m.group(1), m.group(2)
    m = FILE_ONLY_RE.search(text)
    if m:
        return m.group(1), ""
    return None, None


def extract_section(text, section_title):
    lines = text.splitlines()
    result = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## ') and section_title in stripped:
            found = True
            continue
        if found:
            if stripped.startswith('## ') and section_title not in stripped:
                break
            result.append(line)
    return '\n'.join(result)


def parse_capabilities_from_lines(text):
    results = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('- '):
            continue
        if EM_DASH not in stripped:
            continue
        desc_part, _, citation_part = stripped.partition(EM_DASH)
        desc = desc_part.lstrip('- ').strip()
        citation_text = citation_part.strip().strip('`')
        filepath, funcname = extract_file_func(citation_text)
        results.append((desc, filepath, funcname))
    return results


def parse_gaps_from_lines(text):
    results = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('- '):
            continue
        if EM_DASH not in stripped:
            continue
        desc_part, _, sev_part = stripped.partition(EM_DASH)
        desc = desc_part.lstrip('- ').strip()
        severity = sev_part.strip()
        results.append((desc, severity))
    return results


def parse_kernel_table_capabilities(text):
    results = []
    in_phase = False
    for line in text.splitlines():
        if line.startswith('### Phase'):
            in_phase = True
            continue
        if in_phase and line.startswith('## '):
            in_phase = False
            continue
        if in_phase and line.startswith('|') and '\u2705' in line:
            cols = [c.strip() for c in line.split('|')]
            if len(cols) >= 4:
                desc = cols[1]
                citation_col = cols[2]
                filepath, funcname = extract_file_func(citation_col)
                results.append((desc, filepath, funcname))
    return results


def seed_all(engine=None):
    if engine is None:
        engine = hypothesis_engine

    reports_dir = PROJECT_ROOT / "system_devpt_reports"
    stats = {"capabilities": 0, "gaps": 0}

    debate_text = (reports_dir / "debate_argu" / "status.md").read_text(encoding="utf-8")
    kernel_text = (reports_dir / "kernel_core" / "kernel.md").read_text(encoding="utf-8")

    caps_text = extract_section(debate_text, "Current Capability")
    gaps_text = extract_section(debate_text, "Known Gaps")

    caps = parse_capabilities_from_lines(caps_text)
    gaps = parse_gaps_from_lines(gaps_text)
    kernel_caps = parse_kernel_table_capabilities(kernel_text)

    for i, (desc, filepath, funcname) in enumerate(caps, 1):
        metadata = {
            "source_file": "system_devpt_reports/debate_argu/status.md",
        }
        if filepath:
            metadata["evidence_path"] = filepath
        if funcname:
            metadata["evidence_symbol"] = funcname
        engine.create_hypothesis(
            hypothesis_id=f"cap_debate_{i}",
            title=desc,
            description=desc,
            hypothesis_type="capability_claim",
            category="system_status",
            metadata=metadata,
        )
        stats["capabilities"] += 1

    for i, (desc, severity) in enumerate(gaps, 1):
        h = engine.create_hypothesis(
            hypothesis_id=f"gap_debate_{i}",
            title=desc,
            description=desc,
            hypothesis_type="known_gap",
            category="system_status",
            metadata={
                "severity": severity,
                "source_file": "system_devpt_reports/debate_argu/status.md",
            },
        )
        h.status = "uncertain"
        stats["gaps"] += 1

    for i, (desc, filepath, funcname) in enumerate(kernel_caps, 1):
        if not funcname:
            continue
        metadata = {
            "source_file": "system_devpt_reports/kernel_core/kernel.md",
        }
        if filepath:
            metadata["evidence_path"] = filepath
        if funcname:
            metadata["evidence_symbol"] = funcname
        engine.create_hypothesis(
            hypothesis_id=f"cap_kernel_{i}",
            title=desc,
            description=desc,
            hypothesis_type="capability_claim",
            category="system_status",
            metadata=metadata,
        )
        stats["capabilities"] += 1

    return stats


def main():
    stats = seed_all()
    total = hypothesis_engine.stats()
    print(f"Seeded {stats['capabilities']} capability claims, {stats['gaps']} known gaps")
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
