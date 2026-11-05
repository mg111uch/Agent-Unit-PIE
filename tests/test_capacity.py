"""REV-03: agent-first delivery capacity and cost per verified record.

Run: conda run -n myenv python -m unittest tests.test_capacity -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.economy import delivery  # noqa: E402

AGENTS = [
    {"id": "agent:research-1", "capabilities": ["web_research"]},
    {"id": "agent:research-2", "capabilities": ["web_research", "call"]},
    {"id": "agent:finance", "capabilities": ["ledger"]},
]


class AssignTest(unittest.TestCase):
    def test_tasks_go_to_capable_agents_and_load_is_balanced(self):
        tasks = [{"objective": f"t{i}", "skill": "web_research"}
                 for i in range(4)]
        out = delivery.assign_executors(tasks, AGENTS)
        self.assertEqual(out["unassigned"], [])
        owners = [t["executor"] for t in out["tasks"]]
        self.assertEqual(set(owners), {"agent:research-1", "agent:research-2"})
        self.assertEqual(out["load"]["agent:research-1"], 2)
        self.assertEqual(out["load"]["agent:research-2"], 2)
        self.assertTrue(all(t["executor_type"] == "agent" for t in out["tasks"]))

    def test_missing_capability_is_reported_not_hidden(self):
        out = delivery.assign_executors(
            [{"objective": "call leads", "skill": "telepathy"}], AGENTS)
        self.assertEqual(len(out["unassigned"]), 1)
        self.assertEqual(out["unassigned"][0]["reason"], "no capable agent")
        self.assertIsNone(out["tasks"][0]["executor"])

    def test_skill_free_task_uses_any_agent(self):
        out = delivery.assign_executors([{"objective": "generic"}], AGENTS)
        self.assertIsNotNone(out["tasks"][0]["executor"])
        self.assertEqual(out["human_executors"], 0)


class CapacityTest(unittest.TestCase):
    def test_100_records_take_one_agent_day_and_light_qc(self):
        p = delivery.capacity_plan(100)
        self.assertEqual(p["agent_days"], 1)
        self.assertEqual(p["qc_hours"], 0.5)     # 100 * 0.2 * 1.5 min
        self.assertEqual(p["bottleneck"], "agents")
        self.assertEqual(p["total_days"], 1)

    def test_qc_can_be_the_bottleneck(self):
        p = delivery.capacity_plan(2000, agents=5,
                                   qc_minutes_per_record=10,
                                   qc_humans=1)
        self.assertEqual(p["bottleneck"], "qc")
        self.assertGreater(p["qc_days"], p["agent_days"])

    def test_zero_records_is_not_a_division_by_zero(self):
        p = delivery.capacity_plan(0)
        self.assertEqual(p["records"], 0)
        self.assertEqual(p["total_days"], 0)


class CostTest(unittest.TestCase):
    def test_cost_per_verified_record_and_price_floor(self):
        c = delivery.cost_per_verified_record(
            100, payouts=[500, 500], qc_hours=1.0, compute=100)
        self.assertEqual(c["total"], 1400)
        self.assertEqual(c["cost_per_verified_record"], 14)
        self.assertEqual(c["price_floor"], 15.56)  # 14 / 0.9

    def test_no_verified_records_means_unknown_not_zero(self):
        c = delivery.cost_per_verified_record(0, payouts=[500])
        self.assertIsNone(c["cost_per_verified_record"])
        self.assertIn("unknown", c["note"])

    def test_margin_guard_reuses_the_delivery_floor(self):
        c = delivery.cost_per_verified_record(10, payouts=[90], min_margin=0.10)
        self.assertEqual(c["price_floor"], 10.0)


if __name__ == "__main__":
    unittest.main()
