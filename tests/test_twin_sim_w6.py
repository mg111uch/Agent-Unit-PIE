"""W6: twin coverage (TWN-01), scale invariance (SIM-01), run identity (SIM-02).

Run: conda run -n myenv python -m unittest tests.test_twin_sim_w6 -v
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
os.environ.setdefault("PIE_DATA_ROOT", tempfile.mkdtemp(prefix="pie_w6_"))

from modules.digital_twins import city_adapters, city_series, city_state  # noqa: E402
from kernel import simulation_version as sv  # noqa: E402


def _city(fields):
    return city_state.build_state("city_test", fields)


class CoverageTest(unittest.TestCase):
    def test_ten_series_are_defined(self):
        self.assertEqual(len(city_state.FIELDS), 10)
        self.assertIn("road_km", city_state.FIELDS)
        self.assertIn("municipal_budget_cr", city_state.FIELDS)

    def test_kanpur_coverage_separates_observed_from_placeholder(self):
        cov = city_state.coverage(_city(city_adapters.kanpur_fields()))
        self.assertEqual(cov["series"], 10)
        self.assertEqual(cov["observed"], 1)      # population only (census)
        self.assertEqual(cov["placeholder"], 5)
        self.assertEqual(cov["missing"], 4)       # industrial_units, power, road, budget
        self.assertEqual(cov["by_field"]["population"], "observed")
        self.assertEqual(cov["by_field"]["road_km"], "missing")
        self.assertFalse(cov["complete"])

    def test_placeholder_detection_requires_a_real_source(self):
        self.assertTrue(city_state.is_placeholder(
            {"source": "placeholder:kmc", "truth": "AI_INFERRED"}))
        self.assertFalse(city_state.is_placeholder(
            {"source": "kmc_annual_2023", "truth": "OWNER_REPORTED"}))


class SeriesIngestTest(unittest.TestCase):
    def _file(self, rows):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"city_id": "city_kanpur", "series": rows}, tmp)
        tmp.close()
        self.addCleanup(lambda: Path(tmp.name).unlink(missing_ok=True))
        return tmp.name

    def test_real_rows_replace_placeholders_and_raise_coverage(self):
        path = self._file([
            {"field": "road_km", "value": 1850, "source": "kmc_annual_2023",
             "year": 2023, "license": "govt-open"},
            {"field": "water_supply_mld", "value": 460,
             "source": "kmc_water_2024", "year": 2024, "license": "govt-open"},
        ])
        out = city_series.ingest(path, city_adapters.kanpur_fields())
        self.assertTrue(out["ok"])
        self.assertIn("water_supply_mld", out["replaced_placeholders"])
        self.assertEqual(out["coverage"]["by_field"]["road_km"], "observed")
        # population + road_km + water_supply_mld = 3 observed
        self.assertEqual(out["coverage"]["observed"], 3)

    def test_unsourced_rows_are_rejected_not_averaged(self):
        path = self._file([
            {"field": "road_km", "value": 1850, "source": "", "year": 2023,
             "license": "govt-open"},
            {"field": "population", "value": 1, "source": "x", "year": 2023,
             "license": ""},
            {"field": "vibes", "value": 1, "source": "x", "year": 2023,
             "license": "x"},
        ])
        out = city_series.ingest(path, city_adapters.kanpur_fields())
        self.assertFalse(out["ok"])
        self.assertEqual(len(out["rejected"]), 3)
        reasons = " ".join(r["reason"] for r in out["rejected"])
        self.assertIn("missing source", reasons)
        self.assertIn("missing license", reasons)
        self.assertIn("unknown field", reasons)

    def test_stale_series_are_marked(self):
        path = self._file([
            {"field": "population", "value": 2767031, "source": "census_2011",
             "year": 2011, "license": "public-domain"},
        ])
        loaded = city_series.load_file(path)
        self.assertTrue(loaded["accepted"][0]["stale"])

    def test_coverage_table_aggregates_cities(self):
        table = city_series.coverage_table({
            "kanpur": _city(city_adapters.kanpur_fields()),
            "delhi": _city(city_adapters.delhi_fields()),
        })
        self.assertEqual(table["cities"]["kanpur"]["series"], 10)
        self.assertGreater(table["total_placeholder"], 0)
        self.assertEqual(table["total_missing"], 8)   # 4 per city


class SeriesFileTest(unittest.TestCase):
    def test_shipped_city_files_validate_and_raise_coverage(self):
        series_dir = ROOT / "data" / "twins" / "series"
        for city, fn, expected in (("kanpur", city_adapters.kanpur_fields, 3),
                                   ("delhi", city_adapters.delhi_fields, 4)):
            path = series_dir / f"{city}.json"
            self.assertTrue(path.exists(), f"missing {path}")
            out = city_series.ingest(path, fn())
            self.assertTrue(out["ok"], out)
            self.assertEqual(out["rejected"], [], city)
            self.assertGreaterEqual(out["coverage"]["observed"], expected)
            observed = [f for f, v in out["coverage"]["by_field"].items()
                        if v == "observed"]
            self.assertTrue(observed)
            for name in observed:
                if name != "population":
                    self.assertTrue(out["state"]["fields"][name].get("url"),
                                    f"{city}:{name} lost its source url")


class RunKeyTest(unittest.TestCase):
    def test_param_hash_ignores_run_noise(self):
        a = sv.param_hash({"initial_pop": 400, "seed": 1, "run_id": "x"})
        b = sv.param_hash({"initial_pop": 400, "seed": 1, "run_id": "y"})
        self.assertEqual(a, b)
        self.assertNotEqual(a, sv.param_hash({"initial_pop": 401, "seed": 1}))

    def test_seed_set_is_part_of_the_key(self):
        self.assertEqual(sv.seed_set({"seed": 7}), "s7")
        self.assertEqual(sv.seed_set({"seeds": [1, 2]}), "1+2")
        self.assertEqual(sv.seed_set({}), "s-random")
        self.assertNotEqual(
            sv.run_key("popula_dyn", "popula_dyn@abc", {"initial_pop": 400, "seed": 1}),
            sv.run_key("popula_dyn", "popula_dyn@abc", {"initial_pop": 400, "seed": 2}))

    def test_run_key_shape(self):
        key = sv.run_key("popula_dyn", "popula_dyn@abc123",
                         {"initial_pop": 400, "seed": 1})
        self.assertTrue(key.startswith("popula_dyn@abc123:"))
        self.assertEqual(len(key.split(":")), 3)
        bare = sv.run_key("popula_dyn", "V1", {"seed": 1})
        self.assertTrue(bare.startswith("popula_dyn@V1:"))

    def test_different_param_regimes_never_contradict(self):
        a = {"run_key": "k1", "param_hash": "p1"}
        b = {"run_key": "k2", "param_hash": "p2"}
        self.assertFalse(sv.same_regime(a, b))
        self.assertTrue(sv.same_regime(a, dict(a)))

    def test_sweep_is_a_new_regime_not_a_new_commit(self):
        base = {"initial_pop": 400, "seed": 1}
        sweep = {"initial_pop": 2000, "seed": 1}
        self.assertEqual(sv.param_hash(base) == sv.param_hash(sweep), False)
        self.assertEqual(sv.run_key("popula_dyn", "v1", base).split(":")[0],
                         sv.run_key("popula_dyn", "v1", sweep).split(":")[0])


class RunKeyPersistenceTest(unittest.TestCase):
    def test_run_key_round_trips_through_sqlite(self):
        from kernel.persistence.db import kernel_db
        v = sv.get_or_create_initial_version("popula_dyn")
        params = {"initial_pop": 400, "seed": 1, "run_id": "ignored"}
        key = sv.run_key("popula_dyn", v["version_id"], params)
        run_id = f"w6_rt_{os.getpid()}"
        kernel_db.save_simulation_run(run_id, v["version_id"], params, None,
                                      {"ok": True}, simulator="popula_dyn",
                                      run_key=key)
        row = kernel_db.load_simulation_run(run_id)
        self.assertEqual(row["run_key"], key)
        self.assertEqual(row["run_key"], sv.run_key(
            "popula_dyn", v["version_id"], {**params, "run_id": "other"}))


class ScaleHelpersTest(unittest.TestCase):
    def test_level_drift_flags_a_collapsing_baseline(self):
        from modules.simulators.popula_dyn.core.scale import level_drift
        ok = level_drift([1.8, 1.79, 1.7])
        self.assertIsNone(ok["warning"])
        bad = level_drift([1.8, 1.77, 0.086])
        self.assertIsNotNone(bad["warning"])
        self.assertIn("degenerate regime", bad["warning"])
        self.assertIsNone(level_drift([1.0])["warning"])

    def test_weight_per_agent_makes_scale_explicit(self):
        self.assertEqual(city_state_scale(), 6925.0)

    def test_stratified_flags_a_missing_bucket(self):
        from modules.simulators.popula_dyn.core.scale import stratified
        rows = [{"ward": "A", "age": "working"}, {"ward": "A"}]
        out = stratified(rows, ["ward", "age", "income"])
        self.assertIn("income", out["missing"])
        self.assertFalse(out["ok"])

    def test_confidence_interval_widens_with_few_seeds(self):
        from modules.simulators.popula_dyn.core.scale import confidence_interval
        lo, hi = confidence_interval([0.01, 0.02, 0.015])
        self.assertLess(lo, hi)
        self.assertEqual(confidence_interval([0.5]), (0.5, 0.5))


class ScaleRunTest(unittest.TestCase):
    """SIM-01 needs numpy+mesa; skip honestly when the env cannot run the sim."""

    def test_scale_invariance_runs_when_sim_is_importable(self):
        try:
            from modules.simulators.popula_dyn.core.simulation_model import SimulationModel
            from modules.simulators.popula_dyn.core.scale import scale_invariance
            from modules.simulators.popula_dyn.constants import PARAMS
        except Exception as e:  # numpy/mesa absent in this env
            self.skipTest(f"simulator unavailable: {type(e).__name__}: {e}")
        policy = {"target": "all", "mechanism": "food_subsidy", "scope": "all",
                  "magnitude": 0.2, "duration": 3, "cost": 1.0, "start": 0}
        out = scale_invariance(SimulationModel, dict(PARAMS), policy,
                               scales=(400, 2000), years=3, seeds=(1,))
        self.assertIsNotNone(out["passed"])
        self.assertEqual(len(out["by_scale"]), 2)
        self.assertEqual(len(out["baseline_by_scale"]), 2)
        self.assertIn("level_drift", out)
        slow = os.environ.get("PIE_SLOW_SIM") == "1"
        if not slow:
            self.assertNotIn(10000, out["scales"])


def city_state_scale():
    from modules.simulators.popula_dyn.core.scale import weight_per_agent
    return weight_per_agent(2770000, 400)


if __name__ == "__main__":
    unittest.main()
