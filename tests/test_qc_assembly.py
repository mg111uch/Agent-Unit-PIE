"""REV-04/REV-07: QC primitives and deliverable assembly.

Run: conda run -n myenv python -m unittest tests.test_qc_assembly -v
"""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.economy import assembly, qc  # noqa: E402


class BlockingPlanTest(unittest.TestCase):
    def test_duplicates_never_go_to_the_same_analyst(self):
        p = qc.plan([f"r{i}" for i in range(20)], ["a", "b", "c"], seed=3)
        pairs = [(a["record_id"], a["analyst"]) for a in p["assignments"]]
        for rid in p["duplicates"]:
            owners = [an for r, an in pairs if r == rid]
            self.assertEqual(len(owners), 2)
            self.assertNotEqual(owners[0], owners[1])
            self.assertEqual(len(set(owners)), 2)

    def test_blind_ids_are_stable_and_uninformative(self):
        a = qc.plan(["rec-1", "rec-2"], ["a"], seed=9)["assignments"]
        b = qc.plan(["rec-1", "rec-2"], ["a"], seed=9)["assignments"]
        self.assertEqual([x["blind_id"] for x in a], [x["blind_id"] for x in b])
        self.assertEqual(a[0]["copy"], 1)
        self.assertTrue(a[0]["blind_id"].startswith("q_"))
        self.assertNotIn("rec-1", a[0]["blind_id"])

    def test_no_analyst_is_an_error_not_a_silent_plan(self):
        with self.assertRaises(ValueError):
            qc.plan(["r1"], [])

    def test_gold_truth_is_kept_out_of_the_assignment(self):
        p = qc.plan([f"r{i}" for i in range(10)], ["a", "b"], seed=1)
        gold = qc.inject_gold(p["assignments"], [{"record_id": "g1",
                                                 "fields": {"name": "X"}}],
                              ["a", "b"], seed=1)
        self.assertEqual(len(gold["truth"]), 1)
        for a in gold["assignments"]:
            self.assertNotIn("truth", a)
            self.assertFalse(any("fields" in a for _ in [0]))


class ConsensusTest(unittest.TestCase):
    def test_agreement_is_verified_full_confidence(self):
        out = qc.consensus([
            {"record_id": "r1", "value": {"name": "Acme", "city": "Kanpur"}},
            {"record_id": "r1", "value": {"name": "Acme", "city": "Kanpur"}},
        ])["records"]["r1"]
        self.assertEqual(out["status"], "agreed")
        self.assertEqual(out["confidence"], 1.0)
        self.assertEqual(out["value"]["city"], "Kanpur")

    def test_a_single_copy_is_unverified_not_verified(self):
        out = qc.consensus([{"record_id": "r2",
                             "value": {"name": "Beta"}}])["records"]["r2"]
        self.assertEqual(out["status"], "unverified")
        self.assertEqual(out["confidence"], qc.SINGLE_SOURCE_CONFIDENCE)

    def test_disagreement_keeps_modal_value_and_flags_the_field(self):
        out = qc.consensus([
            {"record_id": "r3", "value": {"city": "Kanpur", "pin": "208001"}},
            {"record_id": "r3", "value": {"city": "Kanpur", "pin": "208002"}},
            {"record_id": "r3", "value": {"city": "Kanpur", "pin": "208001"}},
        ])["records"]["r3"]
        self.assertEqual(out["status"], "disputed")
        self.assertEqual(out["disagreements"], ["pin"])
        self.assertEqual(out["value"]["pin"], "208001")
        self.assertLess(out["confidence"], 1.0)


class SlaTest(unittest.TestCase):
    def test_unknown_accuracy_fails_closed(self):
        v = qc.evaluate(None)
        self.assertFalse(v["pass"])
        self.assertIn("hold payment", v["refund"]["policy"])

    def test_refund_ladder(self):
        self.assertEqual(qc.evaluate(0.95)["refund"]["percent"], 0)
        self.assertEqual(qc.evaluate(0.80)["refund"]["percent"], 50)
        self.assertEqual(qc.evaluate(0.60)["refund"]["percent"], 100)
        self.assertTrue(qc.evaluate(0.80)["refund"]["required"])

    def test_gold_scoring_counts_fields_not_records(self):
        truth = {"q_1": {"name": "Acme", "city": "Kanpur"}}
        subs = [{"blind_id": "q_1", "record_id": "gold::1",
                 "value": {"name": "Acme", "city": "Lucknow"}}]
        g = qc.score_gold(subs, truth)
        self.assertEqual(g["gold_fields"], 2)
        self.assertEqual(g["correct"], 1)
        self.assertEqual(g["accuracy"], 0.5)

    def test_spotcheck_is_deterministic(self):
        ids = [f"r{i}" for i in range(100)]
        self.assertEqual(qc.spotcheck(ids, seed=4), qc.spotcheck(ids, seed=4))
        self.assertEqual(len(qc.spotcheck(ids, ratio=0.2, seed=4)), 20)


class AssemblyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.records = [
            {"record_id": "r1", "fields": {"name": "Acme", "value": 1200},
             "confidence": 1.0, "source": "gem:GEM/1"},
            {"record_id": "r2", "fields": {"name": "Beta & Co", "value": 900},
             "confidence": 0.8, "source": "gem:GEM/2"},
        ]
        self.qc = qc.run(["r1", "r2"], ["a", "b"], [
            {"record_id": "r1", "value": {"name": "Acme"}},
            {"record_id": "r1", "value": {"name": "Acme"}},
        ], gold_records=[{"record_id": "g", "fields": {"name": "Acme"}}],
            truth={}, seed=2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_bundle_has_csv_xlsx_and_note_with_qc_columns(self):
        out = assembly.build(self.records, self.tmp.name, "pilot",
                             qc_report=self.qc)
        self.assertEqual(out["rows"], 2)
        for key in ("csv", "xlsx", "methodology"):
            self.assertTrue(Path(out["files"][key]).exists(), key)
        with open(out["files"]["csv"], newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(rows[0]["confidence"], "1.0")
        self.assertEqual(rows[1]["source"], "gem:GEM/2")
        note = Path(out["files"]["methodology"]).read_text()
        self.assertIn("Gold accuracy", note)
        self.assertIn("Refund rule", note)

    def test_xlsx_is_a_real_archive_with_one_sheet(self):
        out = assembly.build(self.records, self.tmp.name, "pilot2")
        with zipfile.ZipFile(out["files"]["xlsx"]) as z:
            names = z.namelist()
            self.assertIn("xl/worksheets/sheet1.xml", names)
            sheet = z.read("xl/worksheets/sheet1.xml").decode()
        self.assertIn("Beta &amp; Co", sheet)

    def test_empty_bundle_is_honest(self):
        out = assembly.build([], self.tmp.name, "empty")
        self.assertEqual(out["rows"], 0)
        self.assertFalse(out["qc"]["pass"])


if __name__ == "__main__":
    unittest.main()
