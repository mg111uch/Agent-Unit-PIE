"""INT-02 + INT-06: agent identity, actor stamping, finding provenance.

Run: conda run -n myenv python -m unittest tests.test_agent_governance -v
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
_KERNEL_ROOT = tempfile.mkdtemp(prefix="pie_gov_")
os.environ.setdefault("PIE_DATA_ROOT", _KERNEL_ROOT)

from modules.economy import agent_identity as ident, ledger, provenance  # noqa: E402


class IdentityTest(unittest.TestCase):
    def test_default_identity_is_least_privilege(self):
        a = ident.load("/nonexistent/identity.json")
        self.assertEqual(a.actor_type, "agent")
        self.assertIn("prospects:import", a.scopes)
        self.assertNotIn("outreach:send", a.scopes)

    def test_forbidden_scope_is_rejected_at_load(self):
        tmp = Path(tempfile.mkdtemp()) / "id.json"
        tmp.write_text(json.dumps({"actor_id": "x", "scopes": ["ledger:write"]}))
        with self.assertRaises(ident.ScopeDenied):
            ident.load(str(tmp))

    def test_require_blocks_unscoped_action(self):
        a = ident.load("/nonexistent/identity.json")
        ident.require(a, "prospects:import")
        with self.assertRaises(ident.ScopeDenied):
            ident.require(a, "outreach:send")

    def test_actor_fields_are_never_anonymous(self):
        a = ident.load("/nonexistent/identity.json")
        self.assertEqual(ident.actor_fields(a)["actor_type"], "agent")
        self.assertEqual(ident.actor_fields(None)["actor_type"], "system")


class LedgerActorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "market.db")
        ledger.ensure_schema(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_prospect_rows_carry_the_actor(self):
        a = ident.load("/nonexistent/identity.json")
        pid = ledger.record_prospect({
            "prospect_id": "pro_1", "company": "Acme", "problem": "supplier discovery",
            "fireflow_id": "ff_9",
        }, db_path=self.db, actor=a)
        row = ledger.get_prospect(pid, db_path=self.db)
        self.assertEqual(row["actor_type"], "agent")
        self.assertEqual(row["actor_id"], "pie_revenue_agent")
        self.assertEqual(row["fireflow_id"], "ff_9")

    def test_transaction_without_actor_is_system(self):
        tid = ledger.record_tx({"tx_id": "tx1", "from": "a", "to": "b",
                                "amount": 10}, db_path=self.db)
        row = ledger.get_tx(tid, db_path=self.db)
        self.assertEqual(row["actor_type"], "system")


class ProvenanceTest(unittest.TestCase):
    def test_stamp_has_all_three_versions(self):
        s = provenance.stamp()
        self.assertEqual(set(s), {"app_commit", "fee_policy_version",
                                  "offer_template_version"})

    def test_policy_change_invalidates_old_findings(self):
        old = provenance.stamped({"finding_id": "f1", "kind": "conversion",
                                  "value": 0.11})
        old["provenance"]["fee_policy_version"] = "rake-5pct"
        now = {"app_commit": old["provenance"]["app_commit"],
               "fee_policy_version": "rake-7pct",
               "offer_template_version": old["provenance"]["offer_template_version"]}
        drift = provenance.needs_invalidation(old, now)
        self.assertIn("fee_policy_version", drift)
        changed, kept = provenance.apply_invalidation([old], now)
        self.assertEqual(changed[0]["validity"]["status"], "HISTORICAL")
        self.assertEqual(kept, [])

    def test_same_regime_stays_active(self):
        f = provenance.stamped({"finding_id": "f2", "kind": "margin"})
        changed, kept = provenance.apply_invalidation([f])
        self.assertEqual(changed, [])
        self.assertEqual(kept[0]["validity"]["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
