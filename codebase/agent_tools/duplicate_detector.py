#!/usr/bin/env python3
"""Intra-file code duplication detector.

Scans files for repeated code blocks WITHIN each file (exact and near-duplicates).

Usage:
  conda run --no-capture-output -n myenv python codebase/agent_tools/duplicate_detector.py
  conda run --no-capture-output -n myenv python codebase/agent_tools/duplicate_detector.py --root /path --min-lines 6
  conda run --no-capture-output -n myenv python codebase/agent_tools/duplicate_detector.py --json --output report.json

Example run against the codebase (default --root codebase, defaults otherwise):
  conda run --no-capture-output -n myenv python codebase/agent_tools/duplicate_detector.py

  Expected output (representative hits, capped at --max-per-file 10 per file):

    codebase/agent_core/providers/gemini_provider/interaction.py
      [1] 6 lines, similarity 0.940, lines 62-67 and 86-91
      A:
        62:     def _generate_initial_from_messages(
        63:         self,
        64:         messages: List[Dict[str, Any]],
        ...
      B:
        86:     def _generate_stateful(
        ...

    ============================================================
    Files scanned:      316
    Duplicate groups:   1406
    Duplicated lines:   10664

  Findings scale with settings; lower --min-lines / --min-similarity to widen,
  or raise --max-per-file to see every group.
"""

from __future__ import annotations

import argparse
import difflib
import json
import keyword
import os
import re
from collections import defaultdict

TOKEN_RE = re.compile(r"\w+|[^\s\w]")
_KEYWORDS = frozenset(keyword.kwlist)

DEFAULT_ROOT = "/home/manigupt/Hello/Agentic_Unit_PIE/codebase"
DEFAULT_IGNORE_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", ".venv", "env"}
DEFAULT_IGNORE_FILES = {"__init__.py"}


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _normalize(text: str) -> str:
    """Replace identifiers/literals with placeholders so near-copies share seeds."""
    out = []
    for tok in _tokens(text):
        if tok.isdigit() or (tok[0].isdigit() and len(tok) > 1):
            out.append("L")
        elif tok.isidentifier() and tok not in _KEYWORDS:
            out.append("N")
        else:
            out.append(tok)
    return " ".join(out)


def _line_similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return difflib.SequenceMatcher(None, ta, tb).ratio()


def _maximal_blocks(lines, norm_lines, seed_lines, min_lines, line_threshold, min_similarity):
    n = len(lines)
    if n < seed_lines:
        return []

    # Group identical normalized seed windows by hash.
    buckets = defaultdict(list)
    for i in range(n - seed_lines + 1):
        key = tuple(norm_lines[i + j] for j in range(seed_lines))
        buckets[key].append(i)

    blocks = []
    seen_starts = set()

    def extend(start1, start2):
        ssum = 0.0
        cnt = 0
        for j in range(seed_lines):
            s = _line_similarity(lines[start1 + j][1], lines[start2 + j][1])
            ssum += s
            cnt += 1
        end1, end2 = start1 + seed_lines, start2 + seed_lines
        while end2 < n and end1 < start2:
            s = _line_similarity(lines[end1][1], lines[end2][1])
            if s < line_threshold or (ssum + s) / (cnt + 1) < min_similarity:
                break
            ssum += s
            cnt += 1
            end1 += 1
            end2 += 1
        while start1 > 0 and start2 - start1 > seed_lines:
            s = _line_similarity(lines[start1 - 1][1], lines[start2 - 1][1])
            if s < line_threshold or (ssum + s) / (cnt + 1) < min_similarity:
                break
            ssum += s
            cnt += 1
            start1 -= 1
            start2 -= 1
        return start1, end1, start2, end2, ssum / cnt

    for positions in buckets.values():
        if len(positions) < 2:
            continue
        positions.sort()
        for a_idx, p1 in enumerate(positions):
            for p2 in positions[a_idx + 1:]:
                if (p1, p2) in seen_starts:
                    continue
                seen_starts.add((p1, p2))
                start1, end1, start2, end2, score = extend(p1, p2)
                length = end1 - start1
                if length < min_lines or end1 > start2:
                    continue
                blocks.append(
                    {
                        "start1": lines[start1][0],
                        "end1": lines[end1 - 1][0],
                        "start2": lines[start2][0],
                        "end2": lines[end2 - 1][0],
                        "length": length,
                        "similarity": score,
                        "lines": (start1, end1, start2, end2),
                    }
                )

    return blocks


def _dedup(blocks):
    """Drop any block nested inside a longer block with the same region starts."""
    by_starts = defaultdict(list)
    for b in blocks:
        by_starts[(b["lines"][0], b["lines"][2])].append(b)

    kept = []
    for group in by_starts.values():
        best = max(group, key=lambda b: (b["length"], b["similarity"]))
        kept.append(best)
    return kept


def detect_file(path, seed_lines, min_lines, min_similarity, line_threshold, max_per_file):
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read().splitlines()

    lines = [(i + 1, re.sub(r"\s+", " ", ln.strip())) for i, ln in enumerate(raw) if ln.strip()]
    if len(lines) < seed_lines:
        return []

    norm_lines = [_normalize(text) for _, text in lines]
    blocks = _maximal_blocks(lines, norm_lines, seed_lines, min_lines, line_threshold, min_similarity)
    blocks = _dedup(blocks)

    # Verify regions do not overlap.
    results = []
    for b in blocks:
        s1, e1, s2, e2 = b["lines"]
        if e1 > s2:
            continue
        results.append(b)
        if max_per_file and len(results) >= max_per_file:
            break
    results.sort(key=lambda b: (-b["similarity"], -b["length"]))
    return results


def _iter_files(root, extensions, ignore_dirs, ignore_files):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for fn in sorted(filenames):
            if fn in ignore_files:
                continue
            if os.path.splitext(fn)[1].lower() in extensions:
                yield os.path.join(dirpath, fn)


def _print_report(results_by_file, show_code):
    total_groups = 0
    total_lines = 0
    for path in sorted(results_by_file, key=lambda p: -len(results_by_file[p])):
        groups = results_by_file[path]
        if not groups:
            continue
        print(f"\n{path}")
        for idx, g in enumerate(groups, 1):
            print(
                f"  [{idx}] {g['length']} lines, similarity {g['similarity']:.3f}, "
                f"lines {g['start1']}-{g['end1']} and {g['start2']}-{g['end2']}"
            )
            total_groups += 1
            total_lines += g["length"]
            if show_code:
                _print_excerpt(path, g)
    return total_groups, total_lines


def _print_excerpt(path, g):
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read().splitlines()
    for label, start, end in (("  A", g["start1"], g["end1"]), ("  B", g["start2"], g["end2"])):
        print(f"{label}:")
        for ln in range(start - 1, min(end, start + 4)):
            print(f"    {ln + 1}: {content[ln]}")
        if end - start > 4:
            print(f"    ... ({end - start} lines)")


def main():
    parser = argparse.ArgumentParser(description="Detect intra-file code duplication candidates.")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Root dir to scan (default: {DEFAULT_ROOT})")
    parser.add_argument("--extensions", nargs="+", default=[".py"], help="File extensions to scan (default: .py)")
    parser.add_argument("--ignore-dirs", nargs="+", default=sorted(DEFAULT_IGNORE_DIRS))
    parser.add_argument("--ignore-files", nargs="+", default=sorted(DEFAULT_IGNORE_FILES))
    parser.add_argument("--seed-lines", type=int, default=2, help="Seed window size (default: 2)")
    parser.add_argument("--min-lines", type=int, default=5, help="Minimum duplicate block length (default: 5)")
    parser.add_argument("--min-similarity", type=float, default=0.6, help="Min block similarity 0-1 (default: 0.6)")
    parser.add_argument("--line-threshold", type=float, default=0.5, help="Min per-line similarity to extend (default: 0.5)")
    parser.add_argument("--max-per-file", type=int, default=10, help="Cap groups per file, 0 = unlimited (default: 10)")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--output", help="Write JSON report to file")
    parser.add_argument("--no-code", action="store_true", help="Omit code excerpts")
    args = parser.parse_args()

    results_by_file = {}
    for path in _iter_files(args.root, set(e.lower() for e in args.extensions), set(args.ignore_dirs), set(args.ignore_files)):
        groups = detect_file(
            path, args.seed_lines, args.min_lines, args.min_similarity, args.line_threshold, args.max_per_file
        )
        if groups:
            results_by_file[path] = groups

    total_groups, total_lines = _print_report(results_by_file, not args.no_code)
    print(f"\n{'=' * 60}")
    print(f"Files scanned:      {sum(1 for _ in _iter_files(args.root, set(args.extensions), set(args.ignore_dirs), set(args.ignore_files)))}")
    print(f"Duplicate groups:   {total_groups}")
    print(f"Duplicated lines:   {total_lines}")

    if args.json or args.output:
        payload = {"root": args.root, "files": {p: g for p, g in results_by_file.items()}}
        data = json.dumps(payload, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(data + "\n")
            print(f"\nReport written to {args.output}")
        if args.json:
            print(data)


if __name__ == "__main__":
    main()