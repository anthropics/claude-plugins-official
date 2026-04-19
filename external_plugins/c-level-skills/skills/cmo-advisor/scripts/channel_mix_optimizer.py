#!/usr/bin/env python3
"""
Channel Mix Optimizer - Optimize marketing budget allocation across channels.

Analyzes historical channel performance and recommends budget reallocation
based on ROI, efficiency frontiers, and diminishing returns modeling.
"""

import argparse
import json
import sys
from datetime import datetime
import math


def optimize_mix(data: dict) -> dict:
    """Optimize channel budget allocation."""
    channels = data.get("channels", [])
    total_budget = data.get("total_budget", 0)
    target_cac = data.get("target_cac", None)
    optimization_goal = data.get("optimization_goal", "roi")  # roi, pipeline, volume

    results = {
        "timestamp": datetime.now().isoformat(),
        "total_budget": total_budget,
        "optimization_goal": optimization_goal,
        "current_allocation": [],
        "recommended_allocation": [],
        "reallocation_summary": [],
        "projected_impact": {},
        "constraints": [],
        "recommendations": [],
    }

    # Analyze current performance
    channel_metrics = []
    for ch in channels:
        name = ch.get("name", "")
        spend = ch.get("current_spend", 0)
        pipeline = ch.get("pipeline_generated", 0)
        customers = ch.get("customers_won", 0)
        revenue = ch.get("revenue_attributed", 0)

        roi = ((revenue - spend) / spend) if spend > 0 else 0
        cac = spend / customers if customers > 0 else float("inf")
        pipeline_per_dollar = pipeline / spend if spend > 0 else 0
        efficiency = revenue / spend if spend > 0 else 0

        # Diminishing returns factor (higher spend = lower marginal return)
        saturation = ch.get("saturation_pct", 50) / 100
        marginal_efficiency = efficiency * (1 - saturation * 0.5)

        channel_metrics.append({
            "name": name,
            "current_spend": spend,
            "pct_of_budget": round(spend / total_budget * 100, 1) if total_budget > 0 else 0,
            "roi": round(roi, 2),
            "cac": round(cac) if cac != float("inf") else 0,
            "pipeline_per_dollar": round(pipeline_per_dollar, 2),
            "efficiency": round(efficiency, 2),
            "marginal_efficiency": round(marginal_efficiency, 2),
            "saturation_pct": ch.get("saturation_pct", 50),
            "min_spend": ch.get("min_spend", 0),
            "max_spend": ch.get("max_spend", spend * 3),
            "customers_won": customers,
            "pipeline_generated": pipeline,
            "revenue_attributed": revenue,
        })

    results["current_allocation"] = channel_metrics

    # Optimize based on goal
    if optimization_goal == "roi":
        sort_key = "marginal_efficiency"
    elif optimization_goal == "pipeline":
        sort_key = "pipeline_per_dollar"
    else:
        sort_key = "customers_won"

    # Sort by efficiency metric
    ranked = sorted(channel_metrics, key=lambda x: x[sort_key], reverse=True)

    # Allocate budget using efficiency-weighted distribution
    remaining_budget = total_budget
    recommended = []

    # First pass: ensure minimums
    for ch in ranked:
        min_spend = ch["min_spend"]
        if min_spend > 0:
            remaining_budget -= min_spend

    # Second pass: allocate by efficiency
    total_efficiency = sum(ch[sort_key] for ch in ranked if ch[sort_key] > 0)

    for ch in ranked:
        if total_efficiency > 0 and ch[sort_key] > 0:
            share = ch[sort_key] / total_efficiency
            allocated = ch["min_spend"] + remaining_budget * share
            allocated = min(allocated, ch["max_spend"])
            allocated = max(allocated, ch["min_spend"])
        else:
            allocated = ch["min_spend"]

        change = allocated - ch["current_spend"]
        change_pct = (change / ch["current_spend"] * 100) if ch["current_spend"] > 0 else 0

        # Project new performance (linear approximation adjusted for saturation)
        scale_factor = allocated / ch["current_spend"] if ch["current_spend"] > 0 else 1
        # Apply diminishing returns
        effective_scale = 1 + (scale_factor - 1) * (1 - ch["saturation_pct"] / 200)
        proj_pipeline = ch["pipeline_generated"] * effective_scale
        proj_customers = ch["customers_won"] * effective_scale
        proj_revenue = ch["revenue_attributed"] * effective_scale

        rec = {
            "name": ch["name"],
            "current_spend": ch["current_spend"],
            "recommended_spend": round(allocated),
            "change": round(change),
            "change_pct": round(change_pct, 1),
            "action": "Increase" if change > 0 else "Decrease" if change < 0 else "Maintain",
            "projected_pipeline": round(proj_pipeline),
            "projected_customers": round(proj_customers),
            "projected_revenue": round(proj_revenue),
            "projected_cac": round(allocated / proj_customers) if proj_customers > 0 else 0,
        }
        recommended.append(rec)

        if abs(change_pct) > 10:
            results["reallocation_summary"].append({
                "channel": ch["name"],
                "action": rec["action"],
                "amount": abs(round(change)),
                "reason": f"{'High' if change > 0 else 'Low'} marginal efficiency ({ch[sort_key]:.2f})",
            })

    results["recommended_allocation"] = recommended

    # Projected impact
    current_total_pipeline = sum(ch["pipeline_generated"] for ch in channel_metrics)
    current_total_customers = sum(ch["customers_won"] for ch in channel_metrics)
    current_total_revenue = sum(ch["revenue_attributed"] for ch in channel_metrics)

    new_total_pipeline = sum(r["projected_pipeline"] for r in recommended)
    new_total_customers = sum(r["projected_customers"] for r in recommended)
    new_total_revenue = sum(r["projected_revenue"] for r in recommended)

    results["projected_impact"] = {
        "pipeline_change_pct": round((new_total_pipeline - current_total_pipeline) / current_total_pipeline * 100, 1) if current_total_pipeline > 0 else 0,
        "customer_change_pct": round((new_total_customers - current_total_customers) / current_total_customers * 100, 1) if current_total_customers > 0 else 0,
        "revenue_change_pct": round((new_total_revenue - current_total_revenue) / current_total_revenue * 100, 1) if current_total_revenue > 0 else 0,
        "new_blended_cac": round(total_budget / new_total_customers) if new_total_customers > 0 else 0,
        "current_blended_cac": round(total_budget / current_total_customers) if current_total_customers > 0 else 0,
    }

    # Recommendations
    increases = [r for r in recommended if r["action"] == "Increase"]
    decreases = [r for r in recommended if r["action"] == "Decrease"]
    if increases:
        results["recommendations"].append(
            f"Increase spend on {len(increases)} channel(s): {', '.join(r['name'] for r in increases[:3])}"
        )
    if decreases:
        results["recommendations"].append(
            f"Reduce spend on {len(decreases)} channel(s): {', '.join(r['name'] for r in decreases[:3])}"
        )
    if target_cac and results["projected_impact"]["new_blended_cac"] > target_cac:
        results["recommendations"].append(
            f"Projected CAC ${results['projected_impact']['new_blended_cac']:,.0f} exceeds target ${target_cac:,.0f}. Further optimization needed."
        )

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 80,
        "CHANNEL MIX OPTIMIZATION",
        "=" * 80,
        f"Budget: ${results['total_budget']:,.0f}  |  Goal: {results['optimization_goal'].upper()}",
        "",
        f"{'Channel':<16} {'Current':>10} {'Recommend':>10} {'Change':>10} {'Proj Pipeline':>14} {'Proj CAC':>9}",
        "-" * 80,
    ]

    for r in results["recommended_allocation"]:
        sign = "+" if r["change"] > 0 else ""
        lines.append(
            f"{r['name']:<16} ${r['current_spend']:>9,.0f} ${r['recommended_spend']:>9,.0f} "
            f"{sign}${r['change']:>8,.0f} ${r['projected_pipeline']:>13,.0f} ${r['projected_cac']:>8,.0f}"
        )

    pi = results["projected_impact"]
    lines.extend([
        "",
        "PROJECTED IMPACT:",
        f"  Pipeline: {pi['pipeline_change_pct']:+.1f}%  |  Customers: {pi['customer_change_pct']:+.1f}%  |  Revenue: {pi['revenue_change_pct']:+.1f}%",
        f"  Blended CAC: ${pi['current_blended_cac']:,.0f} -> ${pi['new_blended_cac']:,.0f}",
    ])

    if results["reallocation_summary"]:
        lines.extend(["", "KEY MOVES:"])
        for r in results["reallocation_summary"]:
            lines.append(f"  {r['action'].upper()}: {r['channel']} by ${r['amount']:,.0f} ({r['reason']})")

    if results["recommendations"]:
        lines.extend(["", "RECOMMENDATIONS:"])
        for r in results["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 80])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Optimize marketing channel budget allocation")
    parser.add_argument("--input", "-i", help="JSON file with channel performance data")
    parser.add_argument("--budget", type=float, help="Total marketing budget")
    parser.add_argument("--goal", choices=["roi", "pipeline", "volume"], default="roi", help="Optimization goal")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "total_budget": 600000,
            "optimization_goal": args.goal,
            "target_cac": 18000,
            "channels": [
                {"name": "Paid Search", "current_spend": 150000, "pipeline_generated": 840000, "customers_won": 14, "revenue_attributed": 420000, "saturation_pct": 60, "min_spend": 50000, "max_spend": 250000},
                {"name": "Content", "current_spend": 80000, "pipeline_generated": 660000, "customers_won": 11, "revenue_attributed": 330000, "saturation_pct": 30, "min_spend": 40000, "max_spend": 200000},
                {"name": "LinkedIn Ads", "current_spend": 120000, "pipeline_generated": 480000, "customers_won": 8, "revenue_attributed": 240000, "saturation_pct": 45, "min_spend": 30000, "max_spend": 200000},
                {"name": "Events", "current_spend": 100000, "pipeline_generated": 360000, "customers_won": 6, "revenue_attributed": 180000, "saturation_pct": 70, "min_spend": 20000, "max_spend": 150000},
                {"name": "Outbound", "current_spend": 90000, "pipeline_generated": 300000, "customers_won": 5, "revenue_attributed": 100000, "saturation_pct": 40, "min_spend": 30000, "max_spend": 150000},
                {"name": "Referral", "current_spend": 10000, "pipeline_generated": 480000, "customers_won": 8, "revenue_attributed": 320000, "saturation_pct": 20, "min_spend": 5000, "max_spend": 50000},
            ],
        }
        if args.budget:
            data["total_budget"] = args.budget

    results = optimize_mix(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
