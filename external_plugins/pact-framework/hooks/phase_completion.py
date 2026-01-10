#!/usr/bin/env python3
"""
Location: .claude/hooks/phase_completion.py
Summary: Stop hook that verifies phase completion and reminds about decision logs.
Used by: Claude Code settings.json Stop hook

Checks for CODE phase completion without decision logs and
reminds about documentation requirements.

Input: JSON from stdin with session transcript/context
Output: JSON with `systemMessage` for reminders if needed
"""

import json
import sys
import os
from pathlib import Path


# Indicators that CODE phase work was performed
CODE_PHASE_INDICATORS = [
    "pact-backend-coder",
    "pact-frontend-coder",
    "pact-database-engineer",
    "pact_backend_coder",
    "pact_frontend_coder",
    "pact_database_engineer",
]

# Terms indicating decision log was mentioned or created
DECISION_LOG_MENTIONS = [
    "decision-log",
    "decision log",
    "decision_log",
    "decisionlog",
    "docs/decision-logs",
    "decision-logs/",
]


def check_for_code_phase_activity(transcript: str) -> bool:
    """
    Determine if CODE phase agents were invoked in this session.

    Args:
        transcript: The session transcript

    Returns:
        True if CODE phase activity detected
    """
    transcript_lower = transcript.lower()
    return any(indicator in transcript_lower for indicator in CODE_PHASE_INDICATORS)


def check_decision_log_mentioned(transcript: str) -> bool:
    """
    Check if decision logs were mentioned in the transcript.

    Args:
        transcript: The session transcript

    Returns:
        True if decision logs were discussed or created
    """
    transcript_lower = transcript.lower()
    return any(mention in transcript_lower for mention in DECISION_LOG_MENTIONS)


def check_decision_logs_exist(project_dir: str) -> bool:
    """
    Check if any decision logs exist in the project.

    Args:
        project_dir: The project root directory

    Returns:
        True if decision-logs directory exists and contains files
    """
    decision_logs_dir = Path(project_dir) / "docs" / "decision-logs"
    if not decision_logs_dir.is_dir():
        return False

    # Check for any markdown files in the directory
    return any(decision_logs_dir.glob("*.md"))


def check_for_test_reminders(transcript: str) -> bool:
    """
    Check if testing was discussed for completed code work.

    Args:
        transcript: The session transcript

    Returns:
        True if testing appears to be addressed
    """
    transcript_lower = transcript.lower()
    test_indicators = [
        "pact-test-engineer",
        "test engineer",
        "testing",
        "unit test",
        "integration test",
        "test coverage",
    ]
    return any(indicator in transcript_lower for indicator in test_indicators)


def main():
    """
    Main entry point for the Stop hook.

    Checks for CODE phase indicators and reminds about decision logs
    and testing if not mentioned in the session.
    """
    try:
        # Read input from stdin
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            input_data = {}

        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
        transcript = input_data.get("transcript", "")

        # If no transcript, nothing to check
        if not transcript:
            sys.exit(0)

        messages = []

        # Check for CODE phase activity
        was_code_phase = check_for_code_phase_activity(transcript)

        if was_code_phase:
            # Check if decision logs were addressed
            decision_log_mentioned = check_decision_log_mentioned(transcript)
            decision_logs_exist = check_decision_logs_exist(project_dir)

            if not decision_log_mentioned and not decision_logs_exist:
                messages.append(
                    "CODE Phase Reminder: Decision logs should be created at "
                    "docs/decision-logs/{feature}-{domain}.md to document key "
                    "implementation decisions and trade-offs."
                )

            # Check if testing was addressed
            testing_discussed = check_for_test_reminders(transcript)
            if not testing_discussed:
                messages.append(
                    "TEST Phase Reminder: Consider invoking pact-test-engineer "
                    "to verify the implementation."
                )

        # Output messages if any reminders are needed
        if messages:
            output = {
                "systemMessage": " | ".join(messages)
            }
            print(json.dumps(output))

        sys.exit(0)

    except Exception as e:
        # Don't block on errors - just warn
        print(f"Hook warning (phase_completion): {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
