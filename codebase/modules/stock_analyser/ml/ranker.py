"""Cross-sectional ranker over trailing primitives (rank fwd_ret, top-N policy).

Model family dispatches via ml/family.py (hgb default, rf, ridge); defaults stay
fixed — no tuning grid (deliberate anti-overfit choice at this data scale).
Artifacts pickle to run shards.
"""
from __future__ import annotations
from typing import Any, Dict, List
from .dataset import FEATURES
from .family import train as _train_family, attribution as _attribution, MODELS

FEATS = list(FEATURES)
DEFAULTS = {"max_depth": 3, "learning_rate": 0.05, "max_iter": 200,
            "l2_regularization": 1.0, "random_state": 7}


def train_ranker(train_df, top_n: int = 5, model: str = "hgb", feats=None, **overrides):
    cols = list(getattr(train_df, "columns", FEATS))
    use = [f for f in (feats or FEATS) if f in cols] or [f for f in FEATS if f in cols]
    if model not in MODELS:
        model = "hgb"
    params = {**DEFAULTS, **overrides} if model == "hgb" else dict(overrides)
    return _train_family(model, train_df, use, top_n=top_n, **params)


def attribution(model, df, feats: List[str] | None = None):
    use = feats or getattr(model, "feats_", FEATS)
    return _attribution(model, df, list(use))


def add_scores(model, df):
    out = df.copy()
    feats = list(getattr(model, "feats_", FEATS))
    use = [f for f in feats if f in df.columns]
    out["score"] = model.predict(df[use].to_numpy(dtype=float))
    return out


def top_n_signals(scored_df, bars_by_symbol: Dict[str, List[Dict]],
                  top_n: int = 5, live_from: str = "") -> Dict[str, List[bool]]:
    """Per-symbol bool lists aligned to each symbol's bars.

    A symbol scores True on date d iff ranked in that day's top-N by a score
    computed from trailing-only features at d. `live_from`: signals before
    this date forced False (honest OOS evaluation).
    """
    daily_top: Dict[str, set] = {}
    for ts, grp in scored_df.groupby("ts"):
        top = grp.nlargest(min(top_n, len(grp)), "score")["symbol"]
        daily_top[str(ts)] = set(top.tolist())
    out = {}
    for s, bars in bars_by_symbol.items():
        sl = []
        for b in bars:
            sl.append(bool(b["ts"] in daily_top and s in daily_top[b["ts"]]
                           and (not live_from or b["ts"] >= live_from)))
        out[s] = sl
    return out


def save_model(model, path: str) -> str:
    import pickle
    with open(path, "wb") as f:
        pickle.dump({"model": model, "top_n": getattr(model, "top_n_", 5),
                      "model_name": getattr(model, "model_name_", "hgb"),
                      "features": list(getattr(model, "feats_", FEATS))}, f)
    return path


def load_model(path: str):
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)
