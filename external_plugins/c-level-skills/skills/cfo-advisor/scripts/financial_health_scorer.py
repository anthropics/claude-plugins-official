#!/usr/bin/env python3
"""
Financial Health Scorer - Comprehensive SaaS financial health assessment.

Calculates Rule of 40, burn multiple, magic number, CAC payback, LTV:CAC,
NRR, and composite financial health score with investor-grade benchmarks.
"""

import argparse
import json
import sys
from datetime import datetime


BENCHMARKS = {
    "rule_of_40": {"excellent": 60, "good": 40, "acceptable": 20, "poor": 0},
    "burn_multiple": {"excellent": 1.0, "good": 1.5, "acceptable": 2.0, "poor": 3.0},
    "ltv_cac_ratio": {"excellent": 5.0, "good": 3.0, "acceptable": 2.0, "poor": 1.0},
    "cac_payback_months": {"excellent": 6, "good": 12, "acceptable": 18, "poor": 24},
    "nrr_pct": {"excellent": 130, "good": 115, "acceptable": 100, "poor": 90},
    "gross_margin_pct": {"excellent": 85, "good": 75, "acceptable": 65, "poor": 50},
    "magic_number": {"excellent": 1.5, "good": 1.0, "acceptable": 0.75, "poor": 0.5},
    "arr_per_employee": {"excellent": 250000, "good": 180000, "acceptable": 120000, "poor": 80000},
    "runway_months": {"excellent": 24, "good": 18, "acceptable": 12, "poor": 6},
}

WEIGHTS = {
    "rule_of_40": 0.15,
    "burn_multiple": 0.15,
    "ltv_cac_ratio": 0.12,
    "cac_payback_months": 0.10,
    "nrr_pct": 0.15,
    "gross_margin_pct": 0.10,
    "magic_number": 0.08,
    "arr_per_employee": 0.07,
    "runway_months": 0.08,
}


def score_metric(value: float, metric_name: str) -> dict:
    """Score a single metric against benchmarks."""
    bench = BENCHMARKS.get(metric_name, {})
    if not bench:
        return {"score": 50, "rating": "N/A", "benchmark_note": "No benchmark available"}

    # Determine if higher or lower is better
    lower_is_better = metric_name in ["burn_multiple", "cac_payback_months"]

    if lower_is_better:
        if value <= bench["excellent"]:
            score, rating = 100, "Excellent"
        elif value <= bench["good"]:
            pct = (bench["good"] - value) / (bench["good"] - bench["excellent"])
            score, rating = 75 + pct * 25, "Good"
        elif value <= bench["acceptable"]:
            pct = (bench["acceptable"] - value) / (bench["acceptable"] - bench["good"])
            score, rating = 50 + pct * 25, "Acceptable"
        elif value <= bench["poor"]:
            pct = (bench["poor"] - value) / (bench["poor"] - bench["acceptable"])
            score, rating = 25 + pct * 25, "Below Average"
        else:
            score, rating = max(0, 25 * bench["poor"] / value), "Poor"
    else:
        if value >= bench["excellent"]:
            score, rating = 100, "Excellent"
        elif value >= bench["good"]:
            pct = (value - bench["good"]) / (bench["excellent"] - bench["good"])
            score, rating = 75 + pct * 25, "Good"
        elif value >= bench["acceptable"]:
            pct = (value - bench["acceptable"]) / (bench["good"] - bench["acceptable"])
            score, rating = 50 + pct * 25, "Acceptable"
        elif value >= bench["poor"]:
            pct = (value - bench["poor"]) / (bench["acceptable"] - bench["poor"])
            score, rating = 25 + pct * 25, "Below Average"
        else:
            score, rating = max(0, 25 * value / bench["poor"]) if bench["poor"] != 0 else 0, "Poor"

    return {
        "score": round(min(100, max(0, score)), 1),
        "rating": rating,
        "benchmark_excellent": bench["excellent"],
        "benchmark_good": bench["good"],
    }


def calculate_health(data: dict) -> dict:
    """Calculate comprehensive financial health score."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "company": data.get("company", "Company"),
        "stage": data.get("stage", "Unknown"),
        "composite_score": 0,
        "composite_rating": "",
        "metrics": {},
        "alerts": [],
        "investor_readiness": {},
        "recommendations": [],
    }

    # Calculate derived metrics
    arr = data.get("arr", 0)
    revenue_growth_pct = data.get("revenue_growth_pct", 0)
    profit_margin_pct = data.get("profit_margin_pct", 0)
    net_burn = data.get("net_burn_monthly", 0)
    net_new_arr = data.get("net_new_arr_quarterly", 0)
    sales_marketing_spend = data.get("sales_marketing_spend_quarterly", 0)
    new_customers = data.get("new_customers_quarterly", 0)
    arpu_monthly = data.get("arpu_monthly", 0)
    gross_margin_pct = data.get("gross_margin_pct", 0)
    customer_lifetime_months = data.get("customer_lifetime_months", 36)
    nrr_pct = data.get("nrr_pct", 100)
    headcount = data.get("headcount", 1)
    cash = data.get("cash_balance", 0)
    prev_quarter_arr = data.get("prev_quarter_arr", 0)

    # Rule of 40
    rule_of_40 = revenue_growth_pct + profit_margin_pct
    results["metrics"]["rule_of_40"] = {
        "value": round(rule_of_40, 1),
        "formula": f"{revenue_growth_pct}% growth + {profit_margin_pct}% margin",
        **score_metric(rule_of_40, "rule_of_40"),
    }

    # Burn Multiple
    burn_multiple = (net_burn * 3 / net_new_arr) if net_new_arr > 0 else 99
    results["metrics"]["burn_multiple"] = {
        "value": round(burn_multiple, 2),
        "formula": f"${net_burn * 3:,.0f} quarterly burn / ${net_new_arr:,.0f} net new ARR",
        **score_metric(burn_multiple, "burn_multiple"),
    }

    # LTV:CAC
    cac = (sales_marketing_spend / new_customers) if new_customers > 0 else 0
    ltv = arpu_monthly * (gross_margin_pct / 100) * customer_lifetime_months
    ltv_cac = (ltv / cac) if cac > 0 else 0
    results["metrics"]["ltv_cac_ratio"] = {
        "value": round(ltv_cac, 1),
        "cac": round(cac),
        "ltv": round(ltv),
        "formula": f"${ltv:,.0f} LTV / ${cac:,.0f} CAC",
        **score_metric(ltv_cac, "ltv_cac_ratio"),
    }

    # CAC Payback
    monthly_contribution = arpu_monthly * (gross_margin_pct / 100)
    cac_payback = (cac / monthly_contribution) if monthly_contribution > 0 else 99
    results["metrics"]["cac_payback_months"] = {
        "value": round(cac_payback, 1),
        "formula": f"${cac:,.0f} CAC / ${monthly_contribution:,.0f} monthly contribution",
        **score_metric(cac_payback, "cac_payback_months"),
    }

    # NRR
    results["metrics"]["nrr_pct"] = {
        "value": round(nrr_pct, 1),
        **score_metric(nrr_pct, "nrr_pct"),
    }

    # Gross Margin
    results["metrics"]["gross_margin_pct"] = {
        "value": round(gross_margin_pct, 1),
        **score_metric(gross_margin_pct, "gross_margin_pct"),
    }

    # Magic Number
    arr_growth_quarterly = arr - prev_quarter_arr if prev_quarter_arr > 0 else net_new_arr
    magic_number = (arr_growth_quarterly / sales_marketing_spend) if sales_marketing_spend > 0 else 0
    results["metrics"]["magic_number"] = {
        "value": round(magic_number, 2),
        "formula": f"${arr_growth_quarterly:,.0f} ARR growth / ${sales_marketing_spend:,.0f} S&M spend",
        **score_metric(magic_number, "magic_number"),
    }

    # ARR per Employee
    arr_per_emp = arr / headcount if headcount > 0 else 0
    results["metrics"]["arr_per_employee"] = {
        "value": round(arr_per_emp),
        "formula": f"${arr:,.0f} ARR / {headcount} employees",
        **score_metric(arr_per_emp, "arr_per_employee"),
    }

    # Runway
    runway = (cash / net_burn) if net_burn > 0 else 999
    results["metrics"]["runway_months"] = {
        "value": round(runway, 1),
        "formula": f"${cash:,.0f} cash / ${net_burn:,.0f} monthly burn",
        **score_metric(runway, "runway_months"),
    }

    # Composite score
    composite = 0
    for metric_name, weight in WEIGHTS.items():
        if metric_name in results["metrics"]:
            composite += results["metrics"][metric_name]["score"] * weight
    results["composite_score"] = round(composite, 1)

    if composite >= 80:
        results["composite_rating"] = "Strong"
    elif composite >= 65:
        results["composite_rating"] = "Healthy"
    elif composite >= 50:
        results["composite_rating"] = "Acceptable"
    elif composite >= 35:
        results["composite_rating"] = "Needs Attention"
    else:
        results["composite_rating"] = "Critical"

    # Alerts
    for name, metric in results["metrics"].items():
        if metric["rating"] == "Poor":
            results["alerts"].append(f"CRITICAL: {name} = {metric['value']} (rated Poor)")
        elif metric["rating"] == "Below Average":
            results["alerts"].append(f"WARNING: {name} = {metric['value']} (Below Average)")

    if runway < 6:
        results["alerts"].insert(0, f"URGENT: Runway is {runway:.0f} months. Extend immediately.")

    # Investor readiness
    investor_ready = sum(1 for m in results["metrics"].values() if m["rating"] in ["Excellent", "Good"])
    total = len(results["metrics"])
    results["investor_readiness"] = {
        "metrics_at_benchmark": investor_ready,
        "total_metrics": total,
        "readiness_pct": round(investor_ready / total * 100) if total > 0 else 0,
        "verdict": "Fundraise-ready" if investor_ready >= 6 else
                   "Near-ready (fix 1-2 metrics)" if investor_ready >= 4 else
                   "Not ready (improve fundamentals first)",
    }

    # Recommendations
    poor_metrics = [(n, m) for n, m in results["metrics"].items() if m["rating"] in ["Poor", "Below Average"]]
    poor_metrics.sort(key=lambda x: WEIGHTS.get(x[0], 0), reverse=True)
    for name, metric in poor_metrics[:3]:
        results["recommendations"].append(
            f"Improve {name}: currently {metric['value']}, target {metric['benchmark_good']}+"
        )

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 65,
        "FINANCIAL HEALTH SCORECARD",
        "=" * 65,
        f"Company: {results['company']}  |  Stage: {results['stage']}",
        f"Date: {results['timestamp'][:10]}",
        f"COMPOSITE SCORE: {results['composite_score']}/100 ({results['composite_rating']})",
        "",
        f"{'Metric':<22} {'Value':>10} {'Score':>7} {'Rating':<15}",
        "-" * 65,
    ]

    for name, m in results["metrics"].items():
        val = m["value"]
        if name in ["gross_margin_pct", "nrr_pct", "rule_of_40"]:
            val_str = f"{val:.1f}%"
        elif name in ["burn_multiple", "ltv_cac_ratio", "magic_number"]:
            val_str = f"{val:.2f}x"
        elif name in ["cac_payback_months", "runway_months"]:
            val_str = f"{val:.0f} mo"
        elif name == "arr_per_employee":
            val_str = f"${val:,.0f}"
        else:
            val_str = f"{val}"
        lines.append(f"{name:<22} {val_str:>10} {m['score']:>6.0f}/100 {m['rating']:<15}")

    if results["alerts"]:
        lines.extend(["", "ALERTS:"])
        for a in results["alerts"]:
            lines.append(f"  {a}")

    ir = results["investor_readiness"]
    lines.extend([
        "",
        f"INVESTOR READINESS: {ir['readiness_pct']}% ({ir['metrics_at_benchmark']}/{ir['total_metrics']} metrics at benchmark)",
        f"  Verdict: {ir['verdict']}",
    ])

    if results["recommendations"]:
        lines.extend(["", "TOP RECOMMENDATIONS:"])
        for r in results["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 65])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Calculate SaaS financial health score")
    parser.add_argument("--input", "-i", help="JSON file with financial data")
    parser.add_argument("--arr", type=float, help="Annual Recurring Revenue")
    parser.add_argument("--revenue-growth", type=float, help="Revenue growth rate (%%)")
    parser.add_argument("--profit-margin", type=float, help="Profit margin (%%)")
    parser.add_argument("--burn", type=float, help="Monthly net burn")
    parser.add_argument("--cash", type=float, help="Cash balance")
    parser.add_argument("--nrr", type=float, help="Net Revenue Retention (%%)")
    parser.add_argument("--gross-margin", type=float, help="Gross margin (%%)")
    parser.add_argument("--headcount", type=int, help="Total headcount")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    elif args.arr:
        data = {
            "company": "Company",
            "stage": "Growth",
            "arr": args.arr,
            "revenue_growth_pct": args.revenue_growth or 50,
            "profit_margin_pct": args.profit_margin or -20,
            "net_burn_monthly": args.burn or 0,
            "net_new_arr_quarterly": args.arr * 0.08,
            "sales_marketing_spend_quarterly": args.arr * 0.12,
            "new_customers_quarterly": 25,
            "arpu_monthly": args.arr / 12 / 100,
            "gross_margin_pct": args.gross_margin or 75,
            "nrr_pct": args.nrr or 110,
            "headcount": args.headcount or 50,
            "cash_balance": args.cash or 5000000,
        }
    else:
        # Demo data
        data = {
            "company": "SaaSCo",
            "stage": "Series A",
            "arr": 3000000,
            "prev_quarter_arr": 2700000,
            "revenue_growth_pct": 95,
            "profit_margin_pct": -40,
            "net_burn_monthly": 350000,
            "net_new_arr_quarterly": 540000,
            "sales_marketing_spend_quarterly": 450000,
            "new_customers_quarterly": 20,
            "arpu_monthly": 2500,
            "gross_margin_pct": 78,
            "customer_lifetime_months": 36,
            "nrr_pct": 115,
            "headcount": 35,
            "cash_balance": 5200000,
        }

    results = calculate_health(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
