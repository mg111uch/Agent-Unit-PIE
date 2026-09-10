"""Genome: mutate a strategy deterministically (no LLM-side code exec)."""
from __future__ import annotations
import copy
import random
from typing import Any, Dict
from .model import Strategy

MUTATIONS = ("threshold", "lookback", "exit", "hold", "position", "timeframe", "feature_scale")

ML_MUTATIONS = ("top_n", "depth", "exit", "hold", "position", "features", "model")

ML_DEFAULTS = {"model": "hgb", "top_n": 5, "max_depth": 3, "stop_atr": 2.0, "take_atr": 4.0,
               "max_hold": 10, "position_frac": 0.2, "max_positions": 3}

ML_MODELS = ("hgb", "rf", "ridge")


def ml_seed(universe: str = "MY_UNIVERSE_200", top_n: int = 5) -> Dict[str, Any]:
    from ..ml.dataset import FEATURES, REL_FEATURES
    return {"name": "ml_ranker", "universe": universe, "timeframe": "1D",
            "flat_cost": 0.0,
            "meta": {"family": "ml", "model": "hgb", "top_n": top_n, "max_depth": 3,
                     "features": list(FEATURES) + list(REL_FEATURES), **{k: v for k, v in ML_DEFAULTS.items()
                                                     if k not in ("model", "top_n", "max_depth")}}}


def mutate_ml(strategy_d: Dict[str, Any], seed: int = 0, kind: str | None = None) -> Dict[str, Any]:
    import random as _r
    rng = _r.Random(seed)
    kind = kind or rng.choice(ML_MUTATIONS)
    d = copy.deepcopy(strategy_d)
    m = d.setdefault("meta", {})
    if kind == "top_n":
        m["top_n"] = int(max(2, min(10, m.get("top_n", 5) + rng.choice([-2, -1, 1, 2]))))
    elif kind == "depth":
        m["max_depth"] = int(max(2, min(5, m.get("max_depth", 3) + rng.choice([-1, 1]))))
    elif kind == "exit":
        m["stop_atr"] = round(max(0.5, m.get("stop_atr", 2.0) + rng.uniform(-0.5, 0.5)), 2)
        m["take_atr"] = round(max(1.0, m.get("take_atr", 4.0) + rng.uniform(-1.0, 1.0)), 2)
    elif kind == "hold":
        m["max_hold"] = max(2, m.get("max_hold", 10) + rng.choice([-3, -1, 2, 3]))
    elif kind == "position":
        m["position_frac"] = round(max(0.05, min(0.5, m.get("position_frac", 0.2)
                                                 + rng.uniform(-0.05, 0.05))), 3)
        m["max_positions"] = max(1, min(8, m.get("max_positions", 3) + rng.choice([-1, 1])))
    elif kind == "features":
        from ..ml.dataset import FEATURES, REL_FEATURES
        pool = list(FEATURES) + list(REL_FEATURES)
        cur = m.get("features", pool)
        if len(cur) > 5 and rng.random() < 0.7:
            cur = [f for f in cur if f != rng.choice(cur)]
        else:
            cur = list(pool)
        m["features"] = cur
    elif kind == "model":
        cur = m.get("model", "hgb")
        opts = [x for x in ML_MODELS if x != cur] or list(ML_MODELS)
        m["model"] = rng.choice(opts)
    d["name"] = f"{d.get('name', 'ml_ranker')}~{kind}{seed}"
    m["parent"] = strategy_d.get("name", "ml_ranker")
    m["mutation"] = kind
    m.pop("oos_seal", None)  # new lineage: hard-seal cleared
    return d


def _walk_numbers(expr: Any, fn) -> Any:
    if isinstance(expr, dict):
        if "const" in expr and isinstance(expr["const"], (int, float)):
            return {"const": fn(float(expr["const"]))}
        return {"op": expr.get("op"), "args": [_walk_numbers(a, fn) for a in expr.get("args", [])]} \
            if "op" in expr else dict(expr)
    return expr


def mutate(strategy: Strategy, seed: int = 0, kind: str | None = None) -> Strategy:
    rng = random.Random(seed)
    kind = kind or rng.choice(MUTATIONS)
    d: Dict[str, Any] = copy.deepcopy(strategy.to_dict())
    if kind == "threshold":
        f = rng.uniform(0.85, 1.18)
        d["entry"] = _walk_numbers(d["entry"], lambda x: round(x * f, 4) if x not in (20,) else x)
    elif kind == "lookback":
        def bump(x: float) -> float:
            return float(max(2, min(120, int(x + rng.choice([-5, 5, 10, -10]))))) if x >= 2 else x
        d["entry"] = _walk_numbers(d["entry"], bump)
    elif kind == "exit":
        d["stop_atr"] = round(max(0.5, strategy.stop_atr + rng.uniform(-0.5, 0.5)), 2)
        d["take_atr"] = round(max(1.0, strategy.take_atr + rng.uniform(-1.0, 1.0)), 2)
    elif kind == "hold":
        d["max_hold"] = max(1, strategy.max_hold + rng.choice([-3, -1, 1, 3, 5]))
    elif kind == "position":
        d["position_frac"] = round(max(0.02, min(0.5, strategy.position_frac + rng.uniform(-0.03, 0.03))), 3)
    elif kind == "timeframe":
        d["timeframe"] = "15m" if strategy.timeframe == "1D" else "1D"
    elif kind == "feature_scale":
        f = rng.uniform(0.8, 1.25)
        d["features"] = {k: _walk_numbers(v, lambda x: round(x * f, 4)) for k, v in strategy.features.items()}
    d["name"] = f"{strategy.name}~{kind}{seed}"
    d["meta"] = {**(strategy.meta or {}), "parent": strategy.name, "mutation": kind}
    d["meta"].pop("oos_seal", None)  # new lineage: hard-seal cleared
    from .model import strategy_from_dict
    return strategy_from_dict(d)
