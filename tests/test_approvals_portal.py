"""Approval queue + magic-link portal (REV-07/STR-05), no frontend tests.

Run: conda run -n myenv python -m unittest tests.test_approvals_portal -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
DATA = tempfile.mkdtemp(prefix="pie_portal_")
os.environ["PIE_DATA_ROOT"] = DATA
os.environ["AGENT_SKIP_AUTH"] = "true"

from modules.economy import approval_store, ledger, portal  # noqa: E402


class ApprovalStoreTest(unittest.TestCase):
    def test_tier2_needs_one_human_and_no_self_approval(self):
        item = approval_store.save({
            "action": "outreach.send.first", "title": "send first email",
            "requested_by": "agent", "payload": {"to": "buyer@example.com"}})
        self.assertEqual(item["tier"], 2)
        self.assertEqual(item["status"], "pending")
        self.assertIn("item_id", item)
        own = approval_store.decide(item["item_id"], "agent")
        self.assertIn("requester cannot approve", own["error"])
        out = approval_store.decide(item["item_id"], "human:1")
        self.assertEqual(out["status"], "approved")
        self.assertEqual(approval_store.get(item["item_id"])["status"], "approved")

    def test_tier3_needs_two_distinct_humans(self):
        item = approval_store.save({"action": "money.live", "title": "go live",
                                    "requested_by": "agent"})
        self.assertEqual(item["tier"], 3)
        first = approval_store.decide(item["item_id"], "human:1")
        self.assertEqual(first["status"], "pending")
        self.assertEqual(first["remaining"], 1)
        same = approval_store.decide(item["item_id"], "human:1")
        self.assertEqual(same["status"], "pending")
        second = approval_store.decide(item["item_id"], "human:2")
        self.assertEqual(second["status"], "approved")

    def test_queue_survives_a_new_connection(self):
        item = approval_store.save({"action": "research.record", "title": "x"})
        self.assertTrue(any(i["item_id"] == item["item_id"]
                            for i in approval_store.list_items("pending")))
        self.assertGreaterEqual(approval_store.counts().get("pending", 0), 1)


class PortalTest(unittest.TestCase):
    def setUp(self):
        self.deliverable = Path(DATA) / "deliverables" / "sample.csv"
        self.deliverable.parent.mkdir(parents=True, exist_ok=True)
        self.deliverable.write_text("record_id,value\n1,a\n")
        self.made = portal.create("Acme Foods", "Supplier list — 100 rows",
                                  2500.0, str(self.deliverable),
                                  request={"records": 100})
        self.token = self.made["token"]
        self.pid = self.made["proposal"]["proposal_id"]

    def test_token_is_the_only_credential(self):
        other = portal.create("Other", "Other", 100.0)
        self.assertNotEqual(other["token"], self.token)
        self.assertIsNone(portal.get("not-a-token"))
        self.assertEqual(portal.get(self.token)["customer"], "Acme Foods")

    def test_accept_issues_one_invoice_and_is_idempotent(self):
        first = portal.accept(self.token)
        self.assertTrue(first["ok"])
        self.assertFalse(first["already"])
        invoice = first["proposal"]["invoice_id"]
        self.assertTrue(invoice.startswith("INV-"))
        again = portal.accept(self.token)
        self.assertTrue(again["already"])
        self.assertEqual(again["proposal"]["invoice_id"], invoice)

    def test_payment_requires_acceptance_and_records_one_tx(self):
        self.assertIn("accept it first", portal.mark_paid(self.pid, "ref1")["error"])
        portal.accept(self.token)
        paid = portal.mark_paid(self.pid, "UPI-123", "human:1")
        self.assertTrue(paid["ok"])
        self.assertEqual(paid["proposal"]["status"], "paid")
        tx = ledger.get_tx("portal:" + self.pid)
        self.assertIsNotNone(tx)
        self.assertEqual(tx["amount"], 2500.0)
        self.assertEqual(tx["actor_type"], "human")
        again = portal.mark_paid(self.pid, "UPI-123", "human:1")
        self.assertTrue(again["already"])

    def test_download_only_serves_files_inside_the_deliverables_root(self):
        self.assertEqual(portal.deliverable(self.token), self.deliverable.resolve())
        bad = portal.create("Bad", "Bad", 10.0, "/etc/passwd")
        self.assertIsNone(portal.deliverable(bad["token"]))
        missing = portal.create("Missing", "Missing", 10.0,
                                str(Path(DATA) / "deliverables" / "nope.csv"))
        self.assertIsNone(portal.deliverable(missing["token"]))


class RoutesSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from agent_core.server import app
        cls.client = TestClient(app)

    def test_pages_and_json_are_mounted(self):
        self.assertEqual(self.client.get("/approvals").status_code, 200)
        self.assertEqual(self.client.get("/api/economy/approvals").status_code, 200)
        made = self.client.post("/api/economy/proposals", json={
            "customer": "Route Co", "title": "Route pilot", "price": 500})
        self.assertEqual(made.status_code, 200, made.text)
        token = made.json()["token"]
        self.assertEqual(self.client.get(f"/portal/{token}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/portal/{token}").status_code, 200)
        accepted = self.client.post(f"/api/portal/{token}/accept", json={})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertIn("invoice_id", accepted.json()["proposal"])

    def test_unknown_portal_token_is_404(self):
        self.assertEqual(self.client.get("/api/portal/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()
