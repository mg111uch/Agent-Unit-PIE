"""REV-01/REV-02: funnel provenance + GeM CSV import.

Run: conda run -n myenv python -m unittest tests.test_funnel_gem -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.economy import funnel_report, ledger  # noqa: E402
from modules.economy.sources import gem_csv  # noqa: E402
from modules.economy import discovery  # noqa: E402

CSV = """Bid Number,Bid Title,Buyer,State,Quantity,Estimated Bid Value,Bid End Date
GEM/2026/B/1,Industrial safety gloves supply,MSME Dept,Kanpur,"1,200",250000,2026-12-01
GEM/2026/B/2,Warehouse racking,Port Trust,Gujarat,40,90000,2026-11-20
,,,
"""


class GemImportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv = Path(self.tmp.name) / "gem.csv"
        self.csv.write_text(CSV)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rows_become_evidence_backed_prospects(self):
        parsed = gem_csv.parse(self.csv)
        self.assertEqual(len(parsed["items"]), 2)
        self.assertEqual(parsed["skipped"], 1)
        first = parsed["items"][0]
        self.assertEqual(first["source"], "gem")
        self.assertEqual(first["triggers"], ["tender"])
        self.assertTrue(first["evidence"][0].startswith("GeM bid GEM/2026/B/1"))
        self.assertEqual(first["estimated_monthly_value"], 250000.0)

    def test_ids_are_stable_and_deduplicable(self):
        a = gem_csv.parse(self.csv)["items"][0]["prospect_id"]
        b = gem_csv.parse(self.csv)["items"][0]["prospect_id"]
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("pro_gem_"))

    def test_collect_accepts_gem_batch_but_still_reports_deferral_without_one(self):
        imported = discovery.collect("gem", gem_csv.parse(self.csv)["items"])
        self.assertEqual(len(imported["items"]), 2)
        self.assertEqual(imported["note"], "imported from file")
        deferred = discovery.collect("gem")
        self.assertEqual(deferred["items"], [])
        self.assertIn("deferred", deferred["note"])

    def test_missing_file_is_honest(self):
        out = gem_csv.parse(Path(self.tmp.name) / "nope.csv")
        self.assertEqual(out["items"], [])
        self.assertIn("not found", out["note"])


class FunnelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "market.db")
        ledger.ensure_schema(self.db)
        for i in range(4):
            ledger.record_prospect({
                "prospect_id": f"pro_{i}", "company": f"C{i}", "problem": "supplier discovery",
                "evidence": ["press"] if i < 3 else [],
            }, db_path=self.db)
        ledger.record_tx({"tx_id": "t1", "from": "a", "to": "b",
                          "amount": 8000, "kind": "payment"}, db_path=self.db)
        ledger.record_tx({"tx_id": "t2", "from": "a", "to": "b",
                          "amount": 3000, "kind": "payout"}, db_path=self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_stages_carry_their_source(self):
        r = funnel_report.build(db_path=self.db)
        self.assertEqual(r["stages"]["prospects"], {"value": 4, "source": "market.db:prospects"})
        self.assertEqual(r["stages"]["researched"]["value"], 3)
        self.assertEqual(r["stages"]["revenue"]["value"], 8000)
        self.assertEqual(r["stages"]["margin"]["value"], 5000)
        self.assertEqual(r["stages"]["contacted"]["value"], None)
        self.assertEqual(r["stages"]["contacted"]["source"], "unavailable")

    def test_fireflow_fills_the_missing_stages(self):
        ff = {"contacted": 9, "responses": 3, "proposals": 2,
              "pilots": 1, "won": 1}
        r = funnel_report.build(db_path=self.db, ff=ff)
        self.assertEqual(r["stages"]["contacted"]["value"], 9)
        self.assertEqual(r["stages"]["contacted"]["source"],
                         "fireflow:/api/metrics/funnel")
        self.assertTrue(r["fireflow_connected"])
        self.assertNotIn("contacted", r["missing"])

    def test_time_to_first_revenue_is_pending_without_prospect_events(self):
        r = funnel_report.build(db_path=self.db)
        self.assertEqual(r["time_to_first_revenue"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
