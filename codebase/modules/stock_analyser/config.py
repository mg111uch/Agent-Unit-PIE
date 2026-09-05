"""Money config: single source of truth (capital, flat costs, scale steps)."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

DEFAULTS: Dict[str, Any] = {
    "capital": 50000, "flat_cost_per_roundtrip": 60, "max_positions": 8,
    "min_history_bars": 60, "scale_step": 25000, "min_trades": 20,
    "retire_after": 25, "screen_min_trades": 3, "screen_min_avg_net": -30.0, "scale_min_closed_trades": 10,
    "scale_min_avg_net_per_trade": 90, "scale_max_drawdown": -0.15,
    "cost_stt_bps": 2.5, "cost_stamp_bps": 0.3, "cost_exch_bps": 0.35,
    "cost_sebi_bps": 0.02, "cost_slip_bps": 5.0, "cost_impact_bps": 8.0,
    "sizing_vol_target": 0, "sizing_min_k": 0.25, "sizing_max_k": 2.0,
    "paper_max_gap": 0.15, "paper_stale_days": 5,
    "liq_max_participation": 0.05, "liq_min_adv": 50000, "liq_min_price": 10.0,
    "liq_max_spread": 0.08, "liq_adv_window": 20,
}


def load_capital(path: str | None = None) -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    p = Path(path) if path else Path(__file__).resolve().parent / "capital.yaml"
    try:
        import yaml
        if p.exists():
            cfg.update(yaml.safe_load(p.read_text()) or {})
    except Exception:
        pass
    return cfg
