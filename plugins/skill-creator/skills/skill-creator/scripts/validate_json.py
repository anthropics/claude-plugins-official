#!/usr/bin/env python3
"""
Validate JSON files produced by skill-creator-edge.

Supports validation for:
- evals.json: Skill evaluation definitions
- grading.json: Grader output
- benchmark.json: Benchmark results
- metrics.json: Executor metrics
- timing.json: Timing data
- history.json: Improve mode version history
- comparison.json: Blind comparator output
- analysis.json: Post-hoc analyzer output

Usage:
    python validate_json.py <file_path> [--type <type>]

Examples:
    python validate_json.py workspace/benchmark.json
    python validate_json.py evals/evals.json --type evals
    python validate_json.py run-1/grading.json --type grading
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# Schema definitions as validation rules
SCHEMAS = {
    "evals": {
        "required": ["skill_name", "evals"],
        "evals_item": {
            "required": ["id", "prompt"],
            "optional": ["expected_output", "files", "expectations"]
        }
    },
    "grading": {
        "required": ["expectations", "summary"],
        "summary": {
            "required": ["passed", "failed", "total", "pass_rate"]
        },
        "expectations_item": {
            "required": ["text", "passed", "evidence"]
        }
    },
    "benchmark": {
        "required": ["metadata", "runs", "run_summary"],
        "metadata": {
            "required": ["skill_name", "timestamp", "runs_per_configuration"]
        },
        "runs_item": {
            "required": ["eval_id", "configuration", "run_number", "result"]
        },
        "run_summary_config": {
            "required": ["pass_rate", "time_seconds", "tokens"]
        }
    },
    "metrics": {
        "required": ["tool_calls", "total_tool_calls"],
        "optional": ["total_steps", "files_created", "errors_encountered",
                     "output_chars", "transcript_chars"]
    },
    "timing": {
        "required": [],  # All fields optional but should have at least one
        "optional": ["executor_start", "executor_end", "executor_duration_seconds",
                     "grader_start", "grader_end", "grader_duration_seconds",
                     "total_duration_seconds"]
    },
    "history": {
        "required": ["started_at", "skill_name", "current_best", "iterations"],
        "iterations_item": {
            "required": ["version", "expectation_pass_rate", "grading_result", "is_current_best"]
        }
    },
    "comparison": {
        "required": ["winner", "reasoning", "rubric", "output_quality"],
        "rubric_side": {
            "required": ["content", "structure", "overall_score"]
        }
    },
    "analysis": {
        "required": ["comparison_summary", "winner_strengths", "loser_weaknesses",
                     "improvement_suggestions"],
        "improvement_item": {
            "required": ["priority", "category", "suggestion"]
        }
    }
}


def infer_type(file_path: Path) -> str | None:
    """Infer JSON type from filename."""
    name = file_path.name.lower()

    if name == "evals.json":
        return "evals"
    elif name == "grading.json":
        return "grading"
    elif name == "benchmark.json":
        return "benchmark"
    elif name == "metrics.json":
        return "metrics"
    elif name == "timing.json":
        return "timing"
    elif name == "history.json":
        return "history"
    elif name.startswith("comparison"):
        return "comparison"
    elif name == "analysis.json":
        return "analysis"

    return None


def validate_required_fields(data: dict, required: list[str], path: str = "") -> list[str]:
    """Check that all required fields are present."""
    errors = []
    for field in required:
        if field not in data:
            errors.append(f"{path}Missing required field: {field}")
    return errors


def validate_evals(data: dict) -> list[str]:
    """Validate evals.json structure."""
    errors = validate_required_fields(data, SCHEMAS["evals"]["required"])

    if "evals" in data:
        if not isinstance(data["evals"], list):
            errors.append("'evals' must be a list")
        else:
            for i, eval_item in enumerate(data["evals"]):
                item_errors = validate_required_fields(
                    eval_item,
                    SCHEMAS["evals"]["evals_item"]["required"],
                    f"evals[{i}]: "
                )
                errors.extend(item_errors)

                # Validate id is an integer
                if "id" in eval_item and not isinstance(eval_item["id"], int):
                    errors.append(f"evals[{i}]: 'id' must be an integer")

                # Validate expectations is a list of strings
                if "expectations" in eval_item:
                    if not isinstance(eval_item["expectations"], list):
                        errors.append(f"evals[{i}]: 'expectations' must be a list")
                    else:
                        for j, exp in enumerate(eval_item["expectations"]):
                            if not isinstance(exp, str):
                                errors.append(f"evals[{i}].expectations[{j}]: must be a string")

    return errors


def validate_grading(data: dict) -> list[str]:
    """Validate grading.json structure."""
    errors = validate_required_fields(data, SCHEMAS["grading"]["required"])

    if "summary" in data:
        summary_errors = validate_required_fields(
            data["summary"],
            SCHEMAS["grading"]["summary"]["required"],
            "summary: "
        )
        errors.extend(summary_errors)

        # Validate pass_rate is between 0 and 1
        if "pass_rate" in data["summary"]:
            pr = data["summary"]["pass_rate"]
            if not isinstance(pr, (int, float)) or pr < 0 or pr > 1:
                errors.append("summary.pass_rate must be a number between 0 and 1")

    if "expectations" in data:
        if not isinstance(data["expectations"], list):
            errors.append("'expectations' must be a list")
        else:
            for i, exp in enumerate(data["expectations"]):
                exp_errors = validate_required_fields(
                    exp,
                    SCHEMAS["grading"]["expectations_item"]["required"],
                    f"expectations[{i}]: "
                )
                errors.extend(exp_errors)

                if "passed" in exp and not isinstance(exp["passed"], bool):
                    errors.append(f"expectations[{i}].passed must be a boolean")

    return errors


def validate_benchmark(data: dict) -> list[str]:
    """Validate benchmark.json structure."""
    errors = validate_required_fields(data, SCHEMAS["benchmark"]["required"])

    if "metadata" in data:
        meta_errors = validate_required_fields(
            data["metadata"],
            SCHEMAS["benchmark"]["metadata"]["required"],
            "metadata: "
        )
        errors.extend(meta_errors)

    if "runs" in data:
        if not isinstance(data["runs"], list):
            errors.append("'runs' must be a list")
        else:
            for i, run in enumerate(data["runs"]):
                run_errors = validate_required_fields(
                    run,
                    SCHEMAS["benchmark"]["runs_item"]["required"],
                    f"runs[{i}]: "
                )
                errors.extend(run_errors)

                # Validate configuration
                if "configuration" in run:
                    if run["configuration"] not in ["with_skill", "without_skill"]:
                        errors.append(f"runs[{i}].configuration must be 'with_skill' or 'without_skill'")

    if "run_summary" in data:
        for config in ["with_skill", "without_skill"]:
            if config in data["run_summary"]:
                config_errors = validate_required_fields(
                    data["run_summary"][config],
                    SCHEMAS["benchmark"]["run_summary_config"]["required"],
                    f"run_summary.{config}: "
                )
                errors.extend(config_errors)

    return errors


def validate_metrics(data: dict) -> list[str]:
    """Validate metrics.json structure."""
    errors = validate_required_fields(data, SCHEMAS["metrics"]["required"])

    if "tool_calls" in data and not isinstance(data["tool_calls"], dict):
        errors.append("'tool_calls' must be an object")

    if "total_tool_calls" in data and not isinstance(data["total_tool_calls"], int):
        errors.append("'total_tool_calls' must be an integer")

    return errors


def validate_timing(data: dict) -> list[str]:
    """Validate timing.json structure."""
    errors = []

    # At least one timing field should be present
    timing_fields = SCHEMAS["timing"]["optional"]
    has_timing = any(field in data for field in timing_fields)

    if not has_timing:
        errors.append("timing.json should have at least one timing field")

    # Validate duration fields are numbers
    for field in ["executor_duration_seconds", "grader_duration_seconds", "total_duration_seconds"]:
        if field in data and not isinstance(data[field], (int, float)):
            errors.append(f"'{field}' must be a number")

    return errors


def validate_history(data: dict) -> list[str]:
    """Validate history.json structure."""
    errors = validate_required_fields(data, SCHEMAS["history"]["required"])

    if "iterations" in data:
        if not isinstance(data["iterations"], list):
            errors.append("'iterations' must be a list")
        else:
            for i, iteration in enumerate(data["iterations"]):
                iter_errors = validate_required_fields(
                    iteration,
                    SCHEMAS["history"]["iterations_item"]["required"],
                    f"iterations[{i}]: "
                )
                errors.extend(iter_errors)

                if "grading_result" in iteration:
                    valid_results = ["baseline", "won", "lost", "tie"]
                    if iteration["grading_result"] not in valid_results:
                        errors.append(f"iterations[{i}].grading_result must be one of: {valid_results}")

    return errors


def validate_comparison(data: dict) -> list[str]:
    """Validate comparison.json structure."""
    errors = validate_required_fields(data, SCHEMAS["comparison"]["required"])

    if "winner" in data:
        if data["winner"] not in ["A", "B", "TIE"]:
            errors.append("'winner' must be 'A', 'B', or 'TIE'")

    if "rubric" in data:
        for side in ["A", "B"]:
            if side in data["rubric"]:
                side_errors = validate_required_fields(
                    data["rubric"][side],
                    SCHEMAS["comparison"]["rubric_side"]["required"],
                    f"rubric.{side}: "
                )
                errors.extend(side_errors)

    return errors


def validate_analysis(data: dict) -> list[str]:
    """Validate analysis.json structure."""
    errors = validate_required_fields(data, SCHEMAS["analysis"]["required"])

    if "improvement_suggestions" in data:
        if not isinstance(data["improvement_suggestions"], list):
            errors.append("'improvement_suggestions' must be a list")
        else:
            for i, suggestion in enumerate(data["improvement_suggestions"]):
                sugg_errors = validate_required_fields(
                    suggestion,
                    SCHEMAS["analysis"]["improvement_item"]["required"],
                    f"improvement_suggestions[{i}]: "
                )
                errors.extend(sugg_errors)

                if "priority" in suggestion:
                    if suggestion["priority"] not in ["high", "medium", "low"]:
                        errors.append(f"improvement_suggestions[{i}].priority must be 'high', 'medium', or 'low'")

    return errors


VALIDATORS = {
    "evals": validate_evals,
    "grading": validate_grading,
    "benchmark": validate_benchmark,
    "metrics": validate_metrics,
    "timing": validate_timing,
    "history": validate_history,
    "comparison": validate_comparison,
    "analysis": validate_analysis,
}


def validate_file(file_path: Path, json_type: str | None = None) -> tuple[bool, list[str]]:
    """
    Validate a JSON file.

    Returns (is_valid, errors) tuple.
    """
    errors = []

    # Check file exists
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    # Load JSON
    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

    # Infer type if not provided
    if json_type is None:
        json_type = infer_type(file_path)

    if json_type is None:
        return False, [f"Could not infer JSON type from filename. Use --type to specify."]

    if json_type not in VALIDATORS:
        return False, [f"Unknown JSON type: {json_type}. Valid types: {list(VALIDATORS.keys())}"]

    # Run validation
    validator = VALIDATORS[json_type]
    errors = validator(data)

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON files produced by skill-creator-edge"
    )
    parser.add_argument("file", type=Path, help="Path to the JSON file to validate")
    parser.add_argument(
        "--type", "-t",
        choices=list(VALIDATORS.keys()),
        help="JSON type (inferred from filename if not specified)"
    )

    args = parser.parse_args()

    is_valid, errors = validate_file(args.file, args.type)

    if is_valid:
        print(f"✓ {args.file} is valid")
        sys.exit(0)
    else:
        print(f"✗ {args.file} has {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
