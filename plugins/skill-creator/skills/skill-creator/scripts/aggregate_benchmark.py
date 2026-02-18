#!/usr/bin/env python3
"""
Aggregate individual run results into benchmark summary statistics.

Reads grading.json files from run directories and produces:
- run_summary with mean, stddev, min, max for each metric
- delta between with_skill and without_skill configurations

Usage:
    python aggregate_benchmark.py <benchmark_dir>

Example:
    python aggregate_benchmark.py benchmarks/2026-01-15T10-30-00/

The script expects this directory structure:
    <benchmark_dir>/
    └── runs/
        └── eval-N/
            ├── with_skill/
            │   ├── run-1/grading.json
            │   ├── run-2/grading.json
            │   └── run-3/grading.json
            └── without_skill/
                ├── run-1/grading.json
                ├── run-2/grading.json
                └── run-3/grading.json
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


def calculate_stats(values: list[float]) -> dict:
    """Calculate mean, stddev, min, max for a list of values."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}

    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4)
    }


def load_run_results(benchmark_dir: Path) -> dict:
    """
    Load all run results from a benchmark directory.

    Returns dict with structure:
    {
        "with_skill": [
            {"eval_id": 1, "run_number": 1, "pass_rate": 0.85, ...},
            ...
        ],
        "without_skill": [...]
    }
    """
    runs_dir = benchmark_dir / "runs"

    if not runs_dir.exists():
        print(f"Runs directory not found: {runs_dir}")
        return {"with_skill": [], "without_skill": []}

    results = {"with_skill": [], "without_skill": []}

    for eval_dir in sorted(runs_dir.glob("eval-*")):
        eval_id = int(eval_dir.name.split("-")[1])

        for config in ["with_skill", "without_skill"]:
            config_dir = eval_dir / config

            if not config_dir.exists():
                continue

            for run_dir in sorted(config_dir.glob("run-*")):
                run_number = int(run_dir.name.split("-")[1])
                grading_file = run_dir / "grading.json"

                if not grading_file.exists():
                    print(f"Warning: grading.json not found in {run_dir}")
                    continue

                try:
                    with open(grading_file) as f:
                        grading = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON in {grading_file}: {e}")
                    continue

                # Extract metrics
                result = {
                    "eval_id": eval_id,
                    "run_number": run_number,
                    "pass_rate": grading.get("summary", {}).get("pass_rate", 0.0),
                    "passed": grading.get("summary", {}).get("passed", 0),
                    "failed": grading.get("summary", {}).get("failed", 0),
                    "total": grading.get("summary", {}).get("total", 0),
                }

                # Extract timing if available
                timing = grading.get("timing", {})
                result["time_seconds"] = timing.get("total_duration_seconds", 0.0)

                # Extract metrics if available
                metrics = grading.get("execution_metrics", {})
                result["tool_calls"] = metrics.get("total_tool_calls", 0)
                result["tokens"] = metrics.get("output_chars", 0)  # Placeholder
                result["errors"] = metrics.get("errors_encountered", 0)

                # Extract expectations
                result["expectations"] = grading.get("expectations", [])

                # Extract notes from user_notes_summary
                notes_summary = grading.get("user_notes_summary", {})
                notes = []
                notes.extend(notes_summary.get("uncertainties", []))
                notes.extend(notes_summary.get("needs_review", []))
                notes.extend(notes_summary.get("workarounds", []))
                result["notes"] = notes

                results[config].append(result)

    return results


def aggregate_results(results: dict) -> dict:
    """
    Aggregate run results into summary statistics.

    Returns run_summary with stats for each configuration and delta.
    """
    run_summary = {}

    for config in ["with_skill", "without_skill"]:
        runs = results.get(config, [])

        if not runs:
            run_summary[config] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            }
            continue

        pass_rates = [r["pass_rate"] for r in runs]
        times = [r["time_seconds"] for r in runs]
        tokens = [r.get("tokens", 0) for r in runs]

        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": calculate_stats(tokens)
        }

    # Calculate delta
    with_skill = run_summary.get("with_skill", {})
    without_skill = run_summary.get("without_skill", {})

    delta_pass_rate = with_skill.get("pass_rate", {}).get("mean", 0) - without_skill.get("pass_rate", {}).get("mean", 0)
    delta_time = with_skill.get("time_seconds", {}).get("mean", 0) - without_skill.get("time_seconds", {}).get("mean", 0)
    delta_tokens = with_skill.get("tokens", {}).get("mean", 0) - without_skill.get("tokens", {}).get("mean", 0)

    run_summary["delta"] = {
        "pass_rate": f"{delta_pass_rate:+.2f}",
        "time_seconds": f"{delta_time:+.1f}",
        "tokens": f"{delta_tokens:+.0f}"
    }

    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "") -> dict:
    """
    Generate complete benchmark.json from run results.
    """
    results = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results)

    # Build runs array for benchmark.json
    runs = []
    for config in ["with_skill", "without_skill"]:
        for result in results.get(config, []):
            runs.append({
                "eval_id": result["eval_id"],
                "configuration": config,
                "run_number": result["run_number"],
                "result": {
                    "pass_rate": result["pass_rate"],
                    "passed": result["passed"],
                    "failed": result["failed"],
                    "total": result["total"],
                    "time_seconds": result["time_seconds"],
                    "tokens": result.get("tokens", 0),
                    "tool_calls": result.get("tool_calls", 0),
                    "errors": result.get("errors", 0)
                },
                "expectations": result["expectations"],
                "notes": result["notes"]
            })

    # Determine eval IDs from results
    eval_ids = sorted(set(
        r["eval_id"]
        for config in results.values()
        for r in config
    ))

    benchmark = {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": skill_path or "<path/to/skill>",
            "executor_model": "<model-name>",
            "analyzer_model": "<model-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": 3
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": []  # To be filled by analyzer
    }

    return benchmark


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md from benchmark data."""
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Model**: {metadata['executor_model']}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))} ({metadata['runs_per_configuration']} runs each per configuration)",
        "",
        "## Summary",
        "",
        "| Metric | With Skill | Without Skill | Delta |",
        "|--------|------------|---------------|-------|",
    ]

    # Format pass rate
    with_pr = run_summary["with_skill"]["pass_rate"]
    without_pr = run_summary["without_skill"]["pass_rate"]
    delta_pr = run_summary["delta"]["pass_rate"]
    lines.append(f"| Pass Rate | {with_pr['mean']*100:.0f}% ± {with_pr['stddev']*100:.0f}% | {without_pr['mean']*100:.0f}% ± {without_pr['stddev']*100:.0f}% | {delta_pr} |")

    # Format time
    with_time = run_summary["with_skill"]["time_seconds"]
    without_time = run_summary["without_skill"]["time_seconds"]
    delta_time = run_summary["delta"]["time_seconds"]
    lines.append(f"| Time | {with_time['mean']:.1f}s ± {with_time['stddev']:.1f}s | {without_time['mean']:.1f}s ± {without_time['stddev']:.1f}s | {delta_time}s |")

    # Format tokens
    with_tokens = run_summary["with_skill"]["tokens"]
    without_tokens = run_summary["without_skill"]["tokens"]
    delta_tokens = run_summary["delta"]["tokens"]
    lines.append(f"| Tokens | {with_tokens['mean']:.0f} ± {with_tokens['stddev']:.0f} | {without_tokens['mean']:.0f} ± {without_tokens['stddev']:.0f} | {delta_tokens} |")

    # Notes section
    if benchmark.get("notes"):
        lines.extend([
            "",
            "## Notes",
            ""
        ])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark run results into summary statistics"
    )
    parser.add_argument(
        "benchmark_dir",
        type=Path,
        help="Path to the benchmark directory"
    )
    parser.add_argument(
        "--skill-name",
        default="",
        help="Name of the skill being benchmarked"
    )
    parser.add_argument(
        "--skill-path",
        default="",
        help="Path to the skill being benchmarked"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output path for benchmark.json (default: <benchmark_dir>/benchmark.json)"
    )

    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}")
        sys.exit(1)

    # Generate benchmark
    benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path)

    # Determine output paths
    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_md = output_json.with_suffix(".md")

    # Write benchmark.json
    with open(output_json, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"Generated: {output_json}")

    # Write benchmark.md
    markdown = generate_markdown(benchmark)
    with open(output_md, "w") as f:
        f.write(markdown)
    print(f"Generated: {output_md}")

    # Print summary
    run_summary = benchmark["run_summary"]
    with_pr = run_summary["with_skill"]["pass_rate"]["mean"]
    without_pr = run_summary["without_skill"]["pass_rate"]["mean"]
    delta = run_summary["delta"]["pass_rate"]

    print(f"\nSummary:")
    print(f"  With skill:    {with_pr*100:.1f}% pass rate")
    print(f"  Without skill: {without_pr*100:.1f}% pass rate")
    print(f"  Delta:         {delta}")


if __name__ == "__main__":
    main()
