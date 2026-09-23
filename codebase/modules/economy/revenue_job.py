"""First live REVENUE_DISCOVERY_JOB (PhasePlan response): public evidence ->
prospect -> offer shortlist. Seeds are real 2026 expansion signals with
source URLs in evidence. No messages sent: OUTREACH/PILOT verdicts mean
'cleared for contact lookup + human approval', never auto-contact.
Run: conda run -n myenv python codebase/modules/economy/revenue_job.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.economy.discovery import collect, rank
from modules.economy.service_templates import get_template, instantiate
from modules.economy.outreach import draft_message
from modules.economy import ledger

TEMPLATE_FOR = {"supplier discovery": "supplier_discovery_100",
                "product catalogue": "price_collection_50",
                "lead list": "price_collection_50",
                "price collection": "price_collection_50"}

SEEDS = [
    {"company": "DN Solutions India", "region": "Bengaluru, Karnataka", "industry": "machine tools", "problem": "supplier discovery", "evidence": ["Rs.600cr first India plant opened Aug 2026 (The Hindu)", "80% localisation by parts count, targeting domestic sourcing"], "triggers": ["new plant"], "estimated_monthly_value": 200000, "recommended_pilot": 8000, "contactability": 0.3, "confidence": 0.72, "source": "press"},
    {"company": "Jabil India", "region": "Pune, Maharashtra", "industry": "electronics manufacturing", "problem": "supplier discovery", "evidence": ["New Pune factory Jun 2026, footprint 0.5M->1.2M sqft", "Headcount 5000->11000, MoU with Maharashtra govt"], "triggers": ["new factory", "hiring surge"], "estimated_monthly_value": 200000, "recommended_pilot": 8000, "contactability": 0.3, "confidence": 0.7, "source": "press"},
    {"company": "Inteva Products India", "region": "Pune, Maharashtra", "industry": "auto components", "problem": "supplier discovery", "evidence": ["Second Pune plant announced, Rs.50cr, 400 jobs", "Deeper integration with India supply ecosystem stated"], "triggers": ["new factory"], "estimated_monthly_value": 120000, "recommended_pilot": 6000, "contactability": 0.35, "confidence": 0.68, "source": "press"},
    {"company": "FORVIA India", "region": "Pune/Chennai", "industry": "auto components", "problem": "supplier discovery", "evidence": ["10th India plant: complete seat assembly, production 2027", "2.6M record H1 2026 vehicle sales driving capacity"], "triggers": ["new plant"], "estimated_monthly_value": 150000, "recommended_pilot": 7000, "contactability": 0.3, "confidence": 0.66, "source": "press"},
    {"company": "Jaya Hind Industries", "region": "Pune/Chennai", "industry": "die casting", "problem": "supplier discovery", "evidence": ["Rs.600cr phased expansion FY26-28, 12+ HPDC machines", "New Chennai facility + machining/heat-treatment in-house"], "triggers": ["capacity expansion"], "estimated_monthly_value": 150000, "recommended_pilot": 7000, "contactability": 0.35, "confidence": 0.68, "source": "press"},
    {"company": "Neolite ZKW", "region": "Pune, Maharashtra", "industry": "auto lighting", "problem": "supplier discovery", "evidence": ["New Pune plant operational Dec 2025, OEM portfolio growing", "Kancheepuram next facility in pipeline"], "triggers": ["new plant"], "estimated_monthly_value": 100000, "recommended_pilot": 6000, "contactability": 0.35, "confidence": 0.65, "source": "press"},
    {"company": "Feintool India", "region": "Pune, Maharashtra", "industry": "precision stamping", "problem": "supplier discovery", "evidence": ["First India plant inaugurated Jun 2026, ramping Pune production", "Expansion into cold forming/e-motor cores planned"], "triggers": ["new plant"], "estimated_monthly_value": 100000, "recommended_pilot": 6000, "contactability": 0.35, "confidence": 0.64, "source": "press"},
    {"company": "Cybernetik Technologies", "region": "Raigad, Maharashtra", "industry": "industrial automation", "problem": "supplier discovery", "evidence": ["5th facility 20 acres Raigad, 15x capacity, 120 staff", "Export push to US via Bombay-Goa highway corridor"], "triggers": ["new factory", "export push"], "estimated_monthly_value": 80000, "recommended_pilot": 5000, "contactability": 0.4, "confidence": 0.66, "source": "press"},
    {"company": "Klubers Lubrication India", "region": "Mysore, Karnataka", "industry": "specialty lubricants", "problem": "supplier discovery", "evidence": ["Rs.142cr Mysore expansion, operational by early 2027", "New IATF/ISO certs, faster local supply stated goal"], "triggers": ["capacity expansion"], "estimated_monthly_value": 80000, "recommended_pilot": 5000, "contactability": 0.35, "confidence": 0.62, "source": "press"},
    {"company": "Cisco India Manufacturing", "region": "Chennai, Tamil Nadu", "industry": "networking hardware", "problem": "supplier discovery", "evidence": ["First India plant Chennai, $1.3B projected impact, 1200 jobs", "Built with Flex, multiyear investment plan phase 1"], "triggers": ["new plant"], "estimated_monthly_value": 150000, "recommended_pilot": 7000, "contactability": 0.25, "confidence": 0.6, "source": "press"},
    {"company": "General Mills India", "region": "Nashik, Maharashtra", "industry": "food manufacturing", "problem": "supplier discovery", "evidence": ["Rs.100cr second Nashik plant Feb 2026", "Local supplier/ancillary boost expected"], "triggers": ["new plant"], "estimated_monthly_value": 60000, "recommended_pilot": 5000, "contactability": 0.3, "confidence": 0.58, "source": "press"},
    {"company": "Nestle India Sanand", "region": "Sanand, Gujarat", "industry": "food manufacturing", "problem": "supplier discovery", "evidence": ["Rs.225cr MUNCH line expansion Mar 2026", "Supply-chain streamlining via Gujarat hub stated"], "triggers": ["capacity expansion"], "estimated_monthly_value": 60000, "recommended_pilot": 5000, "contactability": 0.3, "confidence": 0.58, "source": "press"},
    {"company": "FlaktGroup India", "region": "Pune, Maharashtra", "industry": "HVAC", "problem": "supplier discovery", "evidence": ["Project GAGAN: 13,826 sqm Pune plant, 6500 units/yr", "Structured hiring/training programme underway"], "triggers": ["new plant", "hiring surge"], "estimated_monthly_value": 80000, "recommended_pilot": 5000, "contactability": 0.35, "confidence": 0.62, "source": "press"},
    {"company": "MS Engineering Tech", "region": "Vadodara, Gujarat", "industry": "energy engineering", "problem": "supplier discovery", "evidence": ["DPIIT-registered Vadodara engineering co, unfunded", "Non-renewable power-gen component needs"], "triggers": [], "estimated_monthly_value": 25000, "recommended_pilot": 5000, "contactability": 0.6, "confidence": 0.5, "source": "directory"},
    {"company": "JJ Enginova", "region": "Vadodara, Gujarat", "industry": "industrial automation", "problem": "supplier discovery", "evidence": ["Vadodara automation/PLC panel integrator, unfunded", "Multi-OEM panel + upgrade work"], "triggers": [], "estimated_monthly_value": 25000, "recommended_pilot": 5000, "contactability": 0.6, "confidence": 0.5, "source": "directory"},
    {"company": "Engineeringwerk", "region": "Satara, Maharashtra", "industry": "engineering services", "problem": "supplier discovery", "evidence": ["Satara mobile-machinery design services, unfunded", "Offshore engineering-centre support line"], "triggers": [], "estimated_monthly_value": 20000, "recommended_pilot": 5000, "contactability": 0.6, "confidence": 0.48, "source": "directory"},
    {"company": "Mega Parts Solutions", "region": "Pune, Maharashtra", "industry": "auto components", "problem": "supplier discovery", "evidence": ["Pune auto-component supplier since 1995", "Custom connector/rubber/wire sourcing for workshops"], "triggers": [], "estimated_monthly_value": 30000, "recommended_pilot": 5000, "contactability": 0.65, "confidence": 0.55, "source": "directory"},
    {"company": "Kanpur Leather Goods LB-14247", "region": "Kanpur, UP", "industry": "leather goods", "problem": "product catalogue", "evidence": ["Est. 2003, operating at 50% capacity, seeking brand launch", "Ladies bags/wallets third-party manufacturing base"], "triggers": ["brand launch"], "estimated_monthly_value": 30000, "recommended_pilot": 5000, "contactability": 0.5, "confidence": 0.6, "source": "marketplace"},
    {"company": "Kanpur White-label Leather Mfr", "region": "Kanpur, UP", "industry": "leather goods", "problem": "lead list", "evidence": ["30k wallets+belts/mo capacity, only 5 B2B clients", "Running below capacity, wants client diversification"], "triggers": [], "estimated_monthly_value": 35000, "recommended_pilot": 5000, "contactability": 0.5, "confidence": 0.58, "source": "marketplace"},
    {"company": "Kanpur Leather SME Exporters", "region": "Kanpur, UP", "industry": "leather export", "problem": "export research", "evidence": ["Rs.735cr export drop FY25-26 on US tariffs (FIEO)", "Rs.7000cr leather exports, FTAs opening new lanes"], "triggers": ["tariff shock", "FTA opening"], "estimated_monthly_value": 50000, "recommended_pilot": 5000, "contactability": 0.45, "confidence": 0.6, "source": "press"},
]


def main(persist: bool = True) -> dict:
    bundle = collect("manual", SEEDS)
    ranked = rank(bundle["items"], limit=20)
    offers = []
    for r in ranked:
        tpl_name = TEMPLATE_FOR.get(r["problem"])
        if tpl_name and r["decision"] in ("PILOT", "OUTREACH") and len(offers) < 5:
            inst = instantiate(get_template(tpl_name), r)
            offers.append({"company": r["company"], "problem": r["problem"],
                           "price": inst["quote"]["price"],
                           "draft": draft_message(r, {"deliverable": inst["proposal"]["expected_outcome"]["deliverable"]},
                                                  inst["quote"]["price"])["body"][:200]})
    persisted = 0
    if persist:
        ledger.ensure_schema()
        for r in ranked:
            ledger.record_prospect({k: r[k] for k in (
                "prospect_id", "company", "problem", "region", "industry",
                "evidence", "triggers", "estimated_monthly_value",
                "recommended_pilot", "contactability", "confidence")}, )
            persisted += 1
    report = {"prospects": len(ranked), "persisted": persisted,
              "top20": [{"company": r["company"], "problem": r["problem"],
                         "pain": r["pain_score"], "decision": r["decision"]} for r in ranked],
              "top5_offers": offers,
              "note": "No messages sent. OUTREACH/PILOT = cleared for contact lookup + human approval."}
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main(persist="--no-persist" not in sys.argv)
