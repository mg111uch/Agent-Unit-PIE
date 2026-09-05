"""Data-quality gate (stdlib): single choke point before research/simulation.

- Forming bar: recorder refreshes the live (nse/yahoo) last bar in place; drop it
  so research only sees closed bars. Adjusted history (yahoo-adj) + synthetic stay.
- Adjusted/unadjusted mix: yahoo-adj history + live bars in one window creates
  spurious jumps; flag mixed symbols, exclude when strict.
- Coverage/gaps: exclude gappy symbols; INSUFFICIENT_DATA when too few survive.
Thresholds via capital.yaml `quality_*` keys; lenient defaults.
"""
from __future__ import annotations
from typing import Any, Dict, List

LIVE_SOURCES = ("nse", "yahoo")


def _is_live(src: str) -> bool:
    return (src or "") == "nse" or (src or "").startswith("yahoo") and src != "yahoo-adj"


def inspect_bars(bars: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    out = {}
    for s, bl in bars.items():
        srcs = sorted({str(b.get("source", "?")) for b in bl})
        live = [b for b in bl if _is_live(str(b.get("source", "")))]
        out[s] = {"n": len(bl), "sources": srcs, "n_live": len(live),
                  "mixed": any("yahoo-adj" in x for x in srcs) and bool(live),
                  "last_source": str(bl[-1].get("source", "?")) if bl else "?"}
    return out


def gate(bars: Dict[str, List[Dict]], cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = cfg or {}
    min_bars = int(cfg.get("quality_min_bars", cfg.get("min_history_bars", 60)))
    min_syms = int(cfg.get("quality_min_symbols", 2))
    strict_mix = bool(cfg.get("quality_strict_mix", False))
    trimmed, dropped_forming = {}, 0
    for s, bl in bars.items():
        bl = list(bl)
        if bl and _is_live(str(bl[-1].get("source", ""))):
            bl = bl[:-1]  # possibly-forming live bar: not closed, never researched
            dropped_forming += 1
        trimmed[s] = bl
    kept, excluded = {}, {}
    for s, bl in trimmed.items():
        if len(bl) < min_bars:
            excluded[s] = f"short({len(bl)})"
            continue
        srcs = {str(b.get("source", "?")) for b in bl}
        if strict_mix and any("yahoo-adj" in x for x in srcs) and any(_is_live(x) for x in srcs):
            excluded[s] = "adj-mix"
            continue
        kept[s] = bl
    info = inspect_bars(bars)
    mixed = sorted(s for s, v in info.items() if v["mixed"])
    ok = len(kept) >= min_syms
    return {"ok": ok, "bars": kept, "excluded": excluded, "mixed": mixed,
            "dropped_forming": dropped_forming,
            "reason": "" if ok else f"INSUFFICIENT_DATA kept={len(kept)}<{min_syms}"}
