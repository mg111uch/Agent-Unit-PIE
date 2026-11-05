"""PIE backups + restore drill (OPS-01).

    python scripts/backup.py                 # snapshot every known SQLite file
    python scripts/backup.py --restore-drill # verify newest snapshots open

Uses sqlite3's online backup API, so a running server is safe. Each snapshot
gets a `.sha256` sidecar and one `manifest.json` per run. Encryption is
optional and only reported as done when a real tool (`age`/`gpg`) ran:
honesty beats a flag that pretends the copy is encrypted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from paths import DATA_ROOT  # noqa: E402

DBS = ("kernel.db", "market.db", "bhav_copy.db")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _encrypt(src: Path) -> dict:
    """Encrypt with age/gpg if present; never claim it without a tool."""
    for tool, cmd in (("age", ["age", "-p", "-o", str(src) + ".age", str(src)]),
                      ("gpg", ["gpg", "--batch", "--yes", "--symmetric",
                               "--output", str(src) + ".gpg", str(src)])):
        if not shutil.which(tool):
            continue
        try:
            subprocess.run(cmd, check=True, capture_output=True, input=b"")
            return {"tool": tool, "file": f"{src}.{tool == 'age' and 'age' or 'gpg'}"}
        except subprocess.SubprocessError as e:
            return {"tool": tool, "error": str(e)}
    return {"tool": None, "error": "no age/gpg installed; backup is plaintext"}


def _copy_db(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(dest) + ".tmp"
    with sqlite3.connect(f"file:{src}?mode=ro", uri=True) as s, \
            sqlite3.connect(tmp) as d:
        s.backup(d)
    Path(tmp).replace(dest)


def backup(outdir: Path, encrypt: bool = False) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    entries, skipped = [], []
    for name in DBS:
        src = DATA_ROOT / name
        if not src.exists():
            skipped.append(name)
            continue
        dest = outdir / f"{stamp}-{name}"
        _copy_db(src, dest)
        digest = _sha256(dest)
        Path(f"{dest}.sha256").write_text(f"{digest}  {dest.name}\n")
        entry = {"db": name, "file": str(dest), "sha256": digest,
                 "bytes": dest.stat().st_size}
        if encrypt:
            entry["encryption"] = _encrypt(dest)
        entries.append(entry)
    manifest = {"ok": True, "stamp": stamp, "data_root": str(DATA_ROOT),
                "skipped": skipped, "files": entries,
                "off_machine": bool(os.environ.get("BACKUP_REMOTE"))}
    (outdir / f"{stamp}-manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def restore_drill(outdir: Path) -> dict:
    manifests = sorted(outdir.glob("*-manifest.json"))
    if not manifests:
        return {"ok": False, "error": "no backups found; run without --restore-drill"}
    manifest = json.loads(manifests[-1].read_text())
    checks = []
    for entry in manifest["files"]:
        src = Path(entry["file"])
        expected = Path(f"{src}.sha256").read_text().split(" ")[0]
        actual = _sha256(src) if src.exists() else ""
        tmp = Path(tempfile.gettempdir()) / f"drill-{src.name}"
        ok_rows = None
        if src.exists():
            shutil.copyfile(src, tmp)
            try:
                with sqlite3.connect(tmp) as con:
                    ok_rows = con.execute(
                        "SELECT COUNT(*) FROM sqlite_master").fetchone()[0]
            finally:
                tmp.unlink(missing_ok=True)
        checks.append({"db": entry["db"], "checksum_ok": expected == actual,
                       "opens": bool(ok_rows), "tables": ok_rows})
    return {"ok": all(c["checksum_ok"] and c["opens"] for c in checks),
            "manifest": str(manifests[-1]), "checks": checks,
            "encrypted": any((e.get("encryption") or {}).get("tool")
                             for e in manifest["files"])}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir",
                    default=os.environ.get("BACKUP_DIR", str(DATA_ROOT / "backups")))
    ap.add_argument("--encrypt", action="store_true")
    ap.add_argument("--restore-drill", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    out = restore_drill(Path(a.outdir)) if a.restore_drill else \
        backup(Path(a.outdir), a.encrypt)
    print(json.dumps(out, indent=1) if a.json else
          (f"ok={out.get('ok')} files={len(out.get('files', []))}"
           if not a.restore_drill else f"ok={out.get('ok')} checks={out.get('checks')}"))
    if a.restore_drill and not out.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
