#!/usr/bin/env python3
"""
Board Metrics Dashboard Generator - Generates formatted board-ready metrics dashboards.

Takes raw metric values and targets, calculates status (RAG), trends, and produces
a formatted dashboard suitable for board decks. Supports multiple output formats.
"""

import argparse
import csv
import io
import json
import sys
from datetime import datetime


RAG_THRESHOLDS = {
    "higher_is_better": {"green": 0.95, "yellow": 0.85},
    "lower_is_better": {"green": 1.05, "yellow": 1.15},
    "exact": {"green": 0.02, "yellow": 0.05},
}


def calculate_rag(actual: float, target: float, direction: str = "higher_is_better") -> str:
    """Calculate RAG status based on actual vs target."""
    if target == 0:
        return "N/A"
    ratio = actual / target
    thresholds = RAG_THRESHOLDS.get(direction, RAG_THRESHOLDS["higher_is_better"])

    if direction == "higher_is_better":
        if ratio >= thresholds["green"]:
            return "G"
        elif ratio >= thresholds["yellow"]:
            return "Y"
        else:
            return "R"
    elif direction == "lower_is_better":
        if ratio <= thresholds["green"]:
            return "G"
        elif ratio <= thresholds["yellow"]:
            return "Y"
        else:
            return "R"
    else:
        deviation = abs(1 - ratio)
        if deviation <= thresholds["green"]:
            return "G"
        elif deviation <= thresholds["yellow"]:
            return "Y"
        else:
            return "R"


def calculate_trend(current: float, previous: float) -> str:
    """Determine trend direction."""
    if previous == 0:
        return "New"
    change = (current - previous) / abs(previous)
    if change > 0.02:
        return "Up"
    elif change < -0.02:
        return "Down"
    else:
        return "Flat"


def format_value(value: float, fmt: str = "number") -> str:
    """Format a metric value for display."""
    if fmt == "currency":
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"${value / 1_000:.0f}K"
        else:
            return f"${value:,.0f}"
    elif fmt == "percent":
        return f"{value:.1f}%"
    elif fmt == "ratio":
        return f"{value:.1f}x"
    elif fmt == "months":
        return f"{value:.0f} mo"
    elif fmt == "integer":
        return f"{int(value)}"
    else:
        return f"{value:,.1f}"


def generate_dashboard(metrics: list) -> dict:
    """Generate a complete metrics dashboard."""
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "metrics_count": len(metrics),
        "summary": {"green": 0, "yellow": 0, "red": 0, "na": 0},
        "metrics": [],
        "alerts": [],
        "recommendations": [],
    }

    for m in metrics:
        name = m.get("name", "Unnamed")
        actual = float(m.get("actual", 0))
        target = float(m.get("target", 0))
        previous = float(m.get("previous", 0))
        direction = m.get("direction", "higher_is_better")
        fmt = m.get("format", "number")
        owner = m.get("owner", "Unassigned")

        rag = calculate_rag(actual, target, direction)
        trend = calculate_trend(actual, previous)
        variance_pct = ((actual - target) / abs(target) * 100) if target != 0 else 0

        metric_result = {
            "name": name,
            "actual": actual,
            "actual_formatted": format_value(actual, fmt),
            "target": target,
            "target_formatted": format_value(target, fmt),
            "previous": previous,
            "previous_formatted": format_value(previous, fmt),
            "variance_pct": round(variance_pct, 1),
            "status": rag,
            "trend": trend,
            "owner": owner,
        }
        dashboard["metrics"].append(metric_result)

        # Update summary
        if rag == "G":
            dashboard["summary"]["green"] += 1
        elif rag == "Y":
            dashboard["summary"]["yellow"] += 1
        elif rag == "R":
            dashboard["summary"]["red"] += 1
        else:
            dashboard["summary"]["na"] += 1

        # Generate alerts for red metrics
        if rag == "R":
            dashboard["alerts"].append({
                "metric": name,
                "owner": owner,
                "message": f"{name} is {format_value(actual, fmt)} vs target {format_value(target, fmt)} ({variance_pct:+.1f}%)",
            })

    # Recommendations
    red_count = dashboard["summary"]["red"]
    if red_count >= 3:
        dashboard["recommendations"].append(
            f"{red_count} metrics in RED. Schedule an executive review before board meeting."
        )
    if red_count > 0:
        owners_with_red = set(a["owner"] for a in dashboard["alerts"])
        dashboard["recommendations"].append(
            f"Variance explanations needed from: {', '.join(sorted(owners_with_red))}"
        )
    if dashboard["summary"]["green"] == len(metrics):
        dashboard["recommendations"].append(
            "All metrics green. Verify targets are ambitious enough."
        )

    return dashboard


def format_text(dashboard: dict) -> str:
    """Format dashboard as board-ready text."""
    lines = [
        "=" * 72,
        "KEY METRICS DASHBOARD",
        "=" * 72,
        f"Date: {dashboard['timestamp'][:10]}",
        f"Summary: {dashboard['summary']['green']}G / {dashboard['summary']['yellow']}Y / {dashboard['summary']['red']}R",
        "",
        f"{'Metric':<22} {'Actual':>10} {'Target':>10} {'Prev':>10} {'Var%':>7} {'RAG':>4} {'Trend':<6} {'Owner':<8}",
        "-" * 72,
    ]

    for m in dashboard["metrics"]:
        rag_display = f"[{m['status']}]"
        lines.append(
            f"{m['name']:<22} {m['actual_formatted']:>10} {m['target_formatted']:>10} "
            f"{m['previous_formatted']:>10} {m['variance_pct']:>+6.1f}% {rag_display:>4} "
            f"{m['trend']:<6} {m['owner']:<8}"
        )

    if dashboard["alerts"]:
        lines.extend(["", "ALERTS:"])
        for a in dashboard["alerts"]:
            lines.append(f"  [R] {a['message']} (Owner: {a['owner']})")

    if dashboard["recommendations"]:
        lines.extend(["", "RECOMMENDATIONS:"])
        for r in dashboard["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 72])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate board-ready metrics dashboard"
    )
    parser.add_argument(
        "--input", "-i",
        help="JSON file with metrics data (uses demo data if omitted)"
    )
    parser.add_argument(
        "--csv",
        help="CSV file with metrics (columns: name,actual,target,previous,direction,format,owner)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            metrics = json.load(f)
            if isinstance(metrics, dict):
                metrics = metrics.get("metrics", [])
    elif args.csv:
        metrics = []
        with open(args.csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                for field in ["actual", "target", "previous"]:
                    if field in row:
                        row[field] = float(row[field])
                metrics.append(row)
    else:
        # Demo data
        metrics = [
            {"name": "ARR", "actual": 2400000, "target": 2300000, "previous": 1970000, "direction": "higher_is_better", "format": "currency", "owner": "CRO"},
            {"name": "MoM Growth", "actual": 8.1, "target": 7.5, "previous": 7.2, "direction": "higher_is_better", "format": "percent", "owner": "CRO"},
            {"name": "Burn Multiple", "actual": 1.8, "target": 2.0, "previous": 2.1, "direction": "lower_is_better", "format": "ratio", "owner": "CFO"},
            {"name": "NRR", "actual": 112, "target": 110, "previous": 108, "direction": "higher_is_better", "format": "percent", "owner": "CRO"},
            {"name": "CAC Payback", "actual": 11, "target": 12, "previous": 14, "direction": "lower_is_better", "format": "months", "owner": "CMO"},
            {"name": "Headcount", "actual": 24, "target": 25, "previous": 21, "direction": "higher_is_better", "format": "integer", "owner": "CHRO"},
            {"name": "Runway", "actual": 16, "target": 18, "previous": 19, "direction": "higher_is_better", "format": "months", "owner": "CFO"},
            {"name": "eNPS", "actual": 42, "target": 30, "previous": 38, "direction": "higher_is_better", "format": "integer", "owner": "CHRO"},
        ]

    dashboard = generate_dashboard(metrics)

    if args.json:
        print(json.dumps(dashboard, indent=2))
    else:
        print(format_text(dashboard))


if __name__ == "__main__":
    main()
