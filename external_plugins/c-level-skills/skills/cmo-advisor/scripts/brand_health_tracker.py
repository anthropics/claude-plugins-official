#!/usr/bin/env python3
"""
Brand Health Tracker - Monitor brand awareness, perception, and competitive position.

Tracks brand lift metrics, awareness levels, NPS trends, share of voice,
and competitive perception. Produces board-ready brand health reports.
"""

import argparse
import json
import sys
from datetime import datetime


def assess_brand(data: dict) -> dict:
    """Assess brand health across key dimensions."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "company": data.get("company", "Company"),
        "overall_score": 0,
        "dimensions": {},
        "trends": [],
        "competitive_position": {},
        "recommendations": [],
        "board_summary": {},
    }

    # Dimension scoring (each 0-100)
    dimensions = {
        "awareness": {
            "aided_awareness_pct": data.get("aided_awareness_pct", 0),
            "unaided_awareness_pct": data.get("unaided_awareness_pct", 0),
            "search_volume_index": data.get("search_volume_index", 0),
            "weight": 0.20,
        },
        "perception": {
            "nps": data.get("nps", 0),
            "brand_sentiment_pct": data.get("brand_sentiment_positive_pct", 0),
            "consideration_pct": data.get("consideration_pct", 0),
            "weight": 0.25,
        },
        "differentiation": {
            "unique_positioning_score": data.get("unique_positioning_score", 0),
            "category_association_pct": data.get("category_association_pct", 0),
            "weight": 0.20,
        },
        "engagement": {
            "share_of_voice_pct": data.get("share_of_voice_pct", 0),
            "social_engagement_rate": data.get("social_engagement_rate", 0),
            "content_amplification": data.get("content_amplification_rate", 0),
            "weight": 0.15,
        },
        "loyalty": {
            "nrr_pct": data.get("nrr_pct", 100),
            "referral_rate_pct": data.get("referral_rate_pct", 0),
            "repeat_purchase_pct": data.get("repeat_purchase_pct", 0),
            "weight": 0.20,
        },
    }

    total_score = 0
    for dim_name, dim_data in dimensions.items():
        weight = dim_data.pop("weight")
        values = [v for v in dim_data.values() if isinstance(v, (int, float)) and v > 0]
        # Normalize NPS (-100 to 100) to 0-100 scale
        if dim_name == "perception" and "nps" in dim_data:
            nps = dim_data["nps"]
            dim_data["nps_normalized"] = (nps + 100) / 2

        avg = sum(values) / len(values) if values else 0
        # Cap at 100
        avg = min(100, avg)
        weighted = avg * weight
        total_score += weighted

        rating = "Strong" if avg >= 70 else "Adequate" if avg >= 45 else "Weak"

        results["dimensions"][dim_name] = {
            "score": round(avg, 1),
            "weighted_score": round(weighted, 1),
            "rating": rating,
            "metrics": {k: v for k, v in dim_data.items() if isinstance(v, (int, float))},
        }

    results["overall_score"] = round(total_score, 1)

    # Trends
    historical = data.get("historical", [])
    if historical:
        for period in historical:
            results["trends"].append({
                "period": period.get("period", ""),
                "awareness": period.get("aided_awareness_pct", 0),
                "nps": period.get("nps", 0),
                "sov": period.get("share_of_voice_pct", 0),
            })

    # Competitive position
    competitors = data.get("competitors", [])
    if competitors:
        results["competitive_position"] = {
            "company_sov": data.get("share_of_voice_pct", 0),
            "competitors": [
                {"name": c.get("name", ""), "sov": c.get("share_of_voice_pct", 0), "awareness": c.get("aided_awareness_pct", 0)}
                for c in competitors
            ],
        }

    # Recommendations
    for dim_name, dim_data in results["dimensions"].items():
        if dim_data["rating"] == "Weak":
            if dim_name == "awareness":
                results["recommendations"].append("Increase brand awareness through top-of-funnel content, PR, and thought leadership campaigns.")
            elif dim_name == "perception":
                results["recommendations"].append("Improve brand perception: invest in customer success stories, address negative sentiment drivers.")
            elif dim_name == "differentiation":
                results["recommendations"].append("Sharpen positioning: conduct competitive messaging audit and update value proposition.")
            elif dim_name == "engagement":
                results["recommendations"].append("Boost engagement: increase content frequency, launch community programs, invest in social.")
            elif dim_name == "loyalty":
                results["recommendations"].append("Strengthen loyalty: launch referral program, improve onboarding, address churn drivers.")

    if not results["recommendations"]:
        results["recommendations"].append("Brand health is strong across all dimensions. Focus on maintaining and extending leadership position.")

    # Board summary
    results["board_summary"] = {
        "brand_health_score": f"{results['overall_score']:.0f}/100",
        "strongest_dimension": max(results["dimensions"].items(), key=lambda x: x[1]["score"])[0] if results["dimensions"] else "N/A",
        "weakest_dimension": min(results["dimensions"].items(), key=lambda x: x[1]["score"])[0] if results["dimensions"] else "N/A",
        "nps": data.get("nps", "N/A"),
        "share_of_voice": f"{data.get('share_of_voice_pct', 0)}%",
    }

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 60,
        "BRAND HEALTH REPORT",
        "=" * 60,
        f"Company: {results['company']}  |  Date: {results['timestamp'][:10]}",
        f"Overall Brand Health: {results['overall_score']:.0f}/100",
        "",
        f"{'Dimension':<18} {'Score':>7} {'Weighted':>9} {'Rating':<10}",
        "-" * 50,
    ]

    for name, dim in results["dimensions"].items():
        lines.append(f"{name.title():<18} {dim['score']:>6.0f}/100 {dim['weighted_score']:>8.1f} {dim['rating']:<10}")
        for metric, val in dim["metrics"].items():
            if metric != "nps_normalized":
                unit = "%" if "pct" in metric else ""
                lines.append(f"  {metric.replace('_', ' ').title()}: {val}{unit}")

    if results["competitive_position"].get("competitors"):
        lines.extend(["", "COMPETITIVE SHARE OF VOICE:"])
        lines.append(f"  {results['company']}: {results['competitive_position']['company_sov']}%")
        for c in results["competitive_position"]["competitors"]:
            lines.append(f"  {c['name']}: {c['sov']}%")

    if results["recommendations"]:
        lines.extend(["", "RECOMMENDATIONS:"])
        for r in results["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Track and assess brand health metrics")
    parser.add_argument("--input", "-i", help="JSON file with brand data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "company": "SaaSCo",
            "aided_awareness_pct": 42,
            "unaided_awareness_pct": 18,
            "search_volume_index": 55,
            "nps": 38,
            "brand_sentiment_positive_pct": 72,
            "consideration_pct": 35,
            "unique_positioning_score": 60,
            "category_association_pct": 28,
            "share_of_voice_pct": 15,
            "social_engagement_rate": 3.2,
            "content_amplification_rate": 2.1,
            "nrr_pct": 112,
            "referral_rate_pct": 18,
            "repeat_purchase_pct": 85,
            "competitors": [
                {"name": "Competitor A", "share_of_voice_pct": 28, "aided_awareness_pct": 65},
                {"name": "Competitor B", "share_of_voice_pct": 22, "aided_awareness_pct": 55},
                {"name": "Competitor C", "share_of_voice_pct": 18, "aided_awareness_pct": 40},
            ],
        }

    results = assess_brand(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
