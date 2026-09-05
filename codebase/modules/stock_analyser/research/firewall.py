"""Research firewall (stdlib): provenance fingerprints + execution-layer seal binding.

Every candidate carries DATASET_ID / DATA_HASH / FEATURE_SET_HASH /
MODEL_CONFIG_HASH / CODE_VERSION / RANDOM_SEED in the ledger. The OOS seal is
bound to (strategy_hash, dataset, code): re-validating sealed material on
different data/code, or mutating after seal, is REJECTed here — in the
execution layer, not just workflow convention — so revealed OOS can never
steer ranking, mutation, or allocation down the same lineage.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any, Dict


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def fingerprints(strategy_d: Dict[str, Any], seed: Any, dataset_id: str,
                 data_hash: str, code_version: str) -> Dict[str, str]:
    m = strategy_d.get("meta", {}) or {}
    is_ml = m.get("family") == "ml"
    if is_ml:
        feats = sorted(m.get("features", []) or [])
        model_cfg = {"model": m.get("model"), "top_n": m.get("top_n"),
                     "max_depth": m.get("max_depth")}
    else:
        feats = sorted((strategy_d.get("features", {}) or {}).keys())
        model_cfg = {"stop_atr": strategy_d.get("stop_atr"),
                     "take_atr": strategy_d.get("take_atr"),
                     "max_hold": strategy_d.get("max_hold"),
                     "position_frac": strategy_d.get("position_frac"),
                     "max_positions": strategy_d.get("max_positions")}
    return {"feature_set_hash": _h(feats), "model_config_hash": _h(model_cfg),
            "random_seed": str(seed), "dataset_id": str(dataset_id),
            "data_hash": str(data_hash), "code_version": str(code_version)}


def check_seal_binding(cand_d: Dict[str, Any], data_hash: str,
                       code_version: str) -> str | None:
    """None if clean, else REJECT reason. Sealed material is frozen to data+code."""
    seal = (cand_d.get("meta", {}) or {}).get("oos_seal") or {}
    if not seal:
        return None
    if seal.get("data_hash", "") not in ("", data_hash):
        return "SEAL_DATA_CHANGED"
    if seal.get("code_version", "") not in ("", code_version):
        return "SEAL_CODE_CHANGED"
    return "MUTATED_AFTER_SEAL"  # sealed lineage re-entering validation: new lineage required
