#!/usr/bin/env python3
"""
Usability Test Scorer

Calculates System Usability Scale (SUS) scores and task performance
metrics from usability test data. Supports individual and aggregate analysis.

Uses ONLY Python standard library.

Usage:
    python usability_scorer.py --sus-responses responses.csv
    python usability_scorer.py --task-data tasks.csv
    python usability_scorer.py sample
    python usability_scorer.py --sus-responses responses.csv --json
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, List


# SUS question text for reference
SUS_QUESTIONS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system.",
]


def calculate_sus_score(responses: List[int]) -> float:
    """Calculate SUS score from 10 responses (each 1-5).

    Odd questions (1,3,5,7,9): score - 1
    Even questions (2,4,6,8,10): 5 - score
    Multiply sum by 2.5 for 0-100 scale.
    """
    if len(responses) != 10:
        raise ValueError("SUS requires exactly 10 responses")

    adjusted = []
    for i, score in enumerate(responses):
        if (i + 1) % 2 == 1:  # Odd questions (positive)
            adjusted.append(score - 1)
        else:  # Even questions (negative)
            adjusted.append(5 - score)

    return round(sum(adjusted) * 2.5, 1)


def interpret_sus_score(score: float) -> Dict:
    """Interpret SUS score using standard benchmarks."""
    if score >= 80.3:
        grade = "A"
        adjective = "Excellent"
        percentile = "Top 10%"
    elif score >= 68:
        grade = "B"
        adjective = "Good"
        percentile = "Above average"
    elif score >= 51:
        grade = "C"
        adjective = "OK"
        percentile = "Below average"
    elif score >= 35:
        grade = "D"
        adjective = "Poor"
        percentile = "Bottom 20%"
    else:
        grade = "F"
        adjective = "Awful"
        percentile = "Bottom 5%"

    # Acceptability
    if score >= 70:
        acceptable = "Acceptable"
    elif score >= 50:
        acceptable = "Marginal"
    else:
        acceptable = "Not acceptable"

    return {
        "score": score,
        "grade": grade,
        "adjective": adjective,
        "percentile": percentile,
        "acceptable": acceptable,
        "benchmark": 68.0,
        "above_benchmark": score >= 68,
    }


def calculate_task_metrics(tasks: List[Dict]) -> Dict:
    """Calculate task performance metrics.

    Each task dict should have:
        participant, task, completed (bool), time_seconds, errors
    """
    task_groups = {}
    for t in tasks:
        task_name = t["task"]
        if task_name not in task_groups:
            task_groups[task_name] = []
        task_groups[task_name].append(t)

    results = {}
    for task_name, attempts in task_groups.items():
        total = len(attempts)
        completed = sum(1 for a in attempts if a["completed"])
        times = [a["time_seconds"] for a in attempts if a["completed"]]
        errors = [a["errors"] for a in attempts]

        completion_rate = round((completed / total) * 100, 1) if total > 0 else 0
        avg_time = round(sum(times) / len(times), 1) if times else 0
        median_time = sorted(times)[len(times) // 2] if times else 0
        avg_errors = round(sum(errors) / total, 1) if total > 0 else 0

        # Severity assessment
        if completion_rate < 50:
            severity = "Critical"
        elif completion_rate < 75:
            severity = "Major"
        elif completion_rate < 90:
            severity = "Minor"
        else:
            severity = "None"

        results[task_name] = {
            "participants": total,
            "completion_rate": completion_rate,
            "avg_time_seconds": avg_time,
            "median_time_seconds": median_time,
            "avg_errors": avg_errors,
            "usability_severity": severity,
        }

    return results


def load_sus_csv(filepath: str) -> List[Dict]:
    """Load SUS responses from CSV.

    Expected: participant, q1, q2, ..., q10 (each 1-5)
    """
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            responses = []
            for i in range(1, 11):
                responses.append(int(row.get(f"q{i}", 3)))
            rows.append({
                "participant": row.get("participant", f"P{len(rows)+1}"),
                "responses": responses,
            })
    return rows


def load_task_csv(filepath: str) -> List[Dict]:
    """Load task performance data from CSV.

    Expected: participant, task, completed, time_seconds, errors
    """
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "participant": row.get("participant", "Unknown"),
                "task": row.get("task", "Unknown"),
                "completed": row.get("completed", "true").lower() in ("true", "1", "yes"),
                "time_seconds": float(row.get("time_seconds", 0)),
                "errors": int(row.get("errors", 0)),
            })
    return rows


def create_sample_files():
    """Create sample CSV files for testing."""
    # SUS responses
    sus_header = ["participant"] + [f"q{i}" for i in range(1, 11)]
    sus_rows = [
        ["P1", "4", "2", "5", "1", "4", "2", "5", "1", "4", "2"],
        ["P2", "3", "3", "4", "2", "4", "3", "4", "2", "3", "3"],
        ["P3", "5", "1", "5", "1", "5", "1", "5", "1", "5", "1"],
        ["P4", "3", "4", "3", "3", "3", "3", "3", "3", "3", "4"],
        ["P5", "4", "2", "4", "2", "5", "2", "4", "2", "4", "2"],
        ["P6", "2", "4", "3", "3", "3", "4", "3", "4", "2", "4"],
    ]
    with open("sample_sus.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(sus_header)
        writer.writerows(sus_rows)

    # Task data
    task_header = ["participant", "task", "completed", "time_seconds", "errors"]
    task_rows = [
        ["P1", "Find product", "true", "45", "0"],
        ["P2", "Find product", "true", "62", "1"],
        ["P3", "Find product", "true", "38", "0"],
        ["P4", "Find product", "false", "120", "3"],
        ["P5", "Find product", "true", "55", "1"],
        ["P1", "Complete checkout", "true", "120", "0"],
        ["P2", "Complete checkout", "true", "180", "2"],
        ["P3", "Complete checkout", "false", "240", "4"],
        ["P4", "Complete checkout", "true", "150", "1"],
        ["P5", "Complete checkout", "true", "135", "0"],
        ["P1", "Edit profile", "true", "30", "0"],
        ["P2", "Edit profile", "true", "25", "0"],
        ["P3", "Edit profile", "true", "40", "1"],
        ["P4", "Edit profile", "true", "35", "0"],
        ["P5", "Edit profile", "true", "28", "0"],
    ]
    with open("sample_tasks.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(task_header)
        writer.writerows(task_rows)

    print("Sample files created: sample_sus.csv, sample_tasks.csv")


def format_sus_report(participants: List[Dict], aggregate: Dict) -> str:
    """Format SUS report as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("SYSTEM USABILITY SCALE (SUS) REPORT")
    lines.append("=" * 60)

    interp = aggregate["interpretation"]
    lines.append(f"\n  AGGREGATE SCORE: {aggregate['mean_score']}")
    lines.append(f"  Grade:           {interp['grade']} ({interp['adjective']})")
    lines.append(f"  Percentile:      {interp['percentile']}")
    lines.append(f"  Acceptable:      {interp['acceptable']}")
    lines.append(f"  Benchmark:       {interp['benchmark']} (industry average)")
    lines.append(f"  Participants:    {aggregate['count']}")
    lines.append(f"  Std Deviation:   {aggregate['std_dev']}")
    lines.append(f"  Range:           {aggregate['min_score']} - {aggregate['max_score']}")

    # Score visualization
    lines.append(f"\n  SCORE SCALE")
    lines.append(f"  0    25    50    68    80    100")
    lines.append(f"  |-----|-----|-----|-----|-----|")
    pos = int(aggregate["mean_score"] / 100 * 30)
    ruler = list(" " * 31)
    ruler[min(pos, 30)] = "^"
    lines.append(f"  {''.join(ruler)} ({aggregate['mean_score']})")
    lines.append(f"  F     D     C     B     A")

    # Per-participant
    lines.append(f"\n  INDIVIDUAL SCORES")
    lines.append(f"  {'Participant':<15} {'Score':>7} {'Grade':>6}")
    lines.append(f"  {'-'*15} {'-'*7} {'-'*6}")
    for p in participants:
        lines.append(f"  {p['participant']:<15} {p['score']:>7} {p['interpretation']['grade']:>6}")

    # Question analysis
    if participants:
        lines.append(f"\n  QUESTION ANALYSIS (avg per question)")
        lines.append(f"  {'#':<4} {'Avg':>5} {'Question'}")
        lines.append(f"  {'-'*4} {'-'*5} {'-'*50}")
        for qi in range(10):
            avg_q = round(sum(p["responses"][qi] for p in participants) / len(participants), 1)
            direction = "(+)" if (qi + 1) % 2 == 1 else "(-)"
            lines.append(f"  Q{qi+1:<3} {avg_q:>5} {direction} {SUS_QUESTIONS[qi][:50]}")

    return "\n".join(lines)


def format_task_report(task_results: Dict) -> str:
    """Format task metrics as human-readable text."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("TASK PERFORMANCE REPORT")
    lines.append("=" * 60)

    lines.append(f"\n  {'Task':<25} {'Completion':>12} {'Avg Time':>10} {'Avg Errors':>11} {'Severity':<10}")
    lines.append(f"  {'-'*25} {'-'*12} {'-'*10} {'-'*11} {'-'*10}")

    for task_name, metrics in task_results.items():
        lines.append(
            f"  {task_name:<25} {metrics['completion_rate']:>11}% "
            f"{metrics['avg_time_seconds']:>9}s {metrics['avg_errors']:>11} "
            f"{metrics['usability_severity']:<10}"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate SUS scores and task performance metrics from usability tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample data
  python usability_scorer.py sample

  # Analyze SUS responses
  python usability_scorer.py --sus-responses responses.csv

  # Analyze task performance
  python usability_scorer.py --task-data tasks.csv

  # Both analyses together
  python usability_scorer.py --sus-responses responses.csv --task-data tasks.csv

  # JSON output
  python usability_scorer.py --sus-responses responses.csv --json
        """,
    )

    parser.add_argument("action", nargs="?", help='"sample" to create sample files')
    parser.add_argument("--sus-responses", help="CSV with SUS responses (participant, q1-q10)")
    parser.add_argument("--task-data", help="CSV with task data (participant, task, completed, time_seconds, errors)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.action == "sample":
        create_sample_files()
        return

    if not args.sus_responses and not args.task_data:
        parser.print_help()
        print("\nError: Provide --sus-responses and/or --task-data, or use 'sample' to create test files")
        sys.exit(1)

    output = {}

    if args.sus_responses:
        raw = load_sus_csv(args.sus_responses)
        participants = []
        for p in raw:
            score = calculate_sus_score(p["responses"])
            participants.append({
                "participant": p["participant"],
                "responses": p["responses"],
                "score": score,
                "interpretation": interpret_sus_score(score),
            })

        scores = [p["score"] for p in participants]
        mean = round(sum(scores) / len(scores), 1)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = round(math.sqrt(variance), 1)

        aggregate = {
            "count": len(scores),
            "mean_score": mean,
            "median_score": sorted(scores)[len(scores) // 2],
            "std_dev": std_dev,
            "min_score": min(scores),
            "max_score": max(scores),
            "interpretation": interpret_sus_score(mean),
        }

        output["sus"] = {"participants": participants, "aggregate": aggregate}

        if not args.json:
            print(format_sus_report(participants, aggregate))

    if args.task_data:
        tasks = load_task_csv(args.task_data)
        task_results = calculate_task_metrics(tasks)
        output["task_performance"] = task_results

        if not args.json:
            print(format_task_report(task_results))

    if args.json:
        # Clean up for JSON (remove full response arrays for brevity)
        if "sus" in output:
            for p in output["sus"]["participants"]:
                del p["responses"]
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
