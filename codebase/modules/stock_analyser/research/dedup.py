"""Dedup-before-screen: cross-run exact-hash probe (1 indexed SELECT, no backtest).

Revisits are recorded as DUPLICATE (visible in ledger) instead of silently
burning budget. New hashes still pay for alpha_gate → quick_screen → full
validation in run_job.
"""
from __future__ import annotations


def seen_global(h: str, db_path: str | None = None) -> bool:
    try:
        from .job import _con
        con = _con(db_path)
        try:
            return con.execute("SELECT 1 FROM research_candidates WHERE strategy_hash=?"
                               " LIMIT 1", (h,)).fetchone() is not None
        finally:
            con.close()
    except Exception:
        return False


def record_dup(rid: str, h: str, cand_d: dict, fam: str, kind: str, mode: str,
               db_path: str | None, data_hash: str, code_ver: str,
               dataset_id: str, seed_i: int) -> dict:
    """Exact-hash revisit ledger write (no backtest). Returns the result row."""
    from .job import _record
    from .firewall import fingerprints as _fps0
    _fp = _fps0(cand_d, seed_i, dataset_id, data_hash, code_ver)
    _record(rid, h, cand_d, fam, kind, "DUPLICATE", None, None, 0.0, db_path,
            data_hash, code_ver, _fp["feature_set_hash"], _fp["model_config_hash"],
            _fp["random_seed"], _fp["dataset_id"], "")
    return {"strategy": cand_d.get("name"), "mutation": kind, "verdict": "DUPLICATE",
            "alloc": mode, "avg_net": None, "oos_net": None,
            "summary": "dedup-before-screen"}
