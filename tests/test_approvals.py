"""STR-05: risk-tiered approvals and the autonomy charter.

Run: conda run -n myenv python -m unittest tests.test_approvals -v
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.economy import approvals  # noqa: E402


class ClassifyTest(unittest.TestCase):
    def test_low_risk_agent_work_is_notify_only(self):
        c = approvals.classify({"action": "research.record"})
        self.assertEqual(c["tier"], 1)
        self.assertEqual(c["approvers_required"], 0)

    def test_first_outbound_send_needs_one_human(self):
        self.assertEqual(approvals.classify({"action": "outreach.send.first"})
                         ["tier"], 2)

    def test_money_moving_actions_need_two_humans(self):
        for action in ("money.live", "ledger.refund", "contract.execute"):
            self.assertEqual(approvals.classify({"action": action})["tier"], 3,
                             action)

    def test_large_amount_escalates_regardless_of_action(self):
        c = approvals.classify({"action": "worker.payout",
                                "amount_paise": approvals.LIVE_AMOUNT_PAISE})
        self.assertEqual(c["tier"], 3)

    def test_unknown_action_defaults_to_single_human_never_notify(self):
        self.assertEqual(approvals.classify({"action": "mystery.thing"})
                         ["tier"], 2)

    def test_never_automatic_actions_are_top_tier(self):
        c = approvals.classify({"action": "money.provider_credentials"})
        self.assertEqual(c["tier"], 3)
        self.assertEqual(c["charter"], "never_automatic")


class InboxTest(unittest.TestCase):
    def test_tier3_sorts_before_tier1_and_oldest_first(self):
        now = datetime(2026, 11, 1, tzinfo=timezone.utc)
        items = [
            {"action": "research.record", "created_at": "2026-10-01T00:00:00+00:00"},
            {"action": "money.live", "created_at": "2026-10-30T00:00:00+00:00"},
            {"action": "outreach.send.first", "created_at": "2026-10-29T00:00:00+00:00"},
        ]
        out = approvals.inbox(items, now=now)
        self.assertEqual([i["tier"] for i in out["items"]], [3, 2, 1])
        self.assertEqual(out["counts"], {1: 1, 2: 1, 3: 1})
        self.assertEqual(out["waiting_on_human"], 2)

    def test_sla_breach_is_flagged(self):
        now = datetime(2026, 11, 1, tzinfo=timezone.utc)
        old = (now - timedelta(days=2)).isoformat()
        out = approvals.inbox([{"action": "contract.execute",
                                "created_at": old}], now=now)
        self.assertTrue(out["items"][0]["overdue"])
        self.assertEqual(out["overdue"], 1)

    def test_decided_items_leave_the_inbox(self):
        out = approvals.inbox([{"action": "money.live", "status": "approved"}])
        self.assertEqual(out["items"], [])


class DecideTest(unittest.TestCase):
    def test_requester_cannot_approve_themselves(self):
        item = approvals.enqueue({"action": "money.live",
                                  "requested_by": "agent:growth"})
        out = approvals.decide(item, "agent:growth")
        self.assertIn("requester cannot approve", out["error"])
        self.assertEqual(out["status"], "pending")

    def test_tier3_needs_two_distinct_humans(self):
        item = approvals.enqueue({"action": "money.live",
                                  "requested_by": "agent:growth"})
        first = approvals.decide(item, "user:1")
        self.assertEqual(first["status"], "pending")
        self.assertEqual(first["remaining"], 1)
        second = approvals.decide(first, "user:1")
        self.assertEqual(second["status"], "pending", "same human twice is not two")
        third = approvals.decide(second, "user:2")
        self.assertEqual(third["status"], "approved")
        self.assertEqual(third["approvals"], ["user:1", "user:2"])

    def test_reject_short_circuits(self):
        item = approvals.enqueue({"action": "outreach.send.first",
                                  "requested_by": "agent:growth"})
        out = approvals.decide(item, "user:1", "reject", "bad list")
        self.assertEqual(out["status"], "rejected")
        self.assertEqual(out["reason"], "bad list")

    def test_charter_is_machine_readable(self):
        c = approvals.charter()
        self.assertIn("requester != approver", c["invariants"])
        self.assertIn("money.live", c["charter"]["needs_two_humans"])


if __name__ == "__main__":
    unittest.main()
