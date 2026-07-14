"""Strip JavaScript/REST sections or list/extract headings from gemini_doc.md.

Commands:
  clean                Remove ### JavaScript and ### REST sections (default)
  list <level>         Print all headings at given level, e.g. list "##"
  extract <heading>    Extract section by heading name into OUTPUT file
"""

import os
import re
import sys

INPUT = "/home/manigupt/Hello/Agentic_Unit_PIE/gemini_update.md"
OUTPUT = "/home/manigupt/Hello/Agentic_Unit_PIE/gemini_section_output.md"


def _read() -> str:
    with open(INPUT, encoding="utf-8") as f:
        return f.read()


def _write(text: str) -> None:
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(text)


def clean() -> None:
    text = _read()
    cleaned = re.sub(
        r"^### (JavaScript|REST)\n\n(?:    .*\n?)*",
        "",
        text,
        flags=re.MULTILINE,
    )
    _write(cleaned)
    removed = len(re.findall(r"^### (JavaScript|REST)", text, re.MULTILINE))
    print(f"Removed {removed} section(s). Written to {INPUT}")


def list_headings(level: str) -> None:
    text = _read()
    pattern = rf"^{re.escape(level)}\s+(.+)$"
    headings = re.findall(pattern, text, re.MULTILINE)
    if headings:
        print("\n".join(headings))
    else:
        print(f"No headings at level '{level}'.")


def extract(heading: str) -> None:
    text = _read()
    pattern = re.compile(
        r"^(#{1,6})\s+" + re.escape(heading) + r"\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        print(f"Heading '{heading}' not found.")
        return

    level = match.group(1)
    start = match.start()
    rest = text[start + len(match.group(0)):]

    next_match = re.search(rf"^#{1,{len(level)}}\s+", rest, re.MULTILINE)
    end = start + len(match.group(0)) + (next_match.start() if next_match else len(rest))

    _write(text[start:end])
    print(f"Extracted '{heading}' to {OUTPUT}")


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "clean":
        clean()
    elif args[0] == "list" and len(args) >= 2:
        list_headings(args[1])
    elif args[0] == "extract" and len(args) >= 2:
        extract(args[1])
    else:
        print(__doc__.strip())


if __name__ == "__main__":
    main()
