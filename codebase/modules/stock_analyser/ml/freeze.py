"""Freeze a scoring model so shadow IC is measured on ONE model, not a drifting one.

JSON (not pickle): auditable, diff-able, no code execution on load.  Ridge only (coef + intercept + feature order);
inputs are expected to be the same per-date rank-gauss features used in training.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

import numpy as np

DDL = """CREATE TABLE IF NOT EXISTS model_artifacts(
  name TEXT, version TEXT, created_utc TEXT, sha256 TEXT, payload TEXT, PRIMARY KEY(name, version))"""


def freeze_ridge(db: str, name: str, feats, coef, intercept: float, meta: dict) -> str:
    payload = json.dumps(
        dict(feats=list(feats), coef=[float(c) for c in coef], intercept=float(intercept), meta=meta), sort_keys=True
    )
    sha = hashlib.sha256(payload.encode()).hexdigest()
    version = sha[:12]
    con = sqlite3.connect(db)
    con.execute(DDL)
    # INSERT OR IGNORE: an identical artifact is idempotent; a changed one gets a new version, never overwrites
    con.execute(
        "INSERT OR IGNORE INTO model_artifacts VALUES(?,?,?,?,?)",
        (name, version, datetime.now(timezone.utc).isoformat(), sha, payload),
    )
    con.commit()
    con.close()
    return version


def load_ridge(db: str, name: str, version: str | None = None):
    con = sqlite3.connect(db)
    q = "SELECT version, sha256, payload FROM model_artifacts WHERE name=?" + (" AND version=?" if version else " ORDER BY created_utc DESC LIMIT 1")
    row = con.execute(q, (name, version) if version else (name,)).fetchone()
    con.close()
    if row is None:
        raise KeyError(f"no artifact {name} {version or ''}")
    v, sha, payload = row
    if hashlib.sha256(payload.encode()).hexdigest() != sha:
        raise ValueError("artifact payload does not match stored hash (tampered or corrupted)")
    p = json.loads(payload)
    coef, b, feats = np.asarray(p["coef"]), p["intercept"], p["feats"]
    return v, feats, (lambda X: np.nan_to_num(np.asarray(X)) @ coef + b)


class FrozenRidge:
    """Hash-verified ridge artifact as a ranker-compatible model.

    Wraps load_ridge so shadow scoring reuses ONE frozen model instead of
    retraining daily (which silently contaminates shadow IC). predict()
    matches the sklearn ranker contract used by ml/ranker.add_scores.
    """

    def __init__(self, db: str, name: str, version: str | None = None):
        v, feats, fn = load_ridge(db, name, version)
        self.version = v
        self.feats_ = list(feats)
        self.model_name_ = "ridge-frozen"
        self.top_n_ = 5
        self._fn = fn

    def predict(self, X):
        return self._fn(X)


def freeze_sklearn_ridge(db: str, name: str, model, meta: dict) -> str:
    """Freeze a trained sklearn Ridge (coef_/intercept_/feats_) to SQLite."""
    feats = list(getattr(model, "feats_", []))
    coef = getattr(model, "coef_", None)
    if coef is None or not feats:
        raise ValueError("not a fitted ridge with feats_")
    coef = np.asarray(coef).ravel()
    if coef.shape[0] != len(feats):
        raise ValueError("coef/feats length mismatch")
    return freeze_ridge(db, name, feats, coef, float(getattr(model, "intercept_", 0.0)), meta)


def frozen_name(strategy_name: str) -> str:
    return f"shadow:{strategy_name}"
