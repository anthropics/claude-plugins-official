#!/usr/bin/env python3
"""
Initialize JSON files with the correct structure for skill-creator-edge.

Creates template JSON files that can be filled in.

Usage:
    python init_json.py <type> <output_path>

Examples:
    python init_json.py evals evals/evals.json
    python init_json.py grading run-1/grading.json
    python init_json.py benchmark benchmarks/2026-01-15/benchmark.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


TEMPLATES = {
    "evals": {
        "skill_name": "<skill-name>",
        "evals": [
            {
                "id": 1,
                "prompt": "Example task prompt",
                "expected_output": "Description of expected result",
                "files": [],
                "expectations": [
                    "The output includes X",
                    "The skill correctly handles Y"
                ]
            }
        ]
    },

    "grading": {
        "expectations": [
            {
                "text": "Example expectation",
                "passed": True,
                "evidence": "Found in transcript: ..."
            }
        ],
        "summary": {
            "passed": 1,
            "failed": 0,
            "total": 1,
            "pass_rate": 1.0
        },
        "execution_metrics": {
            "tool_calls": {
                "Read": 0,
                "Write": 0,
                "Bash": 0,
                "Edit": 0,
                "Glob": 0,
                "Grep": 0
            },
            "total_tool_calls": 0,
            "total_steps": 0,
            "errors_encountered": 0,
            "output_chars": 0,
            "transcript_chars": 0
        },
        "timing": {
            "executor_duration_seconds": 0.0,
            "grader_duration_seconds": 0.0,
            "total_duration_seconds": 0.0
        },
        "claims": [],
        "user_notes_summary": {
            "uncertainties": [],
            "needs_review": [],
            "workarounds": []
        }
    },

    "benchmark": {
        "metadata": {
            "skill_name": "<skill-name>",
            "skill_path": "<path/to/skill>",
            "executor_model": "<model-name>",
            "analyzer_model": "<model-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": [1],
            "runs_per_configuration": 3
        },
        "runs": [
            {
                "eval_id": 1,
                "configuration": "with_skill",
                "run_number": 1,
                "result": {
                    "pass_rate": 0.0,
                    "passed": 0,
                    "failed": 0,
                    "total": 0,
                    "time_seconds": 0.0,
                    "tokens": 0,
                    "tool_calls": 0,
                    "errors": 0
                },
                "expectations": [],
                "notes": []
            }
        ],
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            },
            "without_skill": {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            },
            "delta": {
                "pass_rate": "+0.0",
                "time_seconds": "+0.0",
                "tokens": "+0"
            }
        },
        "notes": []
    },

    "metrics": {
        "tool_calls": {
            "Read": 0,
            "Write": 0,
            "Bash": 0,
            "Edit": 0,
            "Glob": 0,
            "Grep": 0
        },
        "total_tool_calls": 0,
        "total_steps": 0,
        "files_created": [],
        "errors_encountered": 0,
        "output_chars": 0,
        "transcript_chars": 0
    },

    "timing": {
        "executor_start": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "executor_end": "",
        "executor_duration_seconds": 0.0,
        "grader_start": "",
        "grader_end": "",
        "grader_duration_seconds": 0.0,
        "total_duration_seconds": 0.0
    },

    "history": {
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill_name": "<skill-name>",
        "current_best": "v0",
        "iterations": [
            {
                "version": "v0",
                "parent": None,
                "expectation_pass_rate": 0.0,
                "grading_result": "baseline",
                "is_current_best": True
            }
        ]
    },

    "comparison": {
        "winner": "A",
        "reasoning": "Explanation of why the winner was chosen",
        "rubric": {
            "A": {
                "content": {
                    "correctness": 5,
                    "completeness": 5,
                    "accuracy": 5
                },
                "structure": {
                    "organization": 5,
                    "formatting": 5,
                    "usability": 5
                },
                "content_score": 5.0,
                "structure_score": 5.0,
                "overall_score": 10.0
            },
            "B": {
                "content": {
                    "correctness": 3,
                    "completeness": 3,
                    "accuracy": 3
                },
                "structure": {
                    "organization": 3,
                    "formatting": 3,
                    "usability": 3
                },
                "content_score": 3.0,
                "structure_score": 3.0,
                "overall_score": 6.0
            }
        },
        "output_quality": {
            "A": {
                "score": 10,
                "strengths": [],
                "weaknesses": []
            },
            "B": {
                "score": 6,
                "strengths": [],
                "weaknesses": []
            }
        }
    },

    "analysis": {
        "comparison_summary": {
            "winner": "A",
            "winner_skill": "<path/to/winner>",
            "loser_skill": "<path/to/loser>",
            "comparator_reasoning": "Summary of comparison"
        },
        "winner_strengths": [],
        "loser_weaknesses": [],
        "instruction_following": {
            "winner": {
                "score": 10,
                "issues": []
            },
            "loser": {
                "score": 5,
                "issues": []
            }
        },
        "improvement_suggestions": [
            {
                "priority": "high",
                "category": "instructions",
                "suggestion": "Specific improvement suggestion",
                "expected_impact": "Why this would help"
            }
        ],
        "transcript_insights": {
            "winner_execution_pattern": "Description of how winner executed",
            "loser_execution_pattern": "Description of how loser executed"
        }
    }
}


def init_json(json_type: str, output_path: Path, force: bool = False) -> bool:
    """
    Initialize a JSON file with the correct template structure.

    Returns True on success, False on failure.
    """
    if json_type not in TEMPLATES:
        print(f"Unknown type: {json_type}. Valid types: {list(TEMPLATES.keys())}")
        return False

    if output_path.exists() and not force:
        print(f"File already exists: {output_path}")
        print("Use --force to overwrite")
        return False

    # Create parent directories
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write template
    template = TEMPLATES[json_type]
    with open(output_path, "w") as f:
        json.dump(template, f, indent=2)

    print(f"Created {json_type} template: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Initialize JSON files with correct structure"
    )
    parser.add_argument(
        "type",
        choices=list(TEMPLATES.keys()),
        help="Type of JSON file to create"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output path for the JSON file"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing file"
    )

    args = parser.parse_args()

    success = init_json(args.type, args.output, args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
