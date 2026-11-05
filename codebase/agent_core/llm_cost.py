"""LLM spend accounting (OPS-07).

Two controls, both per **task** (a conversation/job), not per process:

- `Budget`: a token and ₹ ceiling checked before each call, so a runaway loop
  stops instead of discovering the bill later.
- `CostLog`: SQLite rows (`data/logs/llm_cost.db`) with provider, model,
  tokens, INR and task id, so `unit_economics` can include AI cost.

Prices are configurable (`LLM_PRICING_JSON`) because provider rates move; the
defaults are only estimates and every row stores the rate it used.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data"


def _data_root() -> Path:
    return Path(os.environ.get("PIE_DATA_ROOT", str(_DEFAULT_ROOT)))


# INR per 1k tokens: {"<model>": {"in_per_1k": x, "out_per_1k": y}}
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.0-flash": {"in_per_1k": 0.03, "out_per_1k": 0.12},
    "gemini-1.5-flash": {"in_per_1k": 0.03, "out_per_1k": 0.12},
    "gpt-4o-mini": {"in_per_1k": 0.06, "out_per_1k": 0.24},
    "claude-3-5-haiku": {"in_per_1k": 0.35, "out_per_1k": 1.75},
    "_default": {"in_per_1k": 0.10, "out_per_1k": 0.40},
}


def pricing() -> Dict[str, Dict[str, float]]:
    raw = os.environ.get("LLM_PRICING_JSON")
    if not raw:
        return DEFAULT_PRICING
    try:
        merged = dict(DEFAULT_PRICING)
        merged.update(json.loads(raw))
        return merged
    except (ValueError, TypeError):
        return DEFAULT_PRICING


def price(model: str, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
    table = pricing()
    rate = table.get(model) or table.get("_default")
    inr = (max(0, input_tokens) / 1000.0) * rate["in_per_1k"] + \
          (max(0, output_tokens) / 1000.0) * rate["out_per_1k"]
    return {"inr": round(inr, 4), "rate": dict(rate), "model": model}


def _split(usage: Dict[str, Any]) -> tuple:
    """Accept both provider shapes: prompt/completion or input/output."""
    i = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    o = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    if not i and not o:
        total = int(usage.get("total_tokens") or 0)
        return total, 0
    return i, o


class CostLog:
    """Append-only spend ledger. One SQLite path, no second store."""

    def __init__(self, db_path: Optional[str] = None):
        import sqlite3
        path = db_path or str(_data_root() / "logs" / "llm_cost.db")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS llm_cost ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " ts TEXT NOT NULL,"
            " task_id TEXT NOT NULL,"
            " provider TEXT NOT NULL DEFAULT '',"
            " model TEXT NOT NULL DEFAULT '',"
            " input_tokens INTEGER NOT NULL DEFAULT 0,"
            " output_tokens INTEGER NOT NULL DEFAULT 0,"
            " inr REAL NOT NULL DEFAULT 0,"
            " rate TEXT NOT NULL DEFAULT '{}'"
            ")")
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_cost_task ON llm_cost(task_id)")
        self._conn.commit()

    def record(self, task_id: str, usage: Dict[str, Any],
               provider: str = "", model: str = "",
               budget: Optional["Budget"] = None) -> Dict[str, Any]:
        i, o = _split(usage or {})
        p = price(model, i, o)
        total = i + o
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT INTO llm_cost (ts, task_id, provider, model,"
                " input_tokens, output_tokens, inr, rate)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (now, str(task_id), provider or "", model or "", i, o,
                 p["inr"], json.dumps(p["rate"])))
            self._conn.commit()
        out = {"task_id": str(task_id), "tokens": total, "inr": p["inr"],
               "model": model, "provider": provider}
        if budget:
            out["budget"] = budget.add(total, p["inr"])
        return out

    def task_totals(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS calls, COALESCE(SUM(input_tokens),0) AS i,"
                " COALESCE(SUM(output_tokens),0) AS o,"
                " COALESCE(SUM(inr),0) AS inr"
                " FROM llm_cost WHERE task_id = ?", (str(task_id),)).fetchone()
        return {"task_id": str(task_id), "calls": row[0], "tokens": row[1] + row[2],
                "input_tokens": row[1], "output_tokens": row[2],
                "inr": round(row[3], 4)}

    def summary(self, limit: int = 20) -> Dict[str, Any]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT task_id, COUNT(*), SUM(input_tokens), SUM(output_tokens),"
                " SUM(inr) FROM llm_cost GROUP BY task_id"
                " ORDER BY SUM(inr) DESC LIMIT ?", (limit,)).fetchall()
        tasks = [{"task_id": r[0], "calls": r[1], "tokens": (r[2] or 0) + (r[3] or 0),
                  "inr": round(r[4] or 0, 4)} for r in rows]
        return {"tasks": tasks,
                "total_inr": round(sum(t["inr"] for t in tasks), 4)}


class Budget:
    """Per-task ceiling; `add()` returns the verdict after the spend."""

    def __init__(self, max_tokens: int = 0, max_inr: float = 0.0):
        self.max_tokens = int(max_tokens or 0)
        self.max_inr = float(max_inr or 0.0)
        self.tokens = 0
        self.inr = 0.0

    @classmethod
    def from_env(cls) -> "Budget":
        return cls(int(os.environ.get("LLM_TASK_BUDGET_TOKENS", "0") or 0),
                   float(os.environ.get("LLM_TASK_BUDGET_INR", "0") or 0))

    def add(self, tokens: int, inr: float) -> Dict[str, Any]:
        self.tokens += max(0, int(tokens))
        self.inr = round(self.inr + max(0.0, float(inr)), 4)
        over_tokens = bool(self.max_tokens) and self.tokens > self.max_tokens
        over_inr = bool(self.max_inr) and self.inr > self.max_inr
        return {"ok": not (over_tokens or over_inr),
                "over_tokens": over_tokens, "over_inr": over_inr,
                "tokens": self.tokens, "inr": self.inr,
                "max_tokens": self.max_tokens, "max_inr": self.max_inr}

    def exceeded(self) -> bool:
        return (bool(self.max_tokens) and self.tokens >= self.max_tokens) or \
               (bool(self.max_inr) and self.inr >= self.max_inr)


_default_log: Optional[CostLog] = None
_log_lock = threading.Lock()


def log() -> CostLog:
    global _default_log
    with _log_lock:
        if _default_log is None:
            _default_log = CostLog()
        return _default_log


def record_call(task_id: str, usage: Dict[str, Any], provider: str = "",
                model: str = "", budget: Optional[Budget] = None,
                enabled: Optional[bool] = None) -> Dict[str, Any]:
    """Best-effort hook for the agent loop: a logging error never stops a run."""
    if enabled is None:
        enabled = os.environ.get("LLM_COST_LOG", "1") not in ("0", "false", "off")
    if not enabled:
        return {"skipped": True}
    try:
        return log().record(task_id, usage, provider, model, budget)
    except Exception as e:  # accounting must never break the conversation
        return {"error": f"{type(e).__name__}: {e}"}
