"""Feature block from NSE delivery data -- information NOT derivable from your OHLCV features.

All features at date d use only the day-d EOD file (published after close), i.e. identical timing to your
existing close-based features.  Raw values here; cross-sectional rank-gauss happens downstream
(ml/dataset._xs_normalize / horizon_scan).  Hypotheses (each must clear stage-1 / horizon_scan on its own;
the literature on delivery % in India is thin -- bulk-deal front-running work finds delivery rising before
events -- so treat these as candidates, not facts):

dlv_z60      delivery % vs own 60d history: abnormal holding-intent vs squaring-off
dlv_ret5     5d sum of daily return x (delivery% - own mean): price moves backed by delivery vs churn
trade_size_z log(qty/trades) vs own 60d: larger average ticket = institutional footprint
dlv_qty_surge log(deliverable qty / 20d mean): absolute accumulation, not just share
turn_shock   log(turnover / 60d median): attention shock (control; expect weak)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FLOW_FEATS = ["dlv_z60", "dlv_ret5", "trade_size_z", "dlv_qty_surge", "turn_shock"]


def build_flow_features(bhav: pd.DataFrame, win: int = 60) -> pd.DataFrame:
    """bhav: ['symbol','date','close','qty','trades','deliv_qty','deliv_per','turnover_lacs'] -> ['date','symbol',*FLOW_FEATS]"""
    b = bhav.sort_values(["symbol", "date"]).copy()
    g = b.groupby("symbol", group_keys=False)

    def z(s, w=win):
        m, sd = s.rolling(w, min_periods=w // 2).mean(), s.rolling(w, min_periods=w // 2).std()
        return (s - m) / sd.replace(0, np.nan)

    b["ret"] = g["close"].pct_change(fill_method=None)
    b["dlv_z60"] = g["deliv_per"].transform(z)
    dev = b["deliv_per"] - g["deliv_per"].transform(lambda s: s.rolling(win, min_periods=win // 2).mean())
    b["_x"] = b["ret"] * dev
    b["dlv_ret5"] = b.groupby("symbol")["_x"].transform(lambda s: s.rolling(5, min_periods=5).sum())
    b["_ts"] = np.log(b["qty"].clip(lower=1) / b["trades"].clip(lower=1))
    b["trade_size_z"] = b.groupby("symbol")["_ts"].transform(z)
    b["dlv_qty_surge"] = np.log(b["deliv_qty"].clip(lower=1) / b.groupby("symbol")["deliv_qty"].transform(lambda s: s.rolling(20, min_periods=10).mean()).clip(lower=1))
    b["turn_shock"] = np.log(b["turnover_lacs"].clip(lower=1e-3) / b.groupby("symbol")["turnover_lacs"].transform(lambda s: s.rolling(win, min_periods=win // 2).median()).clip(lower=1e-3))
    return b[["date", "symbol", *FLOW_FEATS]].replace([np.inf, -np.inf], np.nan)
