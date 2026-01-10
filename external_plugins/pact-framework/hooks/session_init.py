#!/usr/bin/env python3
"""
Location: .claude/hooks/session_init.py
Summary: SessionStart hook that detects active plans and notifies user.
Used by: Claude Code settings.json SessionStart hook

Checks docs/plans/ for in-progress work and notifies the user
to consider resuming with /PACT:orchestrate.

Input: JSON from stdin with session context
Output: JSON with `systemMessage` if active plans found
"""

import json
import sys
import os
from pathlib import Path


def find_active_plans(project_dir: str) -> list:
    """
    Find plans with IN_PROGRESS status or uncompleted items.

    Args:
        project_dir: The project root directory path

    Returns:
        List of plan filenames that appear to be in progress
    """
    plans_dir = Path(project_dir) / "docs" / "plans"
    active_plans = []

    if not plans_dir.is_dir():
        return active_plans

    for plan_file in plans_dir.glob("*-plan.md"):
        try:
            content = plan_file.read_text(encoding='utf-8')
            # Check for various in-progress indicators
            in_progress_indicators = [
                "Status: IN_PROGRESS",
                "Status: In Progress",
                "status: in_progress",
                "Status: ACTIVE",
                "Status: Active",
            ]

            # Check for explicit status markers
            has_in_progress_status = any(
                indicator in content for indicator in in_progress_indicators
            )

            # Check for unchecked items (uncompleted tasks)
            has_unchecked_items = "[ ] " in content

            # Check for explicit completion status (to avoid false positives)
            is_completed = any(
                status in content for status in [
                    "Status: COMPLETED",
                    "Status: Completed",
                    "Status: DONE",
                    "Status: Done",
                ]
            )

            if has_in_progress_status or (has_unchecked_items and not is_completed):
                active_plans.append(plan_file.name)

        except (IOError, UnicodeDecodeError):
            # Skip files we can't read
            continue

    return active_plans


def main():
    """
    Main entry point for the SessionStart hook.

    Reads session context from stdin, checks for active plans,
    and outputs a system message if any are found.
    """
    try:
        # Read input from stdin (may be empty for SessionStart)
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            input_data = {}

        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")

        active_plans = find_active_plans(project_dir)

        if active_plans:
            # Format the plan list, limiting to 3 for brevity
            plan_list = ", ".join(active_plans[:3])
            if len(active_plans) > 3:
                plan_list += f" (+{len(active_plans) - 3} more)"

            output = {
                "systemMessage": (
                    f"PACT Notice: Active plan(s) found: {plan_list}. "
                    "Consider resuming with /PACT:orchestrate."
                )
            }
            print(json.dumps(output))

        sys.exit(0)

    except Exception as e:
        # Don't block session start on errors - just warn
        print(f"Hook warning (session_init): {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
