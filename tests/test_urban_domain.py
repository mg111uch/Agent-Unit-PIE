"""SIM-03 Phase A: one engine, two domain packs (agrarian and urban).

Run: conda run -n myenv python -m unittest tests.test_urban_domain -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from modules.simulators.popula_dyn.constants import PARAMS  # noqa: E402
from modules.simulators.popula_dyn.core import domain, policy  # noqa: E402
from modules.simulators.popula_dyn.core.scale import scale_invariance  # noqa: E402
from modules.simulators.popula_dyn.core.simulation_model import SimulationModel  # noqa: E402
from modules.simulators.popula_dyn.core.society import society_state  # noqa: E402
from modules.simulators.popula_dyn.core.urban import ZONES  # noqa: E402


def urban_params(**extra):
    return {"domain": "urban", "grid_width": 14, "grid_height": 14,
            "initial_pop": 80, "years": 1, "seed": 7, "firms_per_1000": 20,
            **extra}


class ProfileTest(unittest.TestCase):
    def test_aliases_resolve_and_unknown_falls_back(self):
        self.assertEqual(domain.resolve("city"), "urban")
        self.assertEqual(domain.resolve("rural"), "agrarian")
        self.assertEqual(domain.resolve("nonsense"), "agrarian")
        self.assertEqual(domain.get("urban")["land_type"], "parcel")

    def test_apply_fills_defaults_without_overwriting(self):
        out = domain.apply({"domain": "urban", "wage_offer": 9.0})
        self.assertEqual(out["domain"], "urban")
        self.assertEqual(out["wage_offer"], 9.0)
        self.assertIn("power_reliability", out)
        self.assertIn("work", out["human_behaviors"])
        self.assertNotEqual(out["land_per_agent"],
                            domain.get("agrarian")["land_per_agent"])


class UrbanInitTest(unittest.TestCase):
    def test_agent_mix_has_workers_firms_and_zoned_parcels(self):
        m = SimulationModel(urban_params())
        humans = [u for u in m.units.values() if u.unit_type == "human"]
        parcels = [u for u in m.units.values() if u.unit_type == "parcel"]
        firms = [u for u in m.units.values() if u.unit_type == "firm"]
        self.assertEqual(len(humans), 80)
        self.assertEqual(len(parcels), 14 * 14)
        self.assertGreaterEqual(len(firms), 1)
        self.assertTrue(all("work" in u.behaviors for u in humans))
        self.assertTrue(all(u.behaviors == ["operate"] for u in firms))
        self.assertTrue(all(u.get_state("zone") in ZONES for u in parcels))


class LabourMarketTest(unittest.TestCase):
    def test_work_produces_output_wages_and_employment(self):
        m = SimulationModel(urban_params())
        for _ in range(4):
            m.step()
        soc = society_state(m)
        self.assertEqual(soc["domain"], "urban")
        self.assertGreater(soc["urban_output"], 0.0)
        self.assertGreater(m.wage_bill, 0.0)
        self.assertGreater(soc["employment_rate"], 0.5)
        self.assertGreater(soc["food_security"], 0.0)
        self.assertGreater(soc["gva_per_worker"], 0.0)
        summary = m.summary()
        for key in ("domain", "employment_rate", "urban_output",
                    "wage_bill", "gva_per_worker"):
            self.assertIn(key, summary)

    def test_firms_do_not_pay_wages_they_cannot_afford(self):
        m = SimulationModel(urban_params())
        for firm in (u for u in m.units.values() if u.unit_type == "firm"):
            firm.resources["wealth"] = 0.0
        m.step()
        self.assertEqual(m.wage_bill, 0.0)

    def test_hire_breaks_ties_by_unit_id_not_insertion_order(self):
        from modules.simulators.popula_dyn.behaviours.urban import _nearest_firm

        class _Firm:
            unit_type = "firm"
            alive = True

            def __init__(self, uid):
                self.unit_id = uid
                self.resources = {"wealth": 100.0}
                self.state = {"position": (5, 5), "max_workers": 10,
                              "wage_offer": 2.0}

            def get_state(self, key, default=None):
                return self.state.get(key, default)

            def get_resource(self, key, default=0):
                return self.resources.get(key, default)

        class _Worker:
            unit_id = "h1"

            def get_state(self, key, default=None):
                return (5, 5) if key == "position" else default

        class _Model:
            units = {}

        model = _Model()
        for uid in ("z_firm", "a_firm"):
            model.units[uid] = _Firm(uid)
        picked = _nearest_firm(_Worker(), model, None, 4)
        self.assertEqual(picked.unit_id, "a_firm")


class AgrarianUnchangedTest(unittest.TestCase):
    def test_default_still_creates_land_and_farmers(self):
        m = SimulationModel({"grid_width": 8, "grid_height": 8,
                             "initial_pop": 10, "initial_healers": 1,
                             "initial_toolmakers": 1, "initial_traders": 1,
                             "seed": 3})
        self.assertEqual(m.domain, "agrarian")
        self.assertTrue(any(u.unit_type == "land" for u in m.units.values()))
        farmers = [u for u in m.units.values() if u.behaviors
                   and "harvest" in u.behaviors]
        self.assertTrue(farmers)
        m.step()
        self.assertGreater(society_state(m)["food_security"], 0.0)


class PolicyDomainTest(unittest.TestCase):
    def _policy(self, mechanism, domain_name):
        return {"target": "all", "mechanism": mechanism, "scope": "all",
                "magnitude": 0.2, "duration": 3, "cost": 10, "start": 0,
                "domain": domain_name}

    def test_urban_lever_compiles_only_on_urban_params(self):
        params = domain.apply({"domain": "urban"})
        out = policy.compile(self._policy("power_reliability_capex", "urban"), params)
        self.assertEqual(out["domain"], "urban")
        self.assertIn("power_capacity", out["deltas"])

    def test_cross_domain_mechanism_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "belongs to domain agrarian"):
            policy.compile(self._policy("industrial_policy", "urban"),
                           domain.apply({"domain": "urban"}))
        with self.assertRaisesRegex(ValueError, "belongs to domain urban"):
            policy.compile(self._policy("water_tariff", "agrarian"),
                           domain.apply({"domain": "agrarian"}))

    def test_agrarian_policy_still_compiles(self):
        params = {**PARAMS, **domain.apply({"domain": "agrarian"})}
        out = policy.compile(self._policy("food_subsidy", "agrarian"), params)
        self.assertEqual(out["domain"], "agrarian")
        self.assertIn("metabolism", out["deltas"])
        self.assertEqual(policy.MECHANISMS, policy.AGRARIAN_MECHANISMS)


class UrbanUtilitiesTest(unittest.TestCase):
    def test_utilities_and_budget_are_reported(self):
        m = SimulationModel(urban_params())
        m.step()
        soc = society_state(m)
        for key in ("power_reliability", "water_supply", "traffic_congestion",
                    "municipal_revenue", "municipal_spend",
                    "municipal_balance", "municipal_balance_total"):
            self.assertIn(key, soc)
        self.assertGreater(soc["power_reliability"], 0.0)
        self.assertLessEqual(soc["power_reliability"], 1.0)
        self.assertGreater(soc["water_supply"], 0.0)
        self.assertGreater(soc["traffic_congestion"], 0.0)
        self.assertGreater(soc["municipal_revenue"], 0.0)

    def test_more_road_capacity_lowers_congestion(self):
        tight = SimulationModel(urban_params(road_capacity=0.8))
        roomy = SimulationModel(urban_params(road_capacity=1.2))
        tight.step()
        roomy.step()
        self.assertGreater(tight.traffic_congestion,
                           roomy.traffic_congestion)
        self.assertEqual(roomy.traffic_congestion, 0.0)

    def test_power_capex_raises_reliability_and_output(self):
        base = SimulationModel(urban_params())
        for _ in range(4):
            base.step()
        p = urban_params()
        compiled = policy.compile(
            {"target": "firms", "mechanism": "power_reliability_capex",
             "scope": "all", "magnitude": 0.2, "duration": 4,
             "cost": 5, "start": 0, "domain": "urban"},
            domain.apply(p))
        treated = SimulationModel(p)
        base_params = dict(treated.params)
        for i in range(4):
            treated.params = policy.at_step(base_params, compiled, i)
            treated.step()
        treated.params = base_params
        self.assertGreater(treated.power_capacity, base.power_capacity)
        self.assertGreater(treated.power_reliability_actual,
                           base.power_reliability_actual)
        self.assertGreater(treated.urban_output_total,
                           base.urban_output_total)

    def test_profit_share_reaches_workers(self):
        m = SimulationModel(urban_params(profit_share=0.5))
        for _ in range(2):
            m.step()
        self.assertGreater(getattr(m, "profit_shared_total", 0.0), 0.0)
        soc = society_state(m)
        self.assertGreater(soc["profit_shared"], 0.0)

    def test_zero_profit_share_pays_nothing(self):
        m = SimulationModel(urban_params(profit_share=0.0))
        m.step()
        self.assertEqual(getattr(m, "profit_shared_total", 0.0), 0.0)

    def test_pending_dividends_settle_at_step_end(self):
        m = SimulationModel(urban_params(profit_share=0.5))
        for _ in range(2):
            m.step()
        pending = [u.get_state("pending_dividend", 0)
                   for u in m.units.values() if u.unit_type == "firm"]
        self.assertTrue(all(not p for p in pending))
        self.assertGreater(getattr(m, "profit_shared_total", 0.0), 0.0)

    def test_deficit_halves_next_step_capex(self):
        m = SimulationModel(urban_params(municipal_capex=100.0))
        m.step()
        first = m.municipal_spend
        self.assertLess(m.municipal_balance, 0.0)
        m.step()
        self.assertGreater(first, 0.0)
        self.assertLessEqual(m.municipal_spend, first * 0.5 + 1e-9)


class UrbanScaleTest(unittest.TestCase):
    def test_urban_policy_direction_holds_on_a_small_scale_sweep(self):
        policy_dict = {"target": "firms", "mechanism": "industrial_incentive",
                       "scope": "all", "magnitude": 0.2, "duration": 3,
                       "cost": 5, "start": 0}
        out = scale_invariance(SimulationModel, urban_params(),
                               policy_dict, scales=(40, 80), years=3, seeds=(1,))
        self.assertEqual(len(out["baseline_by_scale"]), 2)
        self.assertIn(out["by_scale"][0]["effects"][0]["sign"], (-1, 0, 1))
        self.assertIsNotNone(out["passed"])


if __name__ == "__main__":
    unittest.main()
