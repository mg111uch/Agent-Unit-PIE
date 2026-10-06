"""Honest gate: block-bootstrap excess-return test + trial deflation (stdlib).

Nets fed in are already net of execution costs, so a lower confidence bound
above zero IS edge above the cost drag. Weekly blocks approximate independent
5-day cross-sections; empty weeks count as 0 (no cherry-picking active weeks).
Trial deflation: alpha = 0.05 / (# prior candidates on the same dataset_id).
"""
from __future__ import annotations
import random
from datetime import date
from typing import Any, Dict, List

MIN_PERIODS = 30


def _week(ts: str) -> str:
    try:
        d = date.fromisoformat((ts or "")[:10])
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    except Exception:
        return ""


def _weeks_between(w0: str, w1: str) -> List[str]:
    try:
        y0, n0 = int(w0[:4]), int(w0[-2:])
        y1, n1 = int(w1[:4]), int(w1[-2:])
        d = date.fromisocalendar(y0, n0, 1)
        end = date.fromisocalendar(y1, n1, 1)
        out = []
        while d <= end:
            y, w, _ = d.isocalendar()
            out.append(f"{y}-W{w:02d}")
            d = date.fromordinal(d.toordinal() + 7)
        return out
    except Exception:
        return [w0, w1]


def trial_count(dataset_id: str = "", db_path: str | None = None) -> int:
    if not dataset_id:
        return 1
    try:
        from ..data.store import connect
        con = connect(db_path)
        try:
            n = con.execute("SELECT COUNT(*) FROM research_candidates"
                            " WHERE dataset_id=?", (dataset_id,)).fetchone()[0]
        finally:
            con.close()
        return max(1, int(n or 0))
    except Exception:
        return 1


def excess_gate(trades: List[Dict[str, Any]], dataset_id: str = "",
                db_path: str | None = None, seed: int = 7,
                reps: int = 2000, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Block-bootstrap the weekly block-mean net. Pass iff >= MIN_PERIODS
    weeks spanned AND the deflated lower bound stays above zero."""
    cfg = cfg or {}
    need = int(cfg.get("excess_min_periods", MIN_PERIODS))
    wk: Dict[str, float] = {}
    for t in trades or []:
        w = _week(str(t.get("t_out") or t.get("t_in") or ""))
        if w:
            wk[w] = wk.get(w, 0.0) + float(t.get("net") or 0.0)
    out: Dict[str, Any] = {"pass": False, "periods": 0, "trials": 1,
                            "mean": 0.0, "lower": 0.0}
    if not wk:
        out["reason"] = "NO_TRADES"
        return out
    weeks = _weeks_between(min(wk), max(wk))
    blocks = [wk.get(w, 0.0) for w in weeks]
    out["periods"] = len(blocks)
    if len(blocks) < need:
        out["reason"] = f"THIN_SAMPLE({len(blocks)}<{need})"
        return out
    trials = trial_count(dataset_id, db_path)
    out["trials"] = trials
    alpha = 0.05 / max(1, trials)
    lo_pct = max(alpha / 2 * 100.0, 100.0 / max(1, reps))
    rng = random.Random(seed)
    mean = sum(blocks) / len(blocks)
    boot = []
    for _ in range(max(100, reps)):
        s = sum(blocks[rng.randrange(len(blocks))] for _ in range(len(blocks)))
        boot.append(s / len(blocks))
    boot.sort()
    lower = boot[max(0, min(len(boot) - 1, int(len(boot) * lo_pct / 100.0)))]
    out.update(mean=round(mean, 2), lower=round(lower, 2), alpha=round(alpha, 6))
    out["pass"] = bool(lower > 0)
    if not out["pass"]:
        out["reason"] = "WEAK_EXCESS"
    return out
