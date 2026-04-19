#!/usr/bin/env python3
"""
Marketing ROI Calculator - Calculate ROI, CAC, and efficiency across channels.

Computes per-channel ROI, blended CAC, marketing efficiency ratio (MER),
pipeline contribution, and produces board-ready marketing performance reports.
"""

import argparse
import json
import sys
from datetime import datetime


CHANNEL_BENCHMARKS = {
    "organic_search": {"cac_range": "Low", "quality": "Medium-High", "scalability": "Medium"},
    "paid_search": {"cac_range": "Medium", "quality": "High", "scalability": "High"},
    "social_organic": {"cac_range": "Low", "quality": "Low-Medium", "scalability": "Medium"},
    "social_paid": {"cac_range": "Medium", "quality": "Medium", "scalability": "High"},
    "content": {"cac_range": "Low", "quality": "High", "scalability": "Medium"},
    "events": {"cac_range": "High", "quality": "High", "scalability": "Low"},
    "partnerships": {"cac_range": "Medium", "quality": "High", "scalability": "Medium"},
    "email": {"cac_range": "Low", "quality": "Medium", "scalability": "Medium"},
    "outbound": {"cac_range": "High", "quality": "Medium-High", "scalability": "Medium"},
    "referral": {"cac_range": "Low", "quality": "Very High", "scalability": "Low"},
}


def calculate_roi(data: dict) -> dict:
    """Calculate marketing ROI across all channels."""
    channels = data.get("channels", [])
    total_revenue = data.get("total_revenue", 0)
    total_marketing_spend = data.get("total_marketing_spend", 0)
    arr = data.get("arr", 0)
    new_arr = data.get("new_arr_period", 0)

    results = {
        "timestamp": datetime.now().isoformat(),
        "period": data.get("period", "Quarter"),
        "channel_analysis": [],
        "blended_metrics": {},
        "efficiency_metrics": {},
        "attribution": {},
        "recommendations": [],
        "board_summary": {},
    }

    total_spend = 0
    total_pipeline = 0
    total_customers = 0
    total_mqls = 0

    for ch in channels:
        name = ch.get("name", "Unknown")
        spend = ch.get("spend", 0)
        leads = ch.get("leads", 0)
        mqls = ch.get("mqls", 0)
        sqls = ch.get("sqls", 0)
        opportunities = ch.get("opportunities", 0)
        customers = ch.get("customers_won", 0)
        pipeline = ch.get("pipeline_generated", 0)
        revenue = ch.get("revenue_attributed", 0)

        # Per-channel metrics
        cpl = spend / leads if leads > 0 else 0
        cpmql = spend / mqls if mqls > 0 else 0
        cpsql = spend / sqls if sqls > 0 else 0
        cac = spend / customers if customers > 0 else 0
        roi = ((revenue - spend) / spend * 100) if spend > 0 else 0
        pipeline_roi = (pipeline / spend) if spend > 0 else 0
        lead_to_mql = (mqls / leads * 100) if leads > 0 else 0
        mql_to_sql = (sqls / mqls * 100) if mqls > 0 else 0
        sql_to_close = (customers / sqls * 100) if sqls > 0 else 0

        channel_result = {
            "name": name,
            "spend": spend,
            "leads": leads,
            "mqls": mqls,
            "sqls": sqls,
            "opportunities": opportunities,
            "customers_won": customers,
            "pipeline_generated": pipeline,
            "revenue_attributed": revenue,
            "cost_per_lead": round(cpl),
            "cost_per_mql": round(cpmql),
            "cost_per_sql": round(cpsql),
            "cac": round(cac),
            "roi_pct": round(roi, 1),
            "pipeline_roi": round(pipeline_roi, 1),
            "lead_to_mql_pct": round(lead_to_mql, 1),
            "mql_to_sql_pct": round(mql_to_sql, 1),
            "sql_to_close_pct": round(sql_to_close, 1),
            "benchmark": CHANNEL_BENCHMARKS.get(name.lower().replace(" ", "_"), {}),
            "efficiency_rating": "Efficient" if roi > 200 else "Good" if roi > 100 else "Break-even" if roi > 0 else "Losing",
        }
        results["channel_analysis"].append(channel_result)

        total_spend += spend
        total_pipeline += pipeline
        total_customers += customers
        total_mqls += mqls

    # Sort by ROI
    results["channel_analysis"].sort(key=lambda x: x["roi_pct"], reverse=True)

    # Blended metrics
    blended_cac = total_spend / total_customers if total_customers > 0 else 0
    blended_cpmql = total_spend / total_mqls if total_mqls > 0 else 0
    results["blended_metrics"] = {
        "total_spend": round(total_spend),
        "total_pipeline": round(total_pipeline),
        "total_customers": total_customers,
        "total_mqls": total_mqls,
        "blended_cac": round(blended_cac),
        "blended_cost_per_mql": round(blended_cpmql),
        "pipeline_to_spend_ratio": round(total_pipeline / total_spend, 1) if total_spend > 0 else 0,
    }

    # Marketing Efficiency Ratio (MER) and other efficiency metrics
    mer = new_arr / total_marketing_spend if total_marketing_spend > 0 else 0
    marketing_pct_revenue = (total_marketing_spend / total_revenue * 100) if total_revenue > 0 else 0
    pipeline_coverage = (total_pipeline / new_arr) if new_arr > 0 else 0

    results["efficiency_metrics"] = {
        "marketing_efficiency_ratio": round(mer, 2),
        "mer_interpretation": "Strong" if mer > 2.0 else "Good" if mer > 1.0 else "Needs improvement" if mer > 0.5 else "Poor",
        "marketing_pct_of_revenue": round(marketing_pct_revenue, 1),
        "benchmark_pct_revenue": "8-12% (Series A), 15-25% (Growth)",
        "pipeline_coverage": round(pipeline_coverage, 1),
        "pipeline_coverage_target": "3-4x",
        "cac_payback_note": f"Blended CAC ${blended_cac:,.0f} - divide by monthly gross profit per customer for payback months",
    }

    # Attribution summary
    if results["channel_analysis"]:
        top_roi = results["channel_analysis"][0]
        top_pipeline = max(results["channel_analysis"], key=lambda x: x["pipeline_generated"])
        top_volume = max(results["channel_analysis"], key=lambda x: x["mqls"])
        results["attribution"] = {
            "top_roi_channel": f"{top_roi['name']} ({top_roi['roi_pct']:.0f}% ROI)",
            "top_pipeline_channel": f"{top_pipeline['name']} (${top_pipeline['pipeline_generated']:,.0f})",
            "top_volume_channel": f"{top_volume['name']} ({top_volume['mqls']} MQLs)",
        }

    # Recommendations
    losing = [c for c in results["channel_analysis"] if c["roi_pct"] < 0]
    if losing:
        results["recommendations"].append(
            f"Cut or pause {len(losing)} losing channel(s): {', '.join(c['name'] for c in losing)}"
        )
    efficient = [c for c in results["channel_analysis"] if c["roi_pct"] > 200]
    if efficient:
        results["recommendations"].append(
            f"Increase investment in {len(efficient)} high-ROI channel(s): {', '.join(c['name'] for c in efficient)}"
        )
    if marketing_pct_revenue > 25:
        results["recommendations"].append(
            f"Marketing spend at {marketing_pct_revenue:.0f}% of revenue - above typical benchmark. Review efficiency."
        )

    # Board summary
    results["board_summary"] = {
        "total_spend": f"${total_spend:,.0f}",
        "pipeline_generated": f"${total_pipeline:,.0f}",
        "blended_cac": f"${blended_cac:,.0f}",
        "mer": f"{mer:.2f}x",
        "top_channel": results["attribution"].get("top_roi_channel", "N/A"),
        "channels_losing": len(losing),
    }

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 78,
        "MARKETING ROI REPORT",
        "=" * 78,
        f"Period: {results['period']}  |  Date: {results['timestamp'][:10]}",
        "",
        f"{'Channel':<16} {'Spend':>10} {'MQLs':>6} {'Cust':>5} {'CAC':>8} {'Pipeline':>10} {'ROI':>7} {'Rating':<12}",
        "-" * 78,
    ]

    for ch in results["channel_analysis"]:
        lines.append(
            f"{ch['name']:<16} ${ch['spend']:>9,.0f} {ch['mqls']:>6} {ch['customers_won']:>5} "
            f"${ch['cac']:>7,.0f} ${ch['pipeline_generated']:>9,.0f} {ch['roi_pct']:>+6.0f}% {ch['efficiency_rating']:<12}"
        )

    bm = results["blended_metrics"]
    em = results["efficiency_metrics"]
    lines.extend([
        "",
        "BLENDED METRICS:",
        f"  Total Spend: ${bm['total_spend']:,.0f}  |  Pipeline: ${bm['total_pipeline']:,.0f}  |  Customers: {bm['total_customers']}",
        f"  Blended CAC: ${bm['blended_cac']:,.0f}  |  Pipeline:Spend = {bm['pipeline_to_spend_ratio']:.1f}x",
        "",
        "EFFICIENCY:",
        f"  Marketing Efficiency Ratio (MER): {em['marketing_efficiency_ratio']:.2f}x ({em['mer_interpretation']})",
        f"  Marketing % of Revenue: {em['marketing_pct_of_revenue']:.1f}% (benchmark: {em['benchmark_pct_revenue']})",
        f"  Pipeline Coverage: {em['pipeline_coverage']:.1f}x (target: {em['pipeline_coverage_target']})",
    ])

    if results["recommendations"]:
        lines.extend(["", "RECOMMENDATIONS:"])
        for r in results["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 78])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Calculate marketing ROI and efficiency metrics")
    parser.add_argument("--input", "-i", help="JSON file with marketing data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "period": "Q4 2025",
            "arr": 8000000,
            "new_arr_period": 600000,
            "total_revenue": 2000000,
            "total_marketing_spend": 600000,
            "channels": [
                {"name": "Paid Search", "spend": 150000, "leads": 3000, "mqls": 450, "sqls": 112, "opportunities": 56, "customers_won": 14, "pipeline_generated": 840000, "revenue_attributed": 420000},
                {"name": "Content", "spend": 80000, "leads": 5000, "mqls": 600, "sqls": 90, "opportunities": 45, "customers_won": 11, "pipeline_generated": 660000, "revenue_attributed": 330000},
                {"name": "LinkedIn Ads", "spend": 120000, "leads": 2000, "mqls": 380, "sqls": 76, "opportunities": 38, "customers_won": 8, "pipeline_generated": 480000, "revenue_attributed": 240000},
                {"name": "Events", "spend": 100000, "leads": 400, "mqls": 120, "sqls": 48, "opportunities": 24, "customers_won": 6, "pipeline_generated": 360000, "revenue_attributed": 180000},
                {"name": "Outbound", "spend": 90000, "leads": 800, "mqls": 200, "sqls": 60, "opportunities": 30, "customers_won": 5, "pipeline_generated": 300000, "revenue_attributed": 100000},
                {"name": "Referral", "spend": 10000, "leads": 100, "mqls": 60, "sqls": 30, "opportunities": 18, "customers_won": 8, "pipeline_generated": 480000, "revenue_attributed": 320000},
            ],
        }

    results = calculate_roi(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
