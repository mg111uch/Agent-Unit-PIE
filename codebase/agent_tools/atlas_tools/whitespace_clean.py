#!/usr/bin/env python3
"""
Whitespace Cleaner — removes excess blank lines from function/class bodies
while keeping standard one-line spacing between definitions.

Usage:
    # Single file (Output: Removed 104 blank lines)
    python whitespace_clean.py path/to/file.py

    # Recursive directory (all .py files)
    python whitespace_clean.py --dir path/to/dir

    # Dry-run (show what would change without modifying)
    python whitespace_clean.py --dry-run path/to/file.py
    Output: (Would remove 104 blank line(s))

    # CI check mode (exit 1 if any file has excess whitespace)    
    python whitespace_clean.py --check path/to/file.py
    Output: (excess whitespace detected)

    # With verbose output(Print per-file summary)
    python whitespace_clean.py --verbose --dir path/to/dir

    # Ignore specific directories (repeatable)
    python whitespace_clean.py --dir . --ignore-dirs __pycache__ .venv node_modules

    # Also simplify 3-line section headers (e.g., # ==== NAME ====)
    python whitespace_clean.py --simplify-headers path/to/file.py
    python whitespace_clean.py --dir . --simplify-headers
"""

import os
import sys
import re
import argparse


def _has_triple_quotes(line: str) -> bool:
    return '"""' in line or "'''" in line


def _triple_quote_odd(line: str) -> bool:
    """Return True if the line has an odd number of triple-quote delimiters."""
    return (line.count('"""') + line.count("'''")) % 2 == 1


def simplify_headers(content: str) -> str:
    """Collapse 3-line section headers into single-line format.

    Before:                After:
      # ================     # ===== NAME =====
      # NAME
      # ================
    """
    def _replacer(m):
        indent = m.group(1)
        name = m.group(3).strip()
        return f"{indent}# {name}"

    return re.sub(
        r'^([ \t]*)#[ \t]*([=\-]{3,})\s*'
        r'\n\1#[ \t]*(.+?)\s*'
        r'\n\1#[ \t]*\2',
        _replacer,
        content,
        flags=re.MULTILINE,
    )


def clean_file_content(content: str) -> str:
    """Remove excess blank lines inside function/class bodies.

    Uses a look-ahead strategy: when a blank line is encountered, it peeks at
    the next non-blank line's indentation to decide whether the blank is inside
    a function/class body (→ remove) or between definitions (→ keep one).

    Rules:
      - Inside any function or class body: ALL blank lines removed.
      - Between function/class definitions at the same indentation level:
        exactly ONE blank line kept.
      - At module top-level (outside any definition): consecutive blank lines
        collapsed to at most ONE.
      - Inside triple-quoted strings (docstrings, etc.): whitespace preserved
        verbatim.
    """
    lines = content.split("\n")
    if not lines:
        return content

    output = []
    def_stack = []          # indentation levels of enclosing defs/classes
    in_multiline = False
    i = 0

    while i < len(lines):
        raw = lines[i]
        stripped = raw.rstrip()
        indent = len(raw) - len(raw.lstrip())

        # ---------- multiline string ----------
        if in_multiline:
            output.append(raw)
            if _has_triple_quotes(raw):
                in_multiline = False
            i += 1
            continue

        if _has_triple_quotes(stripped) and _triple_quote_odd(stripped):
            in_multiline = True

        # ---------- blank line ----------
        if not stripped:
            # Look ahead to find the next non-blank line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1

            if j >= len(lines):
                break  # trailing blanks → discard

            next_raw = lines[j]
            next_indent = len(next_raw) - len(next_raw.lstrip())
            next_stripped = next_raw.strip()
            next_is_def = (
                next_stripped.startswith("def ")
                or next_stripped.startswith("class ")
                or next_stripped.startswith("async def ")
            )

            # A blank is "inside a body" when the next non-blank line is
            # more indented than the innermost enclosing definition.
            inside = bool(def_stack and next_indent > def_stack[-1])

            # Even if the next line is inside a body, if it's also a new
            # definition at its own level we WANT to keep the blank before it.
            # This handles: blank line before `def bar(self):` inside a class.
            # The blank is inside the class body but between method defs.
            at_boundary = next_is_def and bool(def_stack and next_indent == def_stack[-1])

            if not inside or at_boundary:
                if not output or output[-1] != "":
                    output.append("")

            # Skip all consecutive blank lines at once
            i = j
            continue

        # ---------- non-blank line ----------
        # Pop definitions that this line has dedented past
        while def_stack and indent <= def_stack[-1]:
            def_stack.pop()

        is_def = (
            stripped.lstrip().startswith("def ")
            or stripped.lstrip().startswith("class ")
            or stripped.lstrip().startswith("async def ")
        )
        if is_def:
            def_stack.append(indent)

        output.append(raw)
        i += 1

    return "\n".join(output)


def process_file(
    filepath: str,
    dry_run: bool = False,
    verbose: bool = False,
    check: bool = False,
    simplify_headers_flag: bool = False,
) -> dict:
    """Clean a single .py file.

    Returns dict: {"changed": bool, "lines_removed": int, "headers_done": int}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    cleaned = clean_file_content(original)

    if simplify_headers_flag:
        cleaned = simplify_headers(cleaned)

    blank_diff = original.count("\n") - cleaned.count("\n")

    headers_done = 0
    if simplify_headers_flag:
        orig_headers = len(re.findall(
            r'^[ \t]*#[ \t]*[=\-]{3,}\s*'
            r'\n[ \t]*#[ \t]*.+?\s*'
            r'\n[ \t]*#[ \t]*[=\-]{3,}',
            original, re.MULTILINE
        ))
        clean_headers = len(re.findall(
            r'^[ \t]*#[ \t]*[=\-]{3,}\s*'
            r'\n[ \t]*#[ \t]*.+?\s*'
            r'\n[ \t]*#[ \t]*[=\-]{3,}',
            cleaned, re.MULTILINE
        ))
        headers_done = orig_headers - clean_headers

    changed = blank_diff != 0 or headers_done != 0

    if not changed:
        if verbose:
            print(f"  \u2713  {filepath}")
        return {"changed": False, "lines_removed": 0, "headers_done": 0}

    if check:
        label = "simplify-headers" if simplify_headers_flag else "blank lines"
        print(f"  \u2717  {filepath}  (excess {label} detected)")
        return {"changed": True, "lines_removed": blank_diff, "headers_done": headers_done}

    if verbose or dry_run:
        parts = []
        if blank_diff:
            action = "Would remove" if dry_run else "Removed"
            parts.append(f"{action} {blank_diff} blank line(s)")
        if headers_done:
            action = "Would simplify" if dry_run else "Simplified"
            parts.append(f"{action} {headers_done} header(s)")
        if parts:
            print(f"  ~  {filepath}  ({', '.join(parts)})")

    if not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned)

    return {"changed": True, "lines_removed": blank_diff, "headers_done": headers_done}


def process_dir(
    dirpath: str,
    ignore_dirs: list[str],
    dry_run: bool = False,
    verbose: bool = False,
    check: bool = False,
    simplify_headers_flag: bool = False,
) -> int:
    """Recursively clean all .py files under dirpath.  Returns error count."""
    errors = 0
    total_lines = 0
    total_headers = 0
    modified_count = 0
    ignore_set = set(ignore_dirs or [])

    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in ignore_set]

        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                result = process_file(
                    fpath, dry_run=dry_run, verbose=verbose, check=check,
                    simplify_headers_flag=simplify_headers_flag,
                )
                if result["changed"]:
                    total_lines += result["lines_removed"]
                    total_headers += result["headers_done"]
                    modified_count += 1
                    if check:
                        errors += 1
            except Exception as e:
                print(f"  !  {fpath}  (error: {e})")
                errors += 1

    if modified_count and not check:
        parts = []
        action = "Would remove" if dry_run else "Removed"
        parts.append(f"{action} {total_lines} blank line(s)")
        if total_headers:
            parts.append(f"Simplified {total_headers} header(s)")
        parts.append(f"across {modified_count} file(s)")
        print(f"  ~  {dirpath}  ({', '.join(parts)})")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Remove excess blank lines inside function/class bodies.",
    )
    parser.add_argument(
        "path", nargs="?", default=None,
        help="File or directory to clean (use --dir for directories)",
    )
    parser.add_argument(
        "--dir", action="store_true",
        help="Recursively process all .py files under the given path",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without modifying files",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print summary per file",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="CI mode: exit code 1 if any file has excess whitespace (no --fix)",
    )
    parser.add_argument(
        "--ignore-dirs", nargs="*", default=[],
        help="Directory names to skip during recursive scan",
    )
    parser.add_argument(
        "--simplify-headers", action="store_true",
        help="Collapse 3-line section headers (e.g., # ==== NAME ====) into single lines",
    )

    args = parser.parse_args()

    if not args.path:
        parser.print_help()
        sys.exit(1)

    errors = 0

    if args.dir:
        if not os.path.isdir(args.path):
            print(f"Error: '{args.path}' is not a directory", file=sys.stderr)
            sys.exit(1)
        errors = process_dir(
            args.path,
            ignore_dirs=args.ignore_dirs,
            dry_run=args.dry_run,
            verbose=args.verbose,
            check=args.check,
            simplify_headers_flag=args.simplify_headers,
        )
    else:
        if not os.path.isfile(args.path):
            print(f"Error: '{args.path}' is not a file", file=sys.stderr)
            sys.exit(1)
        if not args.path.endswith(".py"):
            print("Error: only .py files are supported", file=sys.stderr)
            sys.exit(1)
        result = process_file(
            args.path,
            dry_run=args.dry_run,
            verbose=args.verbose or True,
            check=args.check,
            simplify_headers_flag=args.simplify_headers,
        )
        if result["changed"] and args.check:
            errors = 1

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
