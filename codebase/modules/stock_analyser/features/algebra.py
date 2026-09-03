"""Feature algebra: LLM emits expressions (dicts), kernel evaluates deterministically.

Expr forms: {"field": "close"} | {"const": 2.0} | {"op": "rolling_mean", "args": [expr, {"const": 20}]}
Bool exprs for entry: {"op": "gt", "args": [a, b]}, and/or/not.
Series are plain float lists; None = insufficient history (propagates).
"""
from __future__ import annotations
import math
from typing import Dict, List, Any

ALLOWED_OPS = ("lag", "diff", "rolling_mean", "rolling_std", "rolling_min",
               "rolling_max", "rank", "zscore", "percentile", "correlation",
               "covariance", "slope", "ratio", "abs", "log", "gt", "lt", "gte",
               "lte", "and", "or", "not", "add", "sub", "mul", "div")

FIELDS = ("open", "high", "low", "close", "volume", "oi", "iv", "bid", "ask", "returns")


def _num(x: Any) -> float | None:
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _mean(xs: List[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _std(xs: List[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _eval(expr: Any, cols: Dict[str, List[float | None]], i: int) -> float | bool | None:
    if isinstance(expr, (int, float)):
        return expr
    if not isinstance(expr, dict):
        return None
    if "const" in expr:
        return expr["const"]
    if "field" in expr:
        s = cols.get(expr["field"], [])
        return s[i] if 0 <= i < len(s) else None
    op, args = expr.get("op"), expr.get("args", [])
    if op == "lag":
        n = int(_num(_eval(args[1], cols, i)) or 0)
        base = args[0]
        if isinstance(base, dict) and "field" in base:
            s = cols.get(base["field"], [])
            j = i - n
            return s[j] if 0 <= j < len(s) else None
        v = _eval(base, cols, i - n)
        return v
    if op in ("gt", "lt", "gte", "lte"):
        a, b = _eval(args[0], cols, i), _eval(args[1], cols, i)
        if a is None or b is None:
            return None
        return {"gt": a > b, "lt": a < b, "gte": a >= b, "lte": a <= b}[op]
    if op == "and":
        vs = [_eval(a, cols, i) for a in args]
        if any(v is False for v in vs):
            return False
        return True if all(v is True for v in vs) else None
    if op == "or":
        vs = [_eval(a, cols, i) for a in args]
        if any(v is True for v in vs):
            return True
        return False if all(v is False for v in vs) else None
    if op == "not":
        v = _eval(args[0], cols, i)
        return (not v) if isinstance(v, bool) else None
    # numeric ops: evaluate arg series over window ending at i
    def series(e: Any, n: int) -> List[float | None]:
        return [_eval(e, cols, j) for j in range(i - n + 1, i + 1)]
    if op == "diff":
        a, b = _eval(args[0], cols, i), _eval(args[1], cols, i)
        return None if a is None or b is None else a - b
    if op in ("add", "sub", "mul", "div", "ratio"):
        a, b = _eval(args[0], cols, i), _eval(args[1], cols, i)
        if a is None or b is None:
            return None
        if op == "add":
            return a + b
        if op == "sub":
            return a - b
        if op == "mul":
            return a * b
        return None if b == 0 else a / b
    if op == "abs":
        v = _eval(args[0], cols, i)
        return None if v is None else abs(v)
    if op == "log":
        v = _eval(args[0], cols, i)
        return None if v is None or v <= 0 else math.log(v)
    # rolling ops need window
    n = int(_num(_eval(args[1], cols, i)) or 0) if len(args) > 1 else 0
    if n <= 0 or i - n + 1 < 0:
        return None
    w = series(args[0], n)
    if any(v is None for v in w):
        return None
    assert all(isinstance(v, (int, float)) for v in w)
    wf = [float(v) for v in w]  # type: ignore
    if op == "rolling_mean":
        return _mean(wf)
    if op == "rolling_std":
        return _std(wf)
    if op == "rolling_min":
        return min(wf)
    if op == "rolling_max":
        return max(wf)
    if op == "zscore":
        m, s = _mean(wf), _std(wf)
        cur = _eval(args[0], cols, i)
        if m is None or s is None or not s or cur is None:
            return None
        return (cur - m) / s
    if op == "rank":
        cur = _eval(args[0], cols, i)
        if cur is None:
            return None
        return sum(1 for v in wf if v <= cur) / len(wf)
    if op == "percentile":
        cur = _eval(args[0], cols, i)
        if cur is None:
            return None
        s2 = sorted(wf)
        return sum(1 for v in s2 if v <= cur) / len(s2)
    if op in ("correlation", "covariance"):
        if len(args) < 3:
            return None
        m2 = int(_num(_eval(args[2], cols, i)) or 0)
        if m2 <= 1 or i - m2 + 1 < 0:
            return None
        xs = [_eval(args[0], cols, j) for j in range(i - m2 + 1, i + 1)]
        ys = [_eval(args[1], cols, j) for j in range(i - m2 + 1, i + 1)]
        if any(v is None for v in xs + ys):
            return None
        xf = [float(v) for v in xs]  # type: ignore
        yf = [float(v) for v in ys]  # type: ignore
        mx, my = _mean(xf), _mean(yf)
        assert mx is not None and my is not None
        cov = sum((a - mx) * (b - my) for a, b in zip(xf, yf)) / (len(xf) - 1)
        if op == "covariance":
            return cov
        sx, sy = _std(xf), _std(yf)
        if not sx or not sy:
            return None
        return cov / (sx * sy)
    if op == "slope":
        xs = list(range(len(wf)))
        mx = _mean([float(x) for x in xs])
        my = _mean(wf)
        assert mx is not None and my is not None
        den = sum((x - mx) ** 2 for x in xs)
        return None if not den else sum((x - mx) * (y - my) for x, y in zip(xs, wf)) / den
    raise ValueError(f"unknown op: {op}")


def evaluate(expr: Any, cols: Dict[str, List[float | None]]) -> List[Any]:
    n = max((len(v) for v in cols.values()), default=0)
    return [_eval(expr, cols, i) for i in range(n)]


def columns_from_bars(bars: List[Dict[str, Any]]) -> Dict[str, List[float | None]]:
    cols: Dict[str, List[float | None]] = {f: [] for f in FIELDS}
    prev = None
    for b in bars:
        for f in ("open", "high", "low", "close", "volume"):
            cols[f].append(float(b[f]) if b.get(f) is not None else None)
        for f in ("oi", "iv", "bid", "ask"):
            cols[f].append(float(b[f]) if b.get(f) is not None else None)
        c = cols["close"][-1]
        cols["returns"].append(None if prev is None or c is None or prev == 0
                               else (c - prev) / prev)
        prev = c if c is not None else prev
    return cols


def validate_expr(expr: Any, depth: int = 0) -> str | None:
    """Return error string or None if valid."""
    if depth > 8:
        return "expression too deep"
    if isinstance(expr, (int, float)):
        return None
    if not isinstance(expr, dict):
        return "expr must be dict or number"
    if "const" in expr or "field" in expr:
        if "field" in expr and expr["field"] not in FIELDS:
            return f"unknown field {expr['field']}"
        return None
    if expr.get("op") not in ALLOWED_OPS:
        return f"unknown op {expr.get('op')}"
    for a in expr.get("args", []):
        e = validate_expr(a, depth + 1)
        if e:
            return e
    return None
