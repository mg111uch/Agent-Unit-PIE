"""W5 cognition: claim ladder, city relations, min support, DB concurrency.

Run: conda run -n myenv python -m unittest tests.test_kernel_w5 -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
os.environ["PIE_DATA_ROOT"] = tempfile.mkdtemp(prefix="pie_w5_")

from kernel.hypothesis import claim_strength as ladder  # noqa: E402
from kernel.retrieval.relation_retriever import (  # noqa: E402
    CITY_RELATIONS, RelationRetriever)
from kernel.retrieval.retrieval_engine import retrieval_engine  # noqa: E402


class ClaimLadderTest(unittest.TestCase):
    def test_default_is_hypothesis(self):
        v = ladder.check({})
        self.assertEqual(v["effective"], "HYPOTHESIS")
        self.assertTrue(v["ok"])

    def test_replicated_needs_seeds_and_sample_size(self):
        weak = ladder.check({"claim_strength": "REPLICATED", "seeds": 1, "n": 3})
        self.assertFalse(weak["ok"])
        self.assertEqual(weak["effective"], "HYPOTHESIS")
        self.assertTrue(any("REPLICATED needs" in x for x in weak["violations"]))
        strong = ladder.check({"claim_strength": "REPLICATED", "seeds": 2,
                               "n": ladder.min_n()})
        self.assertTrue(strong["ok"])
        self.assertEqual(strong["effective"], "REPLICATED")

    def test_falsification_and_oos_are_separate_rungs(self):
        base = {"seeds": 3, "n": 50}
        no_falsify = ladder.check({**base, "claim_strength": "FALSIFICATION_PASSED"})
        self.assertEqual(no_falsify["effective"], "REPLICATED")
        self.assertFalse(no_falsify["ok"])
        f = ladder.check({**base, "claim_strength": "FALSIFICATION_PASSED",
                          "falsification": {"attempted": True, "passed": True}})
        self.assertTrue(f["ok"])
        oos = ladder.check({**base, "claim_strength": "VALIDATED_OOS",
                            "falsification": {"attempted": True, "passed": True},
                            "oos": {"holdout": True, "metrics": {"auc": 0.71}}})
        self.assertEqual(oos["effective"], "VALIDATED_OOS")
        self.assertTrue(oos["ok"])

    def test_unknown_level_is_not_silently_accepted(self):
        v = ladder.check({"claim_strength": "PROVEN"})
        self.assertFalse(v["ok"])
        self.assertIn("unknown claim_strength", v["violations"][0])

    def test_enforce_downgrades_and_keeps_the_request(self):
        out = ladder.enforce({"claim_strength": "VALIDATED_OOS", "seeds": 1,
                              "n": 2})
        self.assertEqual(out["claim_strength"], "HYPOTHESIS")
        self.assertEqual(out["claim_strength_requested"], "VALIDATED_OOS")
        self.assertTrue(out["claim_strength_downgraded"])


class RelationTest(unittest.TestCase):
    def setUp(self):
        self.r = RelationRetriever()
        from kernel.memory.semantic_memory import semantic_memory
        self.r._memory = semantic_memory

    def test_city_relations_are_typed_and_validated(self):
        self.assertIn("requires", CITY_RELATIONS)
        with self.assertRaises(ValueError):
            self.r.link("a", "b", "vibes_with")

    def test_seed_links_factory_to_electricity(self):
        out = self.r.seed([
            {"source": "unit:factory_1", "target": "unit:grid",
             "relation": "requires", "confidence": 0.9},
            {"source": "unit:road_7", "target": "unit:cluster_leather",
             "relation": "serves"},
            {"source": "unit:ward_3", "target": "unit:neighbourhood_9",
             "relation": "contains"},
        ])
        self.assertEqual(len(out["linked"]), 3)
        self.assertEqual(out["skipped"], [])
        rel = self.r.relations("unit:factory_1")
        self.assertEqual([e["relation"] for e in rel["out"]], ["requires"])
        self.assertEqual(rel["out"][0]["inverse"], "required_by")
        self.assertEqual(self.r.neighbors("unit:facility_never_used"), [])

    def test_explain_returns_a_dependency_path(self):
        self.r.link("unit:factory_2", "unit:grid", "requires")
        self.r.link("unit:grid", "unit:coal", "requires")
        out = self.r.explain("unit:factory_2", depth=2)
        chain = [step["relation"] for path in out["paths"] for step in path]
        self.assertTrue(chain)
        self.assertIn("requires", chain)
        self.assertGreaterEqual(out["path_count"], 1)

    def test_city_summary_counts_only_city_relations(self):
        self.r.link("unit:policy_1", "unit:industry_1", "affects")
        summary = self.r.city_summary()
        self.assertGreaterEqual(summary["counts"].get("affects", 0), 1)

    def test_engine_exposes_relation_retrieval(self):
        self.r.link("unit:worker_1", "unit:firm_1", "employed_by")
        out = retrieval_engine.retrieve_relations("unit:worker_1")
        self.assertIn("paths", out)
        self.assertTrue(out["paths"])


class MinSupportTest(unittest.TestCase):
    def test_default_support_is_two_and_configurable(self):
        from kernel.compression_engine import CompressionEngine
        self.assertEqual(CompressionEngine().min_support, 2)
        self.assertEqual(CompressionEngine(config={"min_support": 5}).min_support, 5)
        self.assertEqual(CompressionEngine(config={"min_support": 0}).min_support, 1)


class DoctorConcurrencyTest(unittest.TestCase):
    def test_doctor_reports_journal_timeout_and_write_probe(self):
        tmp = tempfile.mkdtemp(prefix="pie_doctor_")
        env = {**os.environ, "PIE_DATA_ROOT": tmp,
               "PIE_DB_BUSY_TIMEOUT_MS": "2500"}
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "topic_ops.py"),
             "doctor", "--json"],
            capture_output=True, text=True, env=env, cwd=str(ROOT))
        self.assertEqual(out.returncode in (0, 1), True, out.stderr[-800:])
        report = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(report["db_busy_timeout_ms"], 2500)
        self.assertIn(report["db_journal_mode"].lower(), ("wal", "delete", "memory"))
        self.assertEqual(report["db_write_probe"], "ok")


if __name__ == "__main__":
    unittest.main()
