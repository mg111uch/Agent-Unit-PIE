"""Secret scan (OPS-03). Stdlib only, no network.

    python scripts/secret_scan.py            # scan the repo, exit 1 on a hit
    python scripts/secret_scan.py --all      # include normally-skipped dirs

Detects real-looking credentials only. `.env.example` placeholders pass
because values must be at least 16 chars and not an obvious placeholder.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "data",
             "atlas_output", "generated_reports", "encoding_cache", "cache",
             ".agent_checkpoints", "chroma_data", "utils_files", "backups",
             ".venv", "venv", "dist", "build"}

SKIP_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".png", ".jpg", ".jpeg",
                 ".gif", ".pdf", ".zip", ".gz", ".tgz", ".whl", ".so",
                 ".pyc", ".bin", ".csv", ".xlsx", ".parquet", ".lock"}

PLACEHOLDERS = {"", "changeme", "change-me", "example", "your-key-here",
                "xxx", "todo", "placeholder", "redacted", "<key>", "null",
                "none", "test", "secret", "password", "..."}

# (name, regex, min length of the captured secret)
PATTERNS: List[Tuple[str, re.Pattern, int]] = [
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), 1),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), 20),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), 20),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"), 30),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), 30),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{20,}"), 20),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 16),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), 30),
    ("assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|jwt[_-]?secret)"
        r"\s*[:=]\s*['\"]?([A-Za-z0-9._\-+/=]{16,})['\"]?"), 16),
]

ALLOW_MARKERS = ("<", ">", "$", "{", "}", "your", "example", "redacted",
                 # code expressions, not literals: `token = secrets…`, `token = location…`
                 "secrets.", "token_urlsafe", "location.", "getenv", "os.environ")


def _skip(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return any(part in SKIP_DIRS for part in path.parts)


def _files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and not _skip(p.relative_to(root)):
            yield p


def _looks_placeholder(value: str) -> bool:
    v = value.strip().strip("'\"").lower()
    return v in PLACEHOLDERS or any(m in v for m in ALLOW_MARKERS)


def scan(path: Path, root: Path) -> List[dict]:
    hits = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), start=1):
        if len(line) > 2000:  # minified blobs are noise, not secrets
            continue
        for name, rx, min_len in PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            value = m.group(1) if m.groups() else m.group(0)
            if len(value) < min_len or _looks_placeholder(value):
                continue
            hits.append({"file": str(path.relative_to(root)),
                         "line": lineno, "kind": name})
            break
    return hits


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=str(ROOT))
    ap.add_argument("--all", action="store_true", help="include skipped dirs")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.path).resolve()
    global SKIP_DIRS
    if a.all:
        SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

    hits: List[dict] = []
    for f in _files(root):
        hits.extend(scan(f, root))

    if a.json:
        import json
        print(json.dumps({"hits": hits, "files_scanned": sum(1 for _ in _files(root))}, indent=1))
    else:
        for h in hits:
            print(f"{h['file']}:{h['line']}  {h['kind']}")
        print(f"{len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
