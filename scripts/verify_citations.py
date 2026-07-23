#!/usr/bin/env python3
"""Verify file.py:function() citations in system_devpt_reports/*.md against codebase."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "codebase"))

from scripts.lib.citations import (
    FILE_FUNC_RE,
    resolve_symbol,
    discover_status_files,
    extract_module_name,
)


SKIP_FILES = {"file.py"}


def main():
    results = []
    for status_path in discover_status_files():
        module = extract_module_name(status_path)
        text = status_path.read_text(encoding="utf-8")
        rel = status_path.relative_to(PROJECT_ROOT)
        for match in FILE_FUNC_RE.finditer(text):
            filename = match.group(1)
            funcname = match.group(2)
            if filename in SKIP_FILES:
                continue
            line_num = text[: match.start()].count("\n") + 1
            found, _ = resolve_symbol(filename, funcname)
            tag = "PASS" if found else "FAIL"
            source = "atlas" if found else "grep"
            results.append((tag, source, rel, line_num, filename, funcname))

    for tag, source, rel, line_num, filename, funcname in sorted(results):
        print(f"  {tag}  [{source:5s}] {rel}:{line_num}  {filename}:{funcname}()")

    print()
    print("=" * 52)
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    print(f"  Total: {passed + failed}  Passed: {passed}  Failed: {failed}")
    if failed:
        print("  Some citations failed verification.")
    else:
        print("  All citations verified.")
    print("=" * 52)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
