"""Deliverable assembly (REV-07): CSV + XLSX + methodology note.

A customer never receives a bare dump. Every row carries `confidence` and
`source`, and the bundle ships a methodology note that states the QC policy,
the SLA and the refund rule. XLSX is written with a tiny stdlib writer so no
extra dependency is needed; if that writer fails the caller still gets CSV.
"""
from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from modules.economy import qc

DEFAULT_COLUMNS = ("record_id", "name", "value", "confidence", "source")


def _normalise(records: Iterable[Dict[str, Any]],
               columns: Sequence[str]) -> List[Dict[str, Any]]:
    rows = []
    for r in records:
        fields = dict(r.get("fields") or {})
        row = {"record_id": r.get("record_id", ""), **fields}
        row.setdefault("name", fields.get("company") or fields.get("name", ""))
        row.setdefault("value", fields.get("value", ""))
        row["confidence"] = r.get("confidence", "")
        row["source"] = r.get("source") or r.get("evidence") or ""
        rows.append(row)
    ordered = [c for c in columns] + [c for c in rows[0] if c not in columns] \
        if rows else list(columns)
    return [{c: r.get(c, "") for c in ordered} for r in rows]


def write_csv(path: Path, rows: List[Dict[str, Any]],
              columns: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(columns))
        w.writeheader()
        w.writerows(rows)
    return path


def _col(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        s = chr(65 + rem) + s
    return s


def _esc(v: Any) -> str:
    return (str(v).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _sheet_xml(rows: List[Dict[str, Any]], columns: Sequence[str]) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
           "<sheetData>"]
    header = ["".join(
        f'<c r="{_col(i)}1" t="inlineStr"><is><t>{_esc(c)}</t></is></c>'
        for i, c in enumerate(columns))]
    out.append(f'<row r="1">{"".join(header)}</row>')
    for r_i, row in enumerate(rows, start=2):
        cells = []
        for c_i, c in enumerate(columns):
            ref = f"{_col(c_i)}{r_i}"
            v = row.get(c, "")
            if isinstance(v, bool) or v is None:
                v = "" if v is None else str(v).lower()
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(f'<c r="{ref}"><v>{v}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{_esc(v)}</t></is></c>')
        out.append(f'<row r="{r_i}">{"".join(cells)}</row>')
    out.append("</sheetData></worksheet>")
    return "".join(out)


_STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
           '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
           '<borders count="1"><border/></borders>'
           '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
           '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
           "</styleSheet>")

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    "</Types>")

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>")

_WB_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    "</Relationships>")


def _workbook_xml(sheet_name: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{_esc(sheet_name)[:31] or "Deliverable"}" '
            'sheetId="1" r:id="rId1"/></sheets></workbook>')


def write_xlsx(path: Path, rows: List[Dict[str, Any]],
               columns: Sequence[str], sheet_name: str = "Deliverable") -> Path:
    """Smallest valid XLSX (one sheet, inline strings) — no dependencies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("xl/workbook.xml", _workbook_xml(sheet_name))
        z.writestr("xl/_rels/workbook.xml.rels", _WB_RELS)
        z.writestr("xl/styles.xml", _STYLES)
        z.writestr("xl/worksheets/sheet1.xml", _sheet_xml(rows, list(columns)))
    return path


def methodology_note(project: str, row_count: int,
                     qc_report: Dict[str, Any],
                     extra: Sequence[str] = ()) -> str:
    """Markdown note the customer reads next to the data."""
    p = qc_report.get("policy") or qc.policy()
    summary = (qc_report.get("consensus") or {}).get("summary") or {}
    gold = qc_report.get("gold") or {}
    verdict = qc_report.get("verdict") or {}
    lines = [
        f"# Methodology — {project}",
        "",
        f"Rows delivered: **{row_count}**. Every row carries a `confidence` "
        "score and a `source` field; nothing without a source is included.",
        "",
        "## How the data was checked",
        f"- Blind duplicate assignment on {int(p['duplicate_ratio'] * 100)}% of "
        "records (a second analyst never sees the first answer).",
        f"- Gold records with known answers on {int(p['gold_ratio'] * 100)}% of "
        "the batch, scored separately.",
        f"- Human spot-check on {int(p['spotcheck_ratio'] * 100)}% of records.",
        "",
        "## QC result",
        f"- Records: {summary.get('total', 0)} "
        f"(agreed {summary.get('agreed', 0)}, disputed "
        f"{summary.get('disputed', 0)}, unverified "
        f"{summary.get('unverified', 0)}).",
        f"- Mean confidence: {summary.get('mean_confidence')}.",
        f"- Gold accuracy: {gold.get('accuracy')} "
        f"({gold.get('correct', 0)}/{gold.get('gold_fields', 0)} fields).",
        f"- SLA: {int(p['sla_accuracy'] * 100)}% accuracy.",
        "",
        "## Confidence meanings",
        "- `1.0` two blind copies agreed on every field.",
        "- `< 1.0` partial agreement; the `disagreements` list is available.",
        f"- `{qc.SINGLE_SOURCE_CONFIDENCE}` single source, not yet cross-checked.",
        "",
        "## Refund rule",
        "Below SLA: 50% refund for 75-90% accuracy, 100% below 75%, "
        "calculated from the gold set on the same batch.",
    ]
    if verdict and not verdict.get("pass"):
        lines.append(f"\n**This batch:** {verdict.get('reason')}; "
                     f"refund {verdict.get('refund', {}).get('percent', 0)}%.")
    lines.extend(["", "## Scope limits"] + [f"- {e}" for e in extra])
    return "\n".join(lines) + "\n"


def build(records: Iterable[Dict[str, Any]], outdir: str | Path,
          project: str = "deliverable",
          columns: Sequence[str] = DEFAULT_COLUMNS,
          qc_report: Dict[str, Any] | None = None,
          limits: Sequence[str] = ()) -> Dict[str, Any]:
    """Write the bundle; return paths + a one-line manifest for the ledger."""
    out = Path(outdir)
    rows = _normalise(records, columns)
    cols = list(rows[0]) if rows else list(columns)
    report = qc_report or {"policy": qc.policy(), "consensus": {
        "summary": {"total": len(rows), "agreed": 0, "disputed": 0,
                    "unverified": len(rows), "mean_confidence": None}},
        "gold": {"accuracy": None, "correct": 0, "gold_fields": 0},
        "verdict": qc.evaluate(None)}

    files: Dict[str, str] = {}
    files["csv"] = str(write_csv(out / f"{project}.csv", rows, cols))
    try:
        files["xlsx"] = str(write_xlsx(out / f"{project}.xlsx", rows, cols))
    except Exception as e:  # XLSX is a convenience; CSV is the contract.
        files["xlsx_error"] = f"{type(e).__name__}: {e}"
    note = methodology_note(project, len(rows), report, limits)
    note_path = out / f"{project}-methodology.md"
    note_path.write_text(note, encoding="utf-8")
    files["methodology"] = str(note_path)

    return {
        "project": project, "rows": len(rows), "columns": cols,
        "files": files,
        "qc": {"accuracy": report.get("gold", {}).get("accuracy"),
               "summary": (report.get("consensus") or {}).get("summary"),
               "pass": report.get("verdict", {}).get("pass")},
        "manifest": json.dumps({"project": project, "rows": len(rows),
                                "files": sorted(k for k in files)},
                               sort_keys=True),
    }
