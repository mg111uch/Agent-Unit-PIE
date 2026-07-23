"""Shared citation resolution and bullet parsing for seed + validate scripts."""

import re
import sqlite3
import subprocess
from pathlib import Path

FILE_FUNC_RE = re.compile(r'([\w/.-]+\.py):(\w+)\(\)')
FILE_ONLY_RE = re.compile(r'([\w/.-]+\.py)')
EM_DASH = ' \u2014 '
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODEBASE_DIR = PROJECT_ROOT / "codebase"
ATLAS_DB = PROJECT_ROOT / "atlas_output" / "code_rag.db"


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


def resolve_symbol(filename, funcname):
    atlas_path = ATLAS_DB
    conn = None
    cur = None
    if atlas_path.exists():
        conn = sqlite3.connect(str(atlas_path))
        cur = conn.cursor()
    found = False
    resolved_path = None
    if cur and funcname:
        row = cur.execute(
            "SELECT file_path FROM symbols WHERE symbol_name = ? AND file_path LIKE ?",
            (funcname, f"%/{filename}"),
        ).fetchone()
        if row:
            found = True
            abs_path = row[0]
            try:
                resolved_path = str(Path(abs_path).relative_to(PROJECT_ROOT))
            except ValueError:
                resolved_path = abs_path
    if not found and funcname:
        result = subprocess.run(
            ["grep", "-rl", f"def {funcname}(", str(CODEBASE_DIR), "--include", filename],
            capture_output=True, text=True, timeout=30,
        )
        stdout = result.stdout.strip()
        if stdout:
            found = True
            abs_path = stdout.splitlines()[0]
            try:
                resolved_path = str(Path(abs_path).relative_to(PROJECT_ROOT))
            except ValueError:
                resolved_path = abs_path
    if conn:
        conn.close()
    return found, resolved_path


def discover_status_files():
    reports_dir = PROJECT_ROOT / "system_devpt_reports"
    return sorted(reports_dir.glob("*/status.md"))


def extract_module_name(status_path):
    return status_path.parent.name
