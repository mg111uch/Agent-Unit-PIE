"""Inbox consumer tests (offline, tmp DB): dedup, replay no-op, DLQ, ignore.

Stdlib unittest (pytest is not installed in the conda env).
Run: conda run -n myenv python -m unittest tests.test_inbox -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))

# OPS-06: kernel writes must land in a throwaway root during tests.
_ISOLATED = Path(tempfile.mkdtemp(prefix="pie_test_kernel_"))
os.environ.setdefault("PIE_DATA_ROOT", str(_ISOLATED))

from modules.economy import inbox, ledger  # noqa: E402

PAYMENT = {
    "tx_id": "contract-release:9", "actual_revenue": 100000,
    "actual_cost": 94000, "profit": 6000, "unit": "contract:9", "memo": "t",
}


def ev(eid, etype="payment_settled", payload=None):
    return {"id": eid, "event_type": etype,
            "payload": PAYMENT if payload is None else payload}


def fetcher(events):
    def f(since=None, limit=100):
        return {"events": events, "count": len(events)}
    return f


class InboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "market.db")
        ledger.ensure_schema(self.db)
        self.markers = inbox.MemoryMarkerStore()
        inbox.set_marker_store(self.markers)

    def tearDown(self):
        inbox.set_marker_store(None)
        self.tmp.cleanup()

    def test_duplicate_delivery_applies_once(self):
        inbox.pull(fetcher([ev("e1")]), db_path=self.db)
        second = inbox.pull(fetcher([ev("e1")]), db_path=self.db)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["applied"], 0)
        self.assertEqual(list(self.markers.seen), ["e1"])
        self.assertEqual(inbox.stats(self.db)["applied"], 1)

    def test_replay_is_a_noop(self):
        inbox.pull(fetcher([ev("e1")]), db_path=self.db)
        out = inbox.replay("e1", db_path=self.db)
        self.assertTrue(out["already_applied"])
        self.assertEqual(inbox.stats(self.db)["applied"], 1)

    def test_malformed_payload_dead_letters(self):
        # 3 failed attempts (MAX_ATTEMPTS) before it leaves the queue.
        out = None
        for _ in range(3):
            out = inbox.pull(fetcher([ev("e2", payload={})]), db_path=self.db)
        self.assertEqual(out["dead"], 1)
        row = inbox.dlq_list(self.db)[0]
        self.assertEqual(row["event_id"], "e2")
        self.assertEqual(row["state"], "dead")
        self.assertIn("tx_id", row["last_error"])

    def test_unknown_event_type_is_ignored(self):
        out = inbox.pull(fetcher([ev("e3", etype="something_new")]), db_path=self.db)
        self.assertEqual(out["ignored"], 1)
        self.assertEqual(inbox.stats(self.db)["ignored"], 1)
        self.assertNotIn("e3", self.markers.seen)

    def test_dlq_retry_applies_after_fix(self):
        for _ in range(3):
            inbox.pull(fetcher([ev("e4", payload={})]), db_path=self.db)
        self.assertEqual(inbox.stats(self.db)["dead"], 1)
        con = ledger.connect(self.db)
        try:
            con.execute("UPDATE ff_inbox SET payload_json=? WHERE event_id='e4'",
                        (json.dumps({"tx_id": "t4", "profit": 5}),))
            con.commit()
        finally:
            con.close()
        self.assertEqual(inbox.dlq_retry(self.db)["applied"], 1)
        self.assertEqual(inbox.stats(self.db)["applied"], 1)


if __name__ == "__main__":
    unittest.main()
