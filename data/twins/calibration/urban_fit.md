# Urban pack calibration (SIM-03 Phase C)

Real TWN-01 rows only; placeholders are excluded. A null target means the series is missing, not zero.

## delhi

- agents: 2000 (1 agent = 8395.0 people)
- real series used: population, industrial_units, municipal_budget_cr, road_km
- missing: none
- unmapped in model: employment_rate, industrial_capacity, water_supply_mld, energy_reliability, power_supply_hours, air_quality_pm25

| anchor | target | simulated | rel err | status |
|---|---|---|---|---|
| firms_per_1000 | 7.199 | 6.927 | 0.0378 | on_target |
| municipal_grant | 1.44 | 1.44 | 0.0 | by_construction |
| road_capacity | 1.107 | 1.123 | 0.0145 | on_target |

Fiscal diagnostic: model revenue is 2.262x the budget index (model_gap) — pack limitation, not a fit.

## kanpur

- agents: 2000 (1 agent = 1385.0 people)
- real series used: population, industrial_units, municipal_budget_cr
- missing: road_km
- unmapped in model: employment_rate, industrial_capacity, water_supply_mld, energy_reliability, power_supply_hours, air_quality_pm25

| anchor | target | simulated | rel err | status |
|---|---|---|---|---|
| firms_per_1000 | 10.033 | 9.93 | 0.0103 | on_target |
| municipal_grant | 0.998 | 0.998 | 0.0 | by_construction |
| road_capacity | None | None | None | missing |

Fiscal diagnostic: model revenue is 4.58x the budget index (model_gap) — pack limitation, not a fit.

## Policy stability (calibrated params)

### delhi

metric `welfare`, 2 years, scales [400, 2000, 10000], seeds [1, 2, 3]

| mechanism | direction | passed | n | magnitude range | falsify | claim |
|---|---|---|---|---|---|---|
| power_reliability_capex | mixed/zero | False | 37200 | [-0.011591, 0.088065] | direction not stable at scale | HYPOTHESIS |
| transport_subsidy | mixed/zero | False | 37200 | [0.005976, 0.014512] | direction not stable at scale | HYPOTHESIS |

**Claim (delhi):** HYPOTHESIS: direction does not survive all scales

### kanpur

metric `welfare`, 2 years, scales [400, 2000, 10000], seeds [1, 2, 3]

| mechanism | direction | passed | n | magnitude range | falsify | claim |
|---|---|---|---|---|---|---|
| power_reliability_capex | + | True | 37200 | [0.051763, 0.259562] | passed | FALSIFICATION_PASSED |
| transport_subsidy | + | True | 37200 | [0.03582, 0.355376] | attacks failed: seed=False magnitude=True half=True placebo=True | HYPOTHESIS |

**Claim (kanpur):** HYPOTHESIS: direction does not survive all scales

