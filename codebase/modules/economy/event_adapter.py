"""FireFlow-SHAPED -> kernel event bridge (ONE type: PaymentSettled).

Thin I/O bridge: translates payloads shaped like
execution.record_outcome_tx results ({tx_id, actual_revenue,
actual_cost, profit, unit, ...}) into canonical kernel event/signal
dicts published via kernel_bus. No external calls, no FireFlow-repo
changes, no new tables. Follows the score_cli proxy pattern.

Usage: echo '{"tx_id":"t1","profit":50.0,...}' | python -m modules.economy.event_adapter [--publish]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from . import execution as _EX  # noqa: F401 (field-shape reference)
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

PAYMENT_SETTLED = "payment_settled"
PROFIT_SIGNAL = "capital_flow"


def payment_settled_to_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Translate a PaymentSettled-shaped payload to a kernel event dict."""
    if not isinstance(payload, dict) or not payload.get("tx_id"):
        raise ValueError("payload needs at least {'tx_id': ...}")
    profit = float(payload.get("profit", 0.0) or 0.0)
    return {
        "event_type": PAYMENT_SETTLED,
        "category": "economic",
        "title": f"payment settled {payload['tx_id']}",
        "description": (
            f"tx {payload['tx_id']}: revenue "
            f"{payload.get('actual_revenue', '?')} cost "
            f"{payload.get('actual_cost', '?')} profit {profit}"
        ),
        "source_unit_id": str(payload.get("unit", "unit_ext")),
        "source_type": "fireflow_shaped",
        "confidence": 0.9,
        "importance": 0.7 if profit >= 0 else 0.9,
        "tags": [PAYMENT_SETTLED, "profit" if profit >= 0 else "loss"],
        "metadata": {
            "tx_id": payload["tx_id"],
            "profit": profit,
            "adjustment_tx": payload.get("adjustment_tx"),
            "memo": payload.get("memo", ""),
        },
    }


def payment_settled_to_signal(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Translate a PaymentSettled-shaped payload to a kernel signal dict."""
    if not isinstance(payload, dict) or not payload.get("tx_id"):
        raise ValueError("payload needs at least {'tx_id': ...}")
    return {
        "signal_type": PROFIT_SIGNAL,
        "value": float(payload.get("profit", 0.0) or 0.0),
        "category": "economic",
        "source_unit_id": str(payload.get("unit", "unit_ext")),
        "source_type": "fireflow_shaped",
        "confidence": 0.9,
        "importance": 0.7,
        "metadata": {"tx_id": payload["tx_id"]},
    }


def publish_payment_settled(
    payload: Dict[str, Any], bus: Any = None
) -> Dict[str, str]:
    """Translate + publish via kernel_bus. Returns {event_id, signal_id}."""
    if bus is None:
        from kernel import kernel_bus as bus
    event = bus.publish_event(payment_settled_to_event(payload))
    signal = bus.publish_signal(payment_settled_to_signal(payload))
    event.generated_signals.append(signal.signal_id)
    return {"event_id": event.event_id, "signal_id": signal.signal_id}


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception as e:
        print(json.dumps({"error": f"bad JSON input: {e}"}))
        raise SystemExit(1)
    try:
        out = {"event": payment_settled_to_event(payload),
               "signal": payment_settled_to_signal(payload)}
        if "--publish" in sys.argv:
            out["published"] = publish_payment_settled(payload)
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
