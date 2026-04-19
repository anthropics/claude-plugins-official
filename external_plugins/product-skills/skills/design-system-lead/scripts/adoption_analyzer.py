#!/usr/bin/env python3
"""
Design System Adoption Analyzer

Analyzes design system adoption across products by scanning for
design token usage, custom overrides, and component coverage.

Reads a configuration CSV/JSON listing products and their metrics,
then produces an adoption health dashboard.

Uses ONLY Python standard library.

Usage:
    python adoption_analyzer.py report.csv
    python adoption_analyzer.py sample
    python adoption_analyzer.py report.csv --json
    python adoption_analyzer.py report.csv --threshold 80
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from typing import Dict, List


def load_adoption_csv(filepath: str) -> List[Dict]:
    """Load adoption data from CSV.

    Expected columns:
        product: Product/app name
        total_components: Total UI components in the product
        ds_components: Components using design system
        total_tokens: Total style values in the product
        ds_tokens: Style values using design system tokens
        custom_overrides: Number of custom overrides/deviations
        a11y_score: Accessibility score (0-100)
        last_audit: Date of last audit (YYYY-MM-DD)
    """
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "product": row.get("product", "Unknown"),
                "total_components": int(row.get("total_components", 0)),
                "ds_components": int(row.get("ds_components", 0)),
                "total_tokens": int(row.get("total_tokens", 0)),
                "ds_tokens": int(row.get("ds_tokens", 0)),
                "custom_overrides": int(row.get("custom_overrides", 0)),
                "a11y_score": float(row.get("a11y_score", 0)),
                "last_audit": row.get("last_audit", "N/A"),
            })
    return rows


def create_sample_csv(filepath: str):
    """Create sample adoption data for testing."""
    header = ["product", "total_components", "ds_components", "total_tokens", "ds_tokens", "custom_overrides", "a11y_score", "last_audit"]
    rows = [
        ["Web App", "120", "98", "450", "420", "12", "92", "2026-03-01"],
        ["Mobile App", "85", "72", "320", "285", "18", "88", "2026-02-15"],
        ["Admin Dashboard", "65", "60", "250", "245", "3", "95", "2026-03-10"],
        ["Marketing Site", "45", "30", "200", "140", "25", "78", "2026-01-20"],
        ["Developer Portal", "55", "48", "180", "165", "8", "90", "2026-02-28"],
        ["Onboarding Flow", "30", "28", "120", "118", "2", "96", "2026-03-15"],
    ]

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Sample CSV created at: {filepath}")


def analyze_product(product: Dict) -> Dict:
    """Analyze adoption metrics for a single product."""
    total_comp = product["total_components"] or 1
    total_tok = product["total_tokens"] or 1

    component_coverage = round((product["ds_components"] / total_comp) * 100, 1)
    token_compliance = round((product["ds_tokens"] / total_tok) * 100, 1)
    override_rate = round((product["custom_overrides"] / total_comp) * 100, 1)

    # Health score: weighted average
    health_score = round(
        component_coverage * 0.30
        + token_compliance * 0.30
        + product["a11y_score"] * 0.20
        + max(0, 100 - override_rate * 5) * 0.20,
        1,
    )

    # Status
    if health_score >= 90:
        status = "EXCELLENT"
    elif health_score >= 75:
        status = "GOOD"
    elif health_score >= 60:
        status = "NEEDS ATTENTION"
    else:
        status = "AT RISK"

    # Recommendations
    recommendations = []
    if component_coverage < 80:
        gap = product["total_components"] - product["ds_components"]
        recommendations.append(f"Migrate {gap} custom components to design system")
    if token_compliance < 90:
        gap = product["total_tokens"] - product["ds_tokens"]
        recommendations.append(f"Replace {gap} hardcoded values with design tokens")
    if product["custom_overrides"] > 10:
        recommendations.append(f"Audit {product['custom_overrides']} custom overrides for potential DS contribution")
    if product["a11y_score"] < 85:
        recommendations.append(f"Improve accessibility score from {product['a11y_score']}% to 85%+ target")

    return {
        "product": product["product"],
        "component_coverage": component_coverage,
        "token_compliance": token_compliance,
        "override_rate": override_rate,
        "a11y_score": product["a11y_score"],
        "health_score": health_score,
        "status": status,
        "recommendations": recommendations,
        "last_audit": product["last_audit"],
    }


def analyze_portfolio(products: List[Dict]) -> Dict:
    """Analyze adoption across the entire portfolio."""
    analyses = [analyze_product(p) for p in products]

    total_products = len(analyses)
    adopted_count = sum(1 for a in analyses if a["component_coverage"] >= 50)

    avg_coverage = round(sum(a["component_coverage"] for a in analyses) / total_products, 1) if total_products else 0
    avg_compliance = round(sum(a["token_compliance"] for a in analyses) / total_products, 1) if total_products else 0
    avg_health = round(sum(a["health_score"] for a in analyses) / total_products, 1) if total_products else 0
    avg_a11y = round(sum(a["a11y_score"] for a in analyses) / total_products, 1) if total_products else 0
    total_overrides = sum(p["custom_overrides"] for p in products)

    status_counts = {}
    for a in analyses:
        status_counts[a["status"]] = status_counts.get(a["status"], 0) + 1

    # Top priorities
    priorities = sorted(analyses, key=lambda x: x["health_score"])[:3]

    return {
        "summary": {
            "total_products": total_products,
            "adopted_products": adopted_count,
            "adoption_rate": round((adopted_count / total_products) * 100, 1) if total_products else 0,
            "avg_component_coverage": avg_coverage,
            "avg_token_compliance": avg_compliance,
            "avg_a11y_score": avg_a11y,
            "avg_health_score": avg_health,
            "total_custom_overrides": total_overrides,
            "status_distribution": status_counts,
        },
        "products": analyses,
        "top_priorities": [
            {"product": p["product"], "health_score": p["health_score"], "recommendations": p["recommendations"][:2]}
            for p in priorities
        ],
    }


def format_human_output(report: Dict, threshold: int) -> str:
    """Format adoption report as human-readable text."""
    s = report["summary"]
    lines = []
    lines.append("=" * 60)
    lines.append("DESIGN SYSTEM ADOPTION REPORT")
    lines.append("=" * 60)

    lines.append(f"\n  PORTFOLIO SUMMARY")
    lines.append(f"  " + "-" * 50)
    lines.append(f"  Products tracked:       {s['total_products']}")
    lines.append(f"  Products adopted:       {s['adopted_products']} ({s['adoption_rate']}%)")
    lines.append(f"  Avg component coverage: {s['avg_component_coverage']}%")
    lines.append(f"  Avg token compliance:   {s['avg_token_compliance']}%")
    lines.append(f"  Avg accessibility:      {s['avg_a11y_score']}%")
    lines.append(f"  Avg health score:       {s['avg_health_score']}%")
    lines.append(f"  Total custom overrides: {s['total_custom_overrides']}")

    lines.append(f"\n  Status distribution:")
    for status, count in s["status_distribution"].items():
        bar = "#" * (count * 5)
        lines.append(f"    {status:<18} {count} {bar}")

    lines.append(f"\n  PER-PRODUCT BREAKDOWN")
    lines.append(f"  " + "-" * 50)
    lines.append(f"  {'Product':<20} {'Coverage':>9} {'Tokens':>8} {'A11y':>6} {'Health':>8} {'Status':<15}")
    lines.append(f"  {'-'*20} {'-'*9} {'-'*8} {'-'*6} {'-'*8} {'-'*15}")

    for p in sorted(report["products"], key=lambda x: -x["health_score"]):
        flag = " *" if p["health_score"] < threshold else ""
        lines.append(
            f"  {p['product']:<20} {p['component_coverage']:>8}% {p['token_compliance']:>7}% "
            f"{p['a11y_score']:>5}% {p['health_score']:>7}% {p['status']:<15}{flag}"
        )

    lines.append(f"\n  * Below {threshold}% health threshold")

    lines.append(f"\n  TOP PRIORITIES")
    lines.append(f"  " + "-" * 50)
    for i, p in enumerate(report["top_priorities"], 1):
        lines.append(f"  {i}. {p['product']} (health: {p['health_score']}%)")
        for rec in p["recommendations"]:
            lines.append(f"     - {rec}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze design system adoption across products",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python adoption_analyzer.py sample
  python adoption_analyzer.py adoption_data.csv
  python adoption_analyzer.py adoption_data.csv --threshold 80
  python adoption_analyzer.py adoption_data.csv --json

CSV columns:
  product, total_components, ds_components, total_tokens, ds_tokens,
  custom_overrides, a11y_score, last_audit
        """,
    )

    parser.add_argument("input", help='CSV file with adoption data or "sample" to create sample')
    parser.add_argument("--threshold", "-t", type=int, default=75, help="Health score threshold for flagging (default: 75)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.input == "sample":
        create_sample_csv("sample_adoption.csv")
        return

    products = load_adoption_csv(args.input)
    if not products:
        print("Error: No data found in CSV", file=sys.stderr)
        sys.exit(1)

    report = analyze_portfolio(products)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_human_output(report, args.threshold))


if __name__ == "__main__":
    main()
