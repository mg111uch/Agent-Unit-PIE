"""Kernel bridge: signals + sim_stock findings + run shards. Best-effort kernel imports."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from .constants import SIM_NAME, TOPIC

STATUSES = ("HYPOTHESIS", "SUPPORTED", "ROBUST", "REFUTED", "REGIME_DEPENDENT",
            "INSUFFICIENT_DATA", "SUPERSEDED")


def _ws_root() -> Path:
    return Path(__file__).resolve().parents[3]  # .../Agentic_Unit_PIE


def shard_dir(run_id: str) -> Path:
    p = _ws_root() / "data" / "units" / "simulations" / SIM_NAME / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_shard(run_id: str, params: Dict, signals: List[Dict], summary: Dict) -> str:
    d = shard_dir(run_id)
    (d / "params.yaml").write_text(json.dumps(params, indent=1))
    (d / "signals.json").write_text(json.dumps(signals, indent=1))
    (d / "summary.json").write_text(json.dumps(summary, indent=1))
    return str(d)


def prune_shards(keep: int = 50, root=None) -> Dict[str, int]:
    """Keep newest `keep` successful shards; delete older + errored ones.

    Successful = summary.json parses and has no 'error' verdict. Ledger in
    market.db remains the complete record; shards are just the recent window.
    """
    import shutil
    root = root or (_ws_root() / "data" / "units" / "simulations" / SIM_NAME)
    if not root.is_dir():
        return {"kept": 0, "deleted": 0}
    dirs = sorted([d for d in root.iterdir() if d.is_dir()],
                  key=lambda d: d.stat().st_mtime)
    good, bad = [], []
    for d in dirs:
        try:
            s = json.loads((d / "summary.json").read_text())
            (good if "error" not in json.dumps(s)[:500].lower() else bad).append(d)
        except Exception:
            bad.append(d)
    keep_ids = {d.name for d in good[-keep:]}
    deleted = 0
    for d in dirs:
        if d.name not in keep_ids:
            shutil.rmtree(d, ignore_errors=True)
            deleted += 1
    return {"kept": len(keep_ids), "deleted": deleted}


def emit_signals(run_id: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    sigs: List[Dict[str, Any]] = []
    if (metrics.get("n", 0) or 0) >= 20 and (metrics.get("sharpe", 0) or 0) > 0.5:
        sigs.append({"signal_type": "strategy_edge", "value": metrics["sharpe"], "run_id": run_id})
    if (metrics.get("max_dd", 0) or 0) < -0.25:
        sigs.append({"signal_type": "drawdown_breach", "value": metrics["max_dd"], "run_id": run_id})
    try:
        from kernel.signals.signal_engine import signal_engine
        for s in sigs:
            try:
                signal_engine.emit(s["signal_type"], s["value"],
                                   metadata={"simulator": SIM_NAME, "run_id": run_id})
            except Exception:
                pass
    except Exception:
        pass
    return sigs


def register_episode_finding(summary: Dict[str, Any]) -> Dict[str, Any]:
    """P17: one kernel finding per research episode (not per candidate)."""
    ep = summary.get("episode", "?")
    n, ready = summary.get("tested", 0), summary.get("n_paper_ready", 0)
    status = "SUPPORTED" if ready else ("REFUTED" if summary.get("status") == "ALL_RETIRED"
                                        else "HYPOTHESIS")
    claim = (f"Stock episode {ep}: {n} candidates on {summary.get('universe','?')} "
             f"→ {ready} PAPER_READY {summary.get('paper_ready', [])[:5]}; "
             f"verdicts {summary.get('verdicts', {})}; families {summary.get('families', {})}")
    return register_finding(claim, [ep], {"tested": n, "paper_ready": ready,
                                          "verdicts": summary.get("verdicts", {})},
                            universe=summary.get("universe", ""), status=status)


def register_finding(claim: str, experiments: List[str], metrics: Dict[str, Any],
                     universe: str = "", timeframe: str = "1D",
                     status: str = "HYPOTHESIS") -> Dict[str, Any]:
    if status not in STATUSES:
        status = "HYPOTHESIS"
    node = {"title": claim[:120], "content": claim,
            "experiments": experiments, "metrics": metrics, "universe": universe,
            "timeframe": timeframe, "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(), "topic": TOPIC}
    try:
        from modules.argu_god.engine import topic_store as ts
        nid = f"stock_{experiments[0]}" if experiments else f"stock_{abs(hash(claim)) % 10**8}"
        node_dict = {"name": nid, "premise": claim[:500], "type": "simulation_observation",
                     "metadata": {"experiments": experiments, "metrics": metrics,
                                  "universe": universe, "timeframe": timeframe,
                                  "status": status, "simulator": SIM_NAME}}
        res = ts.add_node(TOPIC, node_dict)
        node["node_id"] = nid
        node["store_result"] = res.get("kind", "") if isinstance(res, dict) else ""
    except Exception as e:
        node["node_id"] = ""
        node["kernel_error"] = str(e)[:200]
    try:
        from kernel.persistence import db as kdb
        if hasattr(kdb, "ensure_schema"):
            kdb.ensure_schema()
    except Exception:
        pass
    return node
