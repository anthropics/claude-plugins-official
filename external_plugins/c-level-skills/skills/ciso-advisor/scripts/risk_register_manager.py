#!/usr/bin/env python3
"""
Risk Register Manager - Quantified cyber risk register with ALE calculations.

Manages a risk register with Single Loss Expectancy (SLE) x Annual Rate of
Occurrence (ARO) = Annual Loss Expectancy (ALE). Calculates mitigation ROI,
prioritizes by business impact, and produces board-ready risk reports.
"""

import argparse
import json
import sys
from datetime import datetime


DEFAULT_RISKS = [
    {"id": "R-001", "threat": "Data breach (customer PII)", "asset": "Customer database", "sle": 2500000, "aro": 0.15, "mitigation_cost": 120000, "mitigation_effectiveness": 0.70, "category": "data", "owner": "CISO"},
    {"id": "R-002", "threat": "Ransomware attack", "asset": "Production systems", "sle": 1800000, "aro": 0.10, "mitigation_cost": 80000, "mitigation_effectiveness": 0.75, "category": "malware", "owner": "CISO"},
    {"id": "R-003", "threat": "Insider threat (IP theft)", "asset": "Source code / trade secrets", "sle": 500000, "aro": 0.05, "mitigation_cost": 40000, "mitigation_effectiveness": 0.50, "category": "insider", "owner": "CISO"},
    {"id": "R-004", "threat": "DDoS attack", "asset": "Customer-facing application", "sle": 200000, "aro": 0.20, "mitigation_cost": 30000, "mitigation_effectiveness": 0.80, "category": "availability", "owner": "CTO"},
    {"id": "R-005", "threat": "Third-party vendor breach", "asset": "Vendor with PII access", "sle": 1200000, "aro": 0.08, "mitigation_cost": 25000, "mitigation_effectiveness": 0.60, "category": "supply_chain", "owner": "CISO"},
    {"id": "R-006", "threat": "Phishing / credential theft", "asset": "Employee accounts", "sle": 150000, "aro": 0.30, "mitigation_cost": 20000, "mitigation_effectiveness": 0.65, "category": "social_engineering", "owner": "CISO"},
    {"id": "R-007", "threat": "Cloud misconfiguration", "asset": "Cloud infrastructure", "sle": 800000, "aro": 0.12, "mitigation_cost": 35000, "mitigation_effectiveness": 0.70, "category": "cloud", "owner": "CTO"},
    {"id": "R-008", "threat": "Compliance violation (GDPR)", "asset": "EU customer data", "sle": 3000000, "aro": 0.05, "mitigation_cost": 100000, "mitigation_effectiveness": 0.80, "category": "compliance", "owner": "Legal"},
]


def analyze_register(risks: list) -> dict:
    """Analyze risk register and calculate business impact."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_risks": len(risks),
        "total_ale": 0,
        "total_residual_ale": 0,
        "total_mitigation_cost": 0,
        "risk_details": [],
        "by_priority": {"critical": [], "high": [], "medium": [], "low": []},
        "by_category": {},
        "roi_ranked": [],
        "budget_summary": {},
        "board_report": {},
    }

    for risk in risks:
        sle = risk.get("sle", 0)
        aro = risk.get("aro", 0)
        ale = sle * aro
        mit_cost = risk.get("mitigation_cost", 0)
        mit_eff = risk.get("mitigation_effectiveness", 0)

        residual_ale = ale * (1 - mit_eff)
        ale_reduction = ale - residual_ale
        roi = (ale_reduction / mit_cost) if mit_cost > 0 else 0

        # Priority based on ALE
        if ale >= 200000:
            priority = "critical"
        elif ale >= 50000:
            priority = "high"
        elif ale >= 10000:
            priority = "medium"
        else:
            priority = "low"

        detail = {
            "id": risk.get("id", ""),
            "threat": risk.get("threat", ""),
            "asset": risk.get("asset", ""),
            "owner": risk.get("owner", "Unassigned"),
            "category": risk.get("category", "other"),
            "sle": sle,
            "aro": aro,
            "ale": round(ale),
            "mitigation_cost": mit_cost,
            "mitigation_effectiveness_pct": round(mit_eff * 100),
            "residual_ale": round(residual_ale),
            "ale_reduction": round(ale_reduction),
            "roi": round(roi, 1),
            "priority": priority,
        }

        results["risk_details"].append(detail)
        results["total_ale"] += ale
        results["total_residual_ale"] += residual_ale
        results["total_mitigation_cost"] += mit_cost
        results["by_priority"][priority].append(detail)

        cat = risk.get("category", "other")
        if cat not in results["by_category"]:
            results["by_category"][cat] = {"count": 0, "total_ale": 0}
        results["by_category"][cat]["count"] += 1
        results["by_category"][cat]["total_ale"] += ale

    results["total_ale"] = round(results["total_ale"])
    results["total_residual_ale"] = round(results["total_residual_ale"])
    results["total_mitigation_cost"] = round(results["total_mitigation_cost"])

    # ROI ranked
    results["roi_ranked"] = sorted(results["risk_details"], key=lambda x: x["roi"], reverse=True)

    # Budget summary
    total_reduction = results["total_ale"] - results["total_residual_ale"]
    results["budget_summary"] = {
        "total_risk_exposure": results["total_ale"],
        "recommended_investment": results["total_mitigation_cost"],
        "expected_risk_reduction": round(total_reduction),
        "residual_exposure": results["total_residual_ale"],
        "portfolio_roi": round(total_reduction / results["total_mitigation_cost"], 1) if results["total_mitigation_cost"] > 0 else 0,
        "coverage_pct": round(total_reduction / results["total_ale"] * 100) if results["total_ale"] > 0 else 0,
    }

    # Board report
    results["board_report"] = {
        "headline": f"${results['total_ale']:,.0f} total annual risk exposure, ${results['total_residual_ale']:,.0f} after mitigations",
        "critical_risks": len(results["by_priority"]["critical"]),
        "high_risks": len(results["by_priority"]["high"]),
        "top_risk": results["roi_ranked"][0]["threat"] if results["roi_ranked"] else "None",
        "investment_ask": f"${results['total_mitigation_cost']:,.0f} to reduce exposure by {results['budget_summary']['coverage_pct']}%",
        "portfolio_roi": f"{results['budget_summary']['portfolio_roi']:.1f}x",
    }

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 75,
        "CYBER RISK REGISTER",
        "=" * 75,
        f"Date: {results['timestamp'][:10]}",
        f"Total Risks: {results['total_risks']}  |  Total ALE: ${results['total_ale']:,.0f}  |  Residual ALE: ${results['total_residual_ale']:,.0f}",
        "",
        f"{'ID':<7} {'Threat':<30} {'SLE':>10} {'ARO':>5} {'ALE':>10} {'Mit $':>8} {'ROI':>5} {'Priority':<9}",
        "-" * 75,
    ]

    sorted_risks = sorted(results["risk_details"], key=lambda x: x["ale"], reverse=True)
    for r in sorted_risks:
        lines.append(
            f"{r['id']:<7} {r['threat']:<30} ${r['sle']:>9,.0f} {r['aro']:>4.0%} "
            f"${r['ale']:>9,.0f} ${r['mitigation_cost']:>7,.0f} {r['roi']:>4.1f}x "
            f"{r['priority'].upper():<9}"
        )

    lines.extend(["", "TOP INVESTMENTS BY ROI:"])
    for r in results["roi_ranked"][:5]:
        lines.append(
            f"  {r['roi']:.1f}x ROI: {r['threat']} - ${r['mitigation_cost']:,.0f} investment "
            f"reduces ALE by ${r['ale_reduction']:,.0f}"
        )

    bs = results["budget_summary"]
    lines.extend([
        "",
        "BUDGET SUMMARY:",
        f"  Total Exposure:  ${bs['total_risk_exposure']:>12,.0f}",
        f"  Investment Ask:  ${bs['recommended_investment']:>12,.0f}",
        f"  Risk Reduction:  ${bs['expected_risk_reduction']:>12,.0f} ({bs['coverage_pct']}% coverage)",
        f"  Residual Risk:   ${bs['residual_exposure']:>12,.0f}",
        f"  Portfolio ROI:   {bs['portfolio_roi']:.1f}x",
    ])

    br = results["board_report"]
    lines.extend([
        "",
        "BOARD SUMMARY:",
        f"  {br['headline']}",
        f"  Critical: {br['critical_risks']} | High: {br['high_risks']}",
        f"  Top Risk: {br['top_risk']}",
        f"  Ask: {br['investment_ask']}",
        "",
        "=" * 75,
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Manage and analyze cyber risk register")
    parser.add_argument("--input", "-i", help="JSON file with risk register data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--sort-by", choices=["ale", "roi", "priority"], default="ale", help="Sort risks by (default: ale)")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
            risks = data if isinstance(data, list) else data.get("risks", DEFAULT_RISKS)
    else:
        risks = DEFAULT_RISKS

    results = analyze_register(risks)

    if args.sort_by == "roi":
        results["risk_details"] = results["roi_ranked"]
    elif args.sort_by == "priority":
        results["risk_details"] = sorted(results["risk_details"], key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]])

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
