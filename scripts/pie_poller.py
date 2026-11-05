"""PIE poller (INT-01): FireFlow outbox -> ff_inbox -> kernel_bus.

    conda run -n myenv python scripts/pie_poller.py --once
    conda run -n myenv python scripts/pie_poller.py --loop --interval 60
    conda run -n myenv python scripts/pie_poller.py --dlq
    conda run -n myenv python scripts/pie_poller.py --replay payment_settled:...

Env: FIREFLOW_URL (default http://localhost:5000), PIE_AGENT_KEY (required).
No secrets in code. Network failures are logged, never fatal.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

from modules.economy import inbox  # noqa: E402
from modules.economy import agent_identity  # noqa: E402

BASE = os.environ.get("FIREFLOW_URL", "http://localhost:5000").rstrip("/")
KEY = agent_identity.api_key()


def _post(path: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = f"{BASE}{path}"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Agent-Api-Key": KEY},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read() or b"{}")
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"[poller] ack failed: {e}", file=sys.stderr)
        return None


def http_fetcher(since: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """GET /api/pie/events. Raises on transport errors (caller decides)."""
    q = {"limit": limit}
    if since:
        q["after"] = since
    url = f"{BASE}/api/pie/events?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"X-Agent-Api-Key": KEY})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read() or b"{}")


def ack(ids) -> None:
    ids = list(ids or [])
    if ids:
        _post("/api/pie/events/ack", {"ids": ids})


def tick(since: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """One poll. Applies events, then acks only the ones that are not dead."""
    try:
        result = inbox.pull(http_fetcher, since=since, limit=limit)
    except Exception as e:  # noqa: BLE001 - offline is normal
        return {"ok": False, "error": str(e)}
    # Ack only events the kernel actually absorbed; dead rows stay queued.
    ack(result.get("applied_ids", []))
    result["ok"] = True
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--since", default=None)
    ap.add_argument("--replay", default=None)
    ap.add_argument("--dlq", action="store_true")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args(argv)

    if not KEY and not (a.dlq or a.stats or a.replay):
        print("PIE_AGENT_KEY is not set", file=sys.stderr)
        return 2
    if a.stats:
        print(json.dumps(inbox.stats(), indent=1))
        return 0
    if a.dlq:
        print(json.dumps(inbox.dlq_list(), indent=1))
        return 0
    if a.replay:
        print(json.dumps(inbox.replay(a.replay), indent=1))
        return 0
    if a.once:
        print(json.dumps(tick(a.since), indent=1))
        return 0
    while True:
        # Acked events leave the pending set, so no cursor bookkeeping is
        # needed; `since` only seeds the first pull.
        print(json.dumps(tick(a.since)), flush=True)
        a.since = None
        time.sleep(max(5, a.interval))


if __name__ == "__main__":
    raise SystemExit(main())
