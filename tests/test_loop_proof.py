"""G0 loop proof (PIE half), offline and deterministic.

One FireFlow settlement (captured payload shape) must become exactly one
kernel event + one `capital_flow` signal, be retrievable by PIE, and replaying
it must change nothing. Dedup uses the real kernel marker store, so these
assertions hold across repeats too.

Run: conda run -n myenv python -m unittest tests.test_loop_proof -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
os.environ["PIE_DATA_ROOT"] = tempfile.mkdtemp(prefix="pie_loop_proof_")

from modules.economy import inbox, ledger  # noqa: E402
from kernel.memory.memory_engine import memory_engine  # noqa: E402
from kernel.retrieval.retrieval_engine import RetrievalEngine  # noqa: E402

FEED = json.loads((ROOT / "tests" / "fixtures" / "fireflow_outbox_sample.json")
                  .read_text())
TX = "contract-release:41"


def fetcher(since=None, limit=100):
    return FEED


def kernel_events() -> list:
    """Every persisted episodic event."""
    out = []
    for oid in memory_engine.list_objects("episodic"):
        obj = memory_engine.load_object("episodic", oid) or {}
        if obj.get("event_type"):
            out.append(obj)
    return out


def signals_of_type(signal_type: str) -> list:
    hits = []
    for mt in ("episodic", "signal"):
        for oid in memory_engine.list_objects(mt):
            obj = memory_engine.load_object(mt, oid) or {}
            if obj.get("signal_type") == signal_type:
                hits.append(obj)
    return hits


def payments_for(tx_id: str) -> list:
    hits = []
    for e in kernel_events():
        if e.get("event_type") != "payment_settled":
            continue
        meta = e.get("metadata", {}) or {}
        extra = meta.get("extra", meta) or {}
        if extra.get("tx_id") == tx_id:
            hits.append(e)
    return hits


class LoopProofTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "market.db")
        ledger.ensure_schema(self.db)
        inbox.set_marker_store(None)  # production dedup: kernel markers

    def tearDown(self):
        self.tmp.cleanup()

    def test_loop_proof_end_to_end(self):
        before = len(kernel_events())
        inbox.pull(fetcher, db_path=self.db)
        after = kernel_events()

        # Exactly one new kernel event, and it is the payment.
        self.assertEqual(len(after) - before, 1)
        self.assertEqual(len(payments_for(TX)), 1)

        ev = payments_for(TX)[0]
        extra = (ev.get("metadata") or {}).get("extra", {})
        self.assertEqual(extra.get("profit"), 6000)

        # The economic signal PIE learns from exists.
        # The signal must belong to THIS settlement (other suites may have
        # written their own capital_flow signals in the same kernel root).
        mine = [s for s in signals_of_type("capital_flow")
                if TX in json.dumps(s, default=str)]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["value"], 6000)

        # Retrievable through the cascade, not just from the table.
        results = RetrievalEngine().search("payment_settled", limit=10)
        blob = json.dumps([r.content for r in results], default=str)
        self.assertIn(TX, blob)

        # Replay is a no-op.
        count = len(kernel_events())
        out = inbox.replay("payment_settled:" + TX, db_path=self.db)
        self.assertTrue(out["already_applied"])
        self.assertEqual(len(kernel_events()), count)

    def test_repeated_delivery_is_deduped(self):
        inbox.pull(fetcher, db_path=self.db)
        inbox.pull(fetcher, db_path=self.db)
        self.assertEqual(len(payments_for(TX)), 1)

    def test_task_verified_is_not_money(self):
        inbox.pull(fetcher, db_path=self.db)
        types = [e.get("event_type") for e in kernel_events()]
        self.assertNotIn("task_verified", types)


if __name__ == "__main__":
    unittest.main()
