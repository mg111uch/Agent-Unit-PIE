"""Model family interface: interchangeable rankers over the same panel target.

Target stays rank(fwd_ret) via top-N cross-sectional policy (rank, don't classify).
Models: hgb (default), rf, ridge. Same train/predict contract; attribution helper
for findings (built-in importances, else +/-corr fallback, stdlib).
"""
from __future__ import annotations
from typing import Any, Dict, List

MODELS = ("hgb", "rf", "ridge")

_DEFAULTS = {
    "hgb": {"max_depth": 3, "learning_rate": 0.05, "max_iter": 200,
            "l2_regularization": 1.0, "random_state": 7},
    "rf": {"n_estimators": 200, "max_depth": 6, "min_samples_leaf": 20,
           "random_state": 7, "n_jobs": -1},
    "ridge": {"alpha": 1.0},
}


def defaults(model: str) -> Dict[str, Any]:
    return dict(_DEFAULTS.get(model, _DEFAULTS["hgb"]))


def train(model: str, train_df, feats: List[str], top_n: int = 5, **overrides):
    model = model if model in MODELS else "hgb"
    feats = [f for f in feats if f in train_df.columns] or list(train_df.columns)
    X = train_df[feats].to_numpy(dtype=float)
    y = train_df["fwd_ret"].to_numpy(dtype=float)
    if model == "rf":
        from sklearn.ensemble import RandomForestRegressor
        p = {**_DEFAULTS["rf"], **overrides}
        depth = overrides.get("max_depth", p["max_depth"])
        p.update({"max_depth": depth})
        est = RandomForestRegressor(**{k: v for k, v in p.items()
                                       if k in ("n_estimators", "max_depth", "min_samples_leaf",
                                                "random_state", "n_jobs")})
    elif model == "ridge":
        from sklearn.linear_model import Ridge
        est = Ridge(alpha=float(overrides.get("alpha", 1.0)))
    else:
        from sklearn.ensemble import HistGradientBoostingRegressor
        p = {**_DEFAULTS["hgb"], **overrides}
        est = HistGradientBoostingRegressor(**{k: v for k, v in p.items()
                                               if k in _DEFAULTS["hgb"]})
    est.fit(X, y)
    est.model_name_ = model
    est.feats_ = list(feats)
    est.top_n_ = top_n
    return est


def attribution(model, df, feats: List[str], cap: int = 500) -> List[Dict[str, Any]]:
    """Top contributing features for findings. Built-in importances preferred."""
    feats = [f for f in feats if f in df.columns]
    if not feats or len(df) == 0:
        return []
    imp = getattr(model, "feature_importances_", None)
    if imp is not None and len(imp) == len(feats):
        order = sorted(zip(feats, map(float, imp)), key=lambda t: -t[1])
        return [{"feature": f, "importance": round(v, 4)} for f, v in order[:8]]
    try:  # permutation fallback on subsample (cheap, model-agnostic)
        import numpy as np
        from sklearn.metrics import mean_squared_error
        sub = df.sample(min(cap, len(df)), random_state=7)
        X = sub[feats].to_numpy(dtype=float)
        y = sub["fwd_ret"].to_numpy(dtype=float)
        base = mean_squared_error(y, model.predict(X))
        out = []
        rng = np.random.RandomState(7)
        for j, f in enumerate(feats):
            Xs = X.copy()
            rng.shuffle(Xs[:, j])
            drop = mean_squared_error(y, model.predict(Xs)) - base
            out.append({"feature": f, "importance": round(float(drop), 6)})
        return sorted(out, key=lambda d: -d["importance"])[:8]
    except Exception:
        return [{"feature": f, "importance": 0.0} for f in feats[:8]]
