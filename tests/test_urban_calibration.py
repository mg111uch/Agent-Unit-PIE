"""SIM-03 Phase C: calibrate the urban pack to real city series.

Run: conda run -n myenv python -m unittest tests.test_urban_calibration -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.simulators.popula_dyn.core import calibration  # noqa: E402
from modules.simulators.popula_dyn.core.simulation_model import (  # noqa: E402
    SimulationModel,
)
from kernel.hypothesis import claim_strength as ladder  # noqa: E402


def observed(value, source="census"):
    return {"value": value, "source": source, "truth": "THIRD_PARTY_VERIFIED"}


KANPUR = {
    "population": observed(2767031),
    "industrial_units": observed(27792, "msme"),
    "municipal_budget_cr": observed(1908, "kmc_budget"),
}

DELHI = {
    "population": observed(16787941),
    "industrial_units": observed(120863, "msme"),
    "municipal_budget_cr": observed(16683.01, "mcd_budget"),
    "road_km": observed(18594.34, "economic_survey"),
}


class MappingTest(unittest.TestCase):
    def test_firms_per_1000_comes_from_units_over_population(self):
        out = calibration.from_fields(KANPUR, agents=400)
        self.assertAlmostEqual(out["params"]["firms_per_1000"],
                               27792 / 2767031 * 1000, places=3)
        self.assertEqual(out["provenance"]["firms_per_1000"]["status"],
                         "observed")
        self.assertAlmostEqual(out["weight_per_agent"], 6917.58, places=2)

    def test_missing_rows_are_null_not_invented(self):
        out = calibration.from_fields({"population": observed(1000000)})
        self.assertIn("industrial_units", out["missing"])
        self.assertIn("municipal_budget_cr", out["missing"])
        self.assertIn("road_km", out["missing"])
        self.assertIsNone(out["anchors"]["firms_per_1000"])
        self.assertNotIn("firms_per_1000", out["params"])
        self.assertNotIn("road_capacity", out["params"])
        # defaults still apply, but as defaults, not as observed numbers
        params = calibration._domain.apply(out["params"])
        self.assertEqual(params["firms_per_1000"],
                         calibration.REFERENCE["firms_per_1000"])

    def test_richer_city_gets_larger_budget_and_road_indices(self):
        kan = calibration.from_fields(KANPUR, agents=400)
        del_ = calibration.from_fields(DELHI, agents=400)
        self.assertGreater(del_["params"]["municipal_grant"],
                           kan["params"]["municipal_grant"])
        self.assertLess(del_["params"]["firms_per_1000"],
                        kan["params"]["firms_per_1000"])
        self.assertIn("road_capacity", del_["params"])
        self.assertNotIn("road_capacity", kan["params"])

    def test_bare_numbers_are_accepted(self):
        out = calibration.from_fields(
            {"population": 1_000_000, "industrial_units": 10_000}, agents=500)
        self.assertAlmostEqual(out["params"]["firms_per_1000"], 10.0)


class FitReportTest(unittest.TestCase):
    def test_anchors_cover_three_real_series(self):
        rep = calibration.fit_report(KANPUR, SimulationModel, agents=200,
                                     years=1, seed=3)
        names = [a["anchor"] for a in rep["anchors"]]
        self.assertEqual(names, ["firms_per_1000", "municipal_grant",
                                 "road_capacity"])
        self.assertGreaterEqual(len(rep["real_series_used"]), 3)
        self.assertIn("road_km", rep["missing"])
        road = next(a for a in rep["anchors"] if a["anchor"] == "road_capacity")
        self.assertIsNone(road["target"])
        self.assertIsNone(road["simulated"])
        self.assertEqual(road["status"], "missing")
        self.assertIn("employment_rate", rep["unmapped"])

    def test_firms_anchor_is_reproduced_by_the_model(self):
        rep = calibration.fit_report(KANPUR, SimulationModel, agents=200,
                                     years=1, seed=3)
        firms = next(a for a in rep["anchors"]
                     if a["anchor"] == "firms_per_1000")
        self.assertLess(firms["relative_error"], 0.2)
        self.assertIn(firms["status"], ("on_target", "within_2x"))

    def test_fiscal_gap_is_reported_not_hidden(self):
        rep = calibration.fit_report(DELHI, SimulationModel, agents=200,
                                     years=1, seed=3)
        diag = rep["fiscal_diagnostic"]
        self.assertIn(diag["status"], ("consistent", "model_gap"))
        self.assertIsNotNone(diag["ratio"])


class TwinDelegationTest(unittest.TestCase):
    def test_twin_entry_point_has_one_urban_mapper(self):
        from modules.digital_twins import calibration_engine
        fields = {k: v for k, v in KANPUR.items()}
        out = calibration_engine.calibrate(fields, domain="urban", agents=300)
        self.assertEqual(out["domain"], "urban")
        self.assertAlmostEqual(out["params"]["firms_per_1000"],
                               27792 / 2767031 * 1000, places=3)
        self.assertIn("road_km", out["missing"])

    def test_agrarian_path_is_unchanged(self):
        from modules.digital_twins import calibration_engine
        fields = {"population": observed(400000),
                  "literacy_rate": observed(0.84)}
        out = calibration_engine.calibrate(fields)
        self.assertNotIn("domain", out)
        self.assertIn("initial_toolmakers", out["params"])


class FindingObservationTest(unittest.TestCase):
    def _result(self, passed, relative):
        return {
            "metric": "welfare", "years": 2, "scales": [400, 2000, 10000],
            "runs": {"power_reliability_capex": {
                "passed": passed, "direction": "+" if passed else "mixed/zero",
                "baseline_by_scale": [0.5, 0.45, 0.4],
                "by_scale": [{"agents": 400, "mean_relative": 0.001},
                             {"agents": 2000, "mean_relative": 0.05},
                             {"agents": 10000, "mean_relative": relative}],
                "level_drift": {"ratio": 0.8},
            }},
        }

    def test_mixed_result_is_recorded_as_unstable(self):
        obs = calibration.finding_observation(
            self._result(False, -0.21), "delhi", "power_reliability_capex")
        self.assertEqual(obs["outcome"], "UNSTABLE")
        self.assertEqual(obs["direction"], "MIXED")
        self.assertEqual(obs["claim_strength"], "HYPOTHESIS")
        self.assertEqual(obs["population"], 10000)
        self.assertEqual(obs["delta"], -21.0)
        self.assertAlmostEqual(obs["observed_value"], 0.4 * 0.79, places=6)

    def test_stable_result_is_direction_only(self):
        obs = calibration.finding_observation(
            self._result(True, 0.12), "kanpur", "power_reliability_capex")
        self.assertEqual(obs["outcome"], "IMPROVED")
        self.assertEqual(obs["direction"], "INCREASE")
        self.assertEqual(obs["metric"], "welfare")


class MetricObservationTest(unittest.TestCase):
    def test_urban_metric_and_override(self):
        from modules.simulators.observation_metrics import build_observation
        obs = build_observation(
            run_id="r", summary={"welfare": 0.55, "population": 200},
            params={"domain": "urban"}, signals=[],
            baseline_summary={"welfare": 0.50, "population": 200},
            baseline_params={"domain": "urban"}, metric="welfare")
        self.assertEqual(obs["metric"], "welfare")
        self.assertEqual(obs["outcome"], "IMPROVED")
        self.assertAlmostEqual(obs["delta"], 10.0)
        mixed = build_observation(
            run_id="r", summary={"welfare": 0.55,
                                 "outcome_override": "UNSTABLE"},
            params={}, signals=[], metric="welfare")
        self.assertEqual(mixed["outcome"], "UNSTABLE")
        self.assertEqual(mixed["direction"], "MIXED")

    def test_connector_persists_an_external_summary(self):
        import tempfile
        from unittest.mock import patch
        from modules.simulators.simulation_connector import SimulationConnector
        with tempfile.TemporaryDirectory() as tmp:
            conn = SimulationConnector(base_path=tmp, emit_to_kernel=False)
            with patch.object(conn, "_persist_run_lineage",
                              lambda *a, **k: None):
                path = conn.save_run_summary(
                    "run_x", {"domain": "urban"}, {"welfare": 0.5})
            self.assertTrue((Path(path) / "summary.json").exists())
            with patch.object(conn, "_read_summary", return_value={
                    "welfare": 0.55, "population": 200}), \
                    patch.object(conn, "get_params",
                                 return_value={"domain": "urban"}), \
                    patch.object(conn, "get_signals", return_value=[]), \
                    patch("kernel.simulation_version.sync_from_git",
                          side_effect=Exception("no git")):
                obs = conn.build_observation("run_x", metric="welfare")
            self.assertEqual(obs["metric"], "welfare")
            self.assertEqual(obs["version_id"], "popula_dyn@V0")


class StabilityTest(unittest.TestCase):
    def test_power_capex_keeps_direction_at_two_scales(self):
        out = calibration.stability(
            SimulationModel, KANPUR,
            mechanisms=("power_reliability_capex",),
            scales=(200, 400), years=1, seed=2)
        run = out["runs"]["power_reliability_capex"]
        self.assertTrue(run["passed"])
        self.assertEqual(run["direction"], "+")
        self.assertEqual([r["agents"] for r in run["by_scale"]],
                         [200, 400])
        self.assertIn("400", out["claim"])

    def test_two_seeds_are_needed_for_any_claim_above_hypothesis(self):
        out = calibration.stability(
            SimulationModel, KANPUR,
            mechanisms=("power_reliability_capex",),
            scales=(200, 400), years=1, seeds=(1, 2))
        run = out["runs"]["power_reliability_capex"]
        self.assertEqual(run["n"], (200 + 400) * 2)
        self.assertEqual(len(run["per_seed_signs"]), 2)
        ev = calibration.claim_evidence(run)
        verdict = ladder.check(ev)
        self.assertEqual(verdict["effective"], "REPLICATED")
        self.assertTrue(verdict["ok"])

    def test_regrade_uses_the_decision_scale_for_seed_agreement(self):
        row = {"scale_passed": True, "direction": "+",
               "by_scale": [{"agents": 400}, {"agents": 10000}],
               "per_seed_signs": {"1": [-1, 1], "2": [1, 1], "3": [1, 1]}}
        self.assertTrue(calibration.regrade(row)["passed"])
        row["per_seed_signs"] = {"1": [1, -1], "2": [1, 1], "3": [1, 1]}
        graded = calibration.regrade(row)
        self.assertFalse(graded["passed"])
        self.assertEqual(graded["direction"], "mixed/zero")


class FalsifyPolicyTest(unittest.TestCase):
    def _params(self, n=100):
        from modules.simulators.popula_dyn.core import domain
        p = {**domain.apply(calibration.from_fields(KANPUR, n)["params"]),
             "years": 1, "seed": 1, "initial_pop": n}
        p["auto_scale_grid"] = True
        p.setdefault("land_per_agent", 1.25)
        return p

    def test_placebo_lever_has_no_effect(self):
        from modules.simulators.popula_dyn.core import falsify
        policy = {"target": "all", "mechanism": "power_reliability_capex",
                  "scope": "all", "magnitude": 0.3, "duration": 3,
                  "cost": 5, "start": 0}
        out = falsify.falsify_policy(
            SimulationModel, self._params(), policy, years=1, seed=1,
            alt_magnitudes=(0.2,))
        self.assertTrue(out["attempted"])
        self.assertIn("placebo", out["tests"])
        self.assertAlmostEqual(out["tests"]["placebo"]["relative"], 0.0,
                               places=6)
        self.assertIn("survived", out)


if __name__ == "__main__":
    unittest.main()
