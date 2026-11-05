"""W4 ops: LLM spend accounting (OPS-07) and secret scan (OPS-03).

Run: conda run -n myenv python -m unittest tests.test_ops -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from agent_core import llm_cost  # noqa: E402


class PriceTest(unittest.TestCase):
    def test_price_uses_model_rate_and_splits_input_output(self):
        p = llm_cost.price("gemini-2.0-flash", 1000, 1000)
        self.assertAlmostEqual(p["inr"], 0.15, places=4)
        self.assertEqual(p["model"], "gemini-2.0-flash")

    def test_unknown_model_falls_back_to_default_rate(self):
        p = llm_cost.price("mystery-model", 1000, 0)
        self.assertEqual(p["rate"], llm_cost.DEFAULT_PRICING["_default"])

    def test_pricing_is_overridable_by_env(self):
        os.environ["LLM_PRICING_JSON"] = '{"my-model":{"in_per_1k":1,"out_per_1k":2}}'
        try:
            self.assertAlmostEqual(llm_cost.price("my-model", 1000, 1000)["inr"], 3.0)
        finally:
            os.environ.pop("LLM_PRICING_JSON", None)


class BudgetTest(unittest.TestCase):
    def test_zero_caps_mean_unlimited(self):
        b = llm_cost.Budget()
        self.assertTrue(b.add(10_000_000, 9999)["ok"])
        self.assertFalse(b.exceeded())

    def test_token_cap_trips(self):
        b = llm_cost.Budget(max_tokens=100)
        out = b.add(60, 0)
        self.assertTrue(out["ok"])
        out = b.add(60, 0)
        self.assertFalse(out["ok"])
        self.assertTrue(out["over_tokens"])

    def test_inr_cap_trips_independently(self):
        b = llm_cost.Budget(max_inr=1.0)
        self.assertFalse(b.add(10, 1.5)["ok"])
        self.assertFalse(b.add(10, 0.0)["ok"])


class CostLogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = llm_cost.CostLog(str(Path(self.tmp.name) / "cost.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_records_tokens_and_inr_per_task(self):
        self.log.record("task-1", {"prompt_tokens": 1000,
                                   "completion_tokens": 500},
                        "gemini", "gemini-2.0-flash")
        t = self.log.task_totals("task-1")
        self.assertEqual(t["tokens"], 1500)
        self.assertEqual(t["calls"], 1)
        self.assertGreater(t["inr"], 0)

    def test_tasks_are_kept_separate(self):
        self.log.record("a", {"total_tokens": 100}, "gemini", "gemini-2.0-flash")
        self.log.record("b", {"total_tokens": 900}, "gemini", "gemini-2.0-flash")
        self.assertEqual(self.log.task_totals("a")["tokens"], 100)
        self.assertEqual(self.log.task_totals("b")["tokens"], 900)
        self.assertEqual(len(self.log.summary()["tasks"]), 2)

    def test_record_returns_budget_verdict(self):
        b = llm_cost.Budget(max_tokens=10)
        out = self.log.record("c", {"total_tokens": 50}, "gemini",
                              "gemini-2.0-flash", b)
        self.assertFalse(out["budget"]["ok"])


class SecretScanTest(unittest.TestCase):
    def _scan(self, files: dict) -> subprocess.CompletedProcess:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name, body in files.items():
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "secret_scan.py"),
             "--path", str(root), "--json"],
            capture_output=True, text=True)

    def test_a_real_looking_key_fails_the_scan(self):
        # Built at runtime so this test file is not itself a scan hit.
        fake = "sk-" + "live0123456789abcdefghijklmn"
        out = self._scan({"app.py": f'KEY = "{fake}"\n'})
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("openai_key", out.stdout)

    def test_placeholders_pass(self):
        out = self._scan({"README.md": "OPENAI_API_KEY=<your-key-here>\n"})
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_repo_and_env_example_are_clean(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "secret_scan.py")],
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


class OpsScriptsTest(unittest.TestCase):
    def test_paths_come_from_env_not_personal_constants(self):
        from paths import describe
        out = describe()
        for key in ("pie_root", "codebase", "data", "fireflow", "atlas"):
            self.assertIn(key, out)

    def test_restore_drill_on_empty_dir_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "backup.py"),
                 "--outdir", tmp, "--restore-drill", "--json"],
                capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertIn("no backups found", out.stdout)


if __name__ == "__main__":
    unittest.main()
