"""StockConnector — develop_experiment interface for simulator='stock_analyser'.

params: {"strategy": <Strategy dict>, "dataset": "synthetic"|"csv",
         "symbols": [...], "n": int, "timeframe": "1D"|"15m", "seed": int}
run_id: 'run_basic' or 'run_policy_<param><int>' (existing validator).
"""
from __future__ import annotations
import json
from typing import Any, Dict, List
from .constants import SIM_NAME
from .data import store as S
from .data.universe import resolve_universe
from .data.providers import SyntheticProvider
from .strategies.model import strategy_from_dict
from .backtest.engine import run_backtest
from . import kernel_bridge as KB


class StockConnector:
    def __init__(self, simulator: str = SIM_NAME, db_path: str | None = None):
        self.simulator = simulator
        self.db_path = db_path
        self._params: Dict[str, Dict] = {}

    def _bars(self, p: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        ds = p.get("dataset", "synthetic")
        tf = p.get("timeframe", "1D")
        syms = p.get("symbols") or resolve_universe(p.get("universe", "MY_RESEARCH_UNIVERSE")) or ["RELIANCE"]
        n = int(p.get("n", 120))
        if ds == "csv":
            out = {}
            for s in syms:
                rows = S.query_equity(f"NSE:{s}", tf, db_path=self.db_path)
                out[s] = rows[-n:] if rows else []  # trailing window, not oldest
            return {s: v for s, v in out.items() if v}
        data = SyntheticProvider().fetch(syms, n=n, timeframe=tf,
                                         seed=int(p.get("seed", 7)), db_path=self.db_path,
                                         persist=False)  # never pollute market.db
        return data

    def run_and_extract(self, params: Dict[str, Any], run_id: str) -> str:
        if "strategy" not in params:
            raise ValueError("params.strategy required")
        strat_d = params["strategy"]
        bars = self._bars(params)
        if not bars:
            raise ValueError("no bars for dataset/universe")
        try:
            from .config import load_capital
            start_cash = float(params.get("start_cash") or load_capital().get("capital", 50000))
        except Exception:
            start_cash = 100000.0
        if (strat_d.get("meta", {}) or {}).get("family") == "ml":
            # OOS-disciplined single run: train on first 80% dates, trade last 20%
            from .ml.strategies import ml_signals, ml_exits
            dates = sorted({b["ts"] for bl in bars.values() for b in bl})
            cut = dates[max(0, int(len(dates) * 0.8) - 1)] if dates else ""
            strat = ml_exits(strat_d)
            sigs = ml_signals(strat_d, bars, live_from=cut)
            res = run_backtest(strat, bars, start_cash=start_cash, signals=sigs)
        else:
            strat = strategy_from_dict(strat_d)
            res = run_backtest(strat, bars, start_cash=start_cash)
            sigs = None
        sigs = KB.emit_signals(run_id, res)
        KB.write_shard(run_id, params, sigs, {k: v for k, v in res.items() if k != "trades"})
        try:
            KB.prune_shards(keep=50)
        except Exception:
            pass
        self._params[run_id] = params
        m = {k: res.get(k) for k in ("n", "wins", "losses", "sharpe", "max_dd", "cagr",
                                     "final_equity", "avg_net_per_trade", "net_profit")}
        return json.dumps({"run_id": run_id, "strategy": strat.name, "metrics": m,
                            "verdict": "PAPER_READY" if (m.get("avg_net_per_trade") or 0) > 0 and (m.get("n") or 0) >= 20 else "EXPLORE"})

    def generate_structured_premise(self, run_id: str, baseline: str | None = None) -> str:
        p = self._params.get(run_id, {})
        s = (p.get("strategy") or {}).get("name", run_id)
        base = f" vs baseline {baseline}" if baseline else ""
        return f"Stock experiment {run_id}: strategy={s}{base} sim={self.simulator}"

    def register_to_kernel(self, run_id: str, premise: str, baseline: str | None = None) -> Dict[str, Any]:
        shard = KB.shard_dir(run_id) / "summary.json"
        metrics: Dict[str, Any] = {}
        try:
            metrics = json.loads(shard.read_text())
        except Exception:
            pass
        node = KB.register_finding(premise, [run_id], metrics,
                                   universe=(self._params.get(run_id, {}) or {}).get("universe", ""),
                                   timeframe=(self._params.get(run_id, {}) or {}).get("timeframe", "1D"))
        return {"name": node.get("node_id", run_id), "topic": KB.TOPIC}

    def get_params(self, run_id: str) -> Dict[str, Any]:
        return self._params.get(run_id, {})

    def get_signals(self, run_id: str) -> List[Dict[str, Any]]:
        try:
            return json.loads((KB.shard_dir(run_id) / "signals.json").read_text())
        except Exception:
            return []
