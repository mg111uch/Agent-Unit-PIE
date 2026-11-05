"""GeM bid CSV import (REV-02) — the cheapest real top-of-funnel source.

A GeM export is downloaded by a human (no scraping, no CAPTCHA bypass) and
this module turns it into prospect dicts the existing pipeline already knows.
Every row keeps its provenance: `source="gem"` plus the bid reference.

Expected columns are matched loosely (case/spacing insensitive); unknown
columns are ignored rather than guessed.
"""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# GeM exports vary; this map covers the common header spellings.
COLUMNS = {
    "bid_number": ("bid number", "bid no", "bid_id", "bid id", "gem bid no"),
    "title": ("bid title", "title", "item category", "category name", "items"),
    "buyer": ("buyer", "consignee", "department", "ministry", "organisation"),
    "region": ("state", "delivery state", "consignee state", "location"),
    "quantity": ("quantity", "qty", "total quantity"),
    "value": ("estimated bid value", "bid value", "estimated value", "value"),
    "end_date": ("bid end date", "end date", "closing date", "due date"),
}

_NUM = re.compile(r"[^0-9.]")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _index(header: List[str]) -> Dict[str, int]:
    norm = [_norm(h) for h in header]
    out: Dict[str, int] = {}
    for key, options in COLUMNS.items():
        for opt in options:
            if opt in norm:
                out[key] = norm.index(opt)
                break
    return out


def _num(raw: str) -> float:
    cleaned = _NUM.sub("", (raw or "").replace(",", ""))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def _prospect_id(bid: str, title: str) -> str:
    digest = hashlib.sha1(f"{bid}|{title}".encode()).hexdigest()[:12]
    return f"pro_gem_{digest}"


def parse(path: str | Path, limit: Optional[int] = None) -> Dict[str, Any]:
    """CSV -> {items, skipped, note}. Never raises on a malformed row."""
    p = Path(path)
    if not p.exists():
        return {"items": [], "skipped": 0, "note": f"{p} not found"}
    items: List[Dict[str, Any]] = []
    skipped = 0
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return {"items": [], "skipped": 0, "note": "empty file"}
        idx = _index(header)
        if "title" not in idx and "bid_number" not in idx:
            return {"items": [], "skipped": 0,
                    "note": "no recognisable GeM columns (need bid number or title)"}
        for row in reader:
            if limit is not None and len(items) >= limit:
                break

            def cell(key: str) -> str:
                i = idx.get(key)
                return (row[i].strip() if i is not None and i < len(row) else "")

            title = cell("title")
            bid = cell("bid_number")
            if not title and not bid:
                skipped += 1
                continue
            buyer = cell("buyer")
            items.append({
                "prospect_id": _prospect_id(bid, title),
                "company": buyer or "GeM buyer",
                "problem": title or f"GeM bid {bid}",
                "region": cell("region"),
                "industry": "public procurement",
                "evidence": [f"GeM bid {bid}: {title}" if bid else f"GeM: {title}"],
                "triggers": ["tender"],
                "estimated_monthly_value": _num(cell("value")),
                "recommended_pilot": 5000.0,
                "contactability": 0.4,
                "confidence": 0.6,
                "source": "gem",
                "bid_number": bid,
                "quantity": cell("quantity"),
                "end_date": cell("end_date"),
            })
    return {"items": items, "skipped": skipped,
            "note": f"{len(items)} rows from {p.name}"}


def import_items(path: str | Path, limit: Optional[int] = None) -> List[Any]:
    """CSV -> normalized Prospects (the pipeline's own type)."""
    from modules.economy.discovery import normalize_raw
    parsed = parse(path, limit=limit)
    return normalize_raw("gem", parsed["items"])
