"""Thin city adapters: static shaped payloads -> canonical CityState values.

KMC-shaped (Kanpur) and DDA-shaped (Delhi, MPD-2047-style zones).
Shaped/static inputs only — no network fetching. Placeholder values
carry confidence <=0.35 and source 'placeholder:<basis>'; never fake
precision (rounded estimates only).
"""
from __future__ import annotations

from typing import Any, Dict

KANPUR_SHAPED = {
    "city": "Kanpur",
    "source": "kmc",
    "wards": 110,
    "population_2011": 2767031,
    "districts": ["Kanpur Nagar"],
    "services": ["water", "sewerage", "solid_waste", "property", "gis"],
}

DELHI_SHAPED = {
    "city": "Delhi",
    "source": "dda",
    "mpd": "2047",
    "population_2011": 16787941,
    "zones": ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "N", "O", "P"],
    "sectors": ["environment", "economy", "transport", "water",
                "waste", "power", "spatial", "monitoring"],
}


def kanpur_fields() -> Dict[str, Dict[str, Any]]:
    return {
        "population": {"value": 2770000, "source": "census_2011", "truth": "THIRD_PARTY_VERIFIED",
                       "quality": "census", "confidence": 0.85,
                       "geography": {"wards": KANPUR_SHAPED["wards"]}},
        "employment_rate": {"value": 0.52, "source": "placeholder:plfs_like", "truth": "AI_INFERRED",
                            "quality": "estimate", "confidence": 0.3},
        "industrial_capacity": {"value": 0.71, "source": "placeholder:phase3_slice", "truth": "AI_INFERRED",
                                "quality": "estimate", "confidence": 0.35},
        "water_supply_mld": {"value": 420, "source": "placeholder:kmc_reports", "truth": "AI_INFERRED",
                             "quality": "estimate", "confidence": 0.3},
        "energy_reliability": {"value": 0.88, "source": "placeholder:discom", "truth": "AI_INFERRED",
                               "quality": "estimate", "confidence": 0.3},
        "literacy_rate": {"value": 0.84, "source": "census_2011", "truth": "THIRD_PARTY_VERIFIED",
                          "quality": "census", "confidence": 0.8},
        "air_quality_pm25": {"value": 110, "source": "placeholder:cpcb_like", "truth": "AI_INFERRED",
                             "quality": "estimate", "confidence": 0.3},
    }


def delhi_fields() -> Dict[str, Dict[str, Any]]:
    return {
        "population": {"value": 16790000, "source": "census_2011", "truth": "THIRD_PARTY_VERIFIED",
                       "quality": "census", "confidence": 0.85,
                       "geography": {"zones": len(DELHI_SHAPED["zones"]),
                                     "mpd": DELHI_SHAPED["mpd"]}},
        "employment_rate": {"value": 0.55, "source": "placeholder:plfs_like", "truth": "AI_INFERRED",
                            "quality": "estimate", "confidence": 0.3},
        "industrial_capacity": {"value": 0.76, "source": "placeholder:survey", "truth": "AI_INFERRED",
                                "quality": "estimate", "confidence": 0.3},
        "water_supply_mld": {"value": 3200, "source": "placeholder:djb_reports", "truth": "AI_INFERRED",
                             "quality": "estimate", "confidence": 0.3},
        "energy_reliability": {"value": 0.97, "source": "placeholder:discom", "truth": "AI_INFERRED",
                               "quality": "estimate", "confidence": 0.35},
        "literacy_rate": {"value": 0.86, "source": "census_2011", "truth": "THIRD_PARTY_VERIFIED",
                          "quality": "census", "confidence": 0.8},
        "air_quality_pm25": {"value": 140, "source": "placeholder:cpcb_like", "truth": "AI_INFERRED",
                             "quality": "estimate", "confidence": 0.3},
    }


def kanpur_history() -> Dict[int, Dict[str, Any]]:
    """Sparse anchor snapshots, all labeled estimates except census years."""
    return {
        2011: {"population": 2767031, "quality": "census"},
        2015: {"population": 2900000, "quality": "estimate"},
        2020: {"population": 3100000, "quality": "estimate"},
        2025: {"population": 3300000, "quality": "estimate"},
    }


def delhi_history() -> Dict[int, Dict[str, Any]]:
    return {
        2011: {"population": 16787941, "quality": "census"},
        2015: {"population": 18000000, "quality": "estimate"},
        2020: {"population": 20000000, "quality": "estimate"},
        2025: {"population": 22000000, "quality": "estimate"},
    }
