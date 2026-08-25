"""
Tests for CogniCore Failure Memory in Claude Code.
Ensures failed attempts are first-class citizens that guide future sessions with DO NOT REPEAT warnings,
and that environment-conditional failure validity adapts when dependencies or runtime environments change.
"""

import json
import os
import tempfile
import pytest
from cognicore.extension.remote import (
    cognicore_record_experience,
    cognicore_verify_experience,
    cognicore_recall_experience,
)


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["COGNICORE_DB_PATH"] = db_path
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_failure_memory_indexing_and_warning(temp_db):
    # Agent 1 solves a problem after 2 failures
    rec = json.loads(cognicore_record_experience(
        task="Fix JWT authentication token expiration bug",
        problem="Users logged out randomly after 5 minutes",
        solution="Synchronize clock skew tolerances and use refresh token rotation",
        why_it_worked="Compensates for 30s NTP drift across distributed instances",
        attempts_json=json.dumps([
            {
                "approach": "Increase JWT expiration time to 24 hours",
                "outcome": "failure",
                "reason": "Security vulnerability: revoked tokens remained valid for 24h"
            },
            {
                "approach": "Disable token expiration check entirely in middleware",
                "outcome": "failure",
                "reason": "Breaks authentication contract and fails test_auth_expired"
            },
            {
                "approach": "Synchronize clock skew leeway (leeway=60) and enable refresh rotation",
                "outcome": "success",
                "reason": "Solves clock drift while maintaining short token lifespans"
            }
        ]),
        repository_id="acme/auth-service",
    ))
    exp_id = rec["experience_id"]
    assert rec["failures_stored"] == 2

    # Promote to verified
    cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([
            {"command": "pytest tests/auth/ -q", "exit_code": 0}
        ])
    )

    # Agent 2 encounters a similar task in a separate context
    recall = json.loads(cognicore_recall_experience(
        query="JWT auth expiration bug random logout",
        include_failures=True,
    ))

    # Verify structured failure warnings
    failure_warnings = recall["failure_warnings"]
    assert len(failure_warnings) >= 2

    fail_texts = [f["problem"] for f in failure_warnings]
    assert any("Increase JWT expiration time" in t for t in fail_texts)
    assert any("Disable token expiration check" in t for t in fail_texts)

    # Verify the successful solution is also returned
    assert len(recall["experiences"]) >= 1
    exp = recall["experiences"][0]
    assert "refresh token rotation" in exp["solution"]
    assert exp["verification_status"] == "verified"


def test_conditional_failure_becomes_reusable_after_environment_change(temp_db):
    """
    Test: Environment-conditional failure is active in matching environment,
    but becomes reconsiderable when the relevant dependency is upgraded.
    Historical failure record remains permanently preserved.
    """
    # Session 1: Record a failure caused specifically by a bug in requests 2.28.0
    rec = json.loads(cognicore_record_experience(
        task="HTTP connection keep-alive timeout",
        problem="Connection hung indefinitely during socket reuse",
        solution="Configure custom HTTPAdapter with explicit pool timeouts",
        why_it_worked="Safely handles socket close events",
        attempts_json=json.dumps([
            {
                "approach": "Use default Session with stream=True",
                "outcome": "failure",
                "reason": "Known connection pool bug in requests 2.28.0"
            },
            {
                "approach": "Configure custom HTTPAdapter with explicit pool timeouts",
                "outcome": "success",
                "reason": "Safely handles socket close events"
            }
        ]),
        python_version="3.11.0",
        dependencies_json=json.dumps({"requests": "2.28.0"}),
    ))
    assert rec["failures_stored"] == 1

    # In Environment v1 (requests 2.28.0): Failure is ACTIVE as DO NOT REPEAT
    recall_v1 = json.loads(cognicore_recall_experience(
        query="HTTP connection keep-alive timeout socket reuse",
        include_failures=True,
        python_version="3.11.0",
        dependencies_json=json.dumps({"requests": "2.28.0"}),
    ))
    assert len(recall_v1["failure_warnings"]) == 1
    assert "stream=True" in recall_v1["failure_warnings"][0]["problem"]

    # In Environment v2 (requests upgraded to 3.0.0):
    # The dependency changed, so the 2.28.0-specific failure does NOT actively block the session
    recall_v2 = json.loads(cognicore_recall_experience(
        query="HTTP connection keep-alive timeout socket reuse",
        include_failures=True,
        python_version="3.11.0",
        dependencies_json=json.dumps({"requests": "3.0.0"}),
    ))
    assert len(recall_v2["failure_warnings"]) == 0

    # Historical failure entry remains permanently in DB for audit trail
    recall_all = json.loads(cognicore_recall_experience(
        query="HTTP connection keep-alive timeout socket reuse",
        include_failures=True,
    ))
    assert len(recall_all["failure_warnings"]) >= 1


def test_permanent_failure_remains_active_across_environment_changes(temp_db):
    """
    Test: Architectural/algorithmic failures without library dependencies
    remain active as DO NOT REPEAT across all environment changes.
    """
    rec = json.loads(cognicore_record_experience(
        task="Prevent divide by zero in calculate_rate",
        problem="Unhandled ZeroDivisionError on rate=0",
        solution="Raise ValueError on non-positive rate",
        why_it_worked="Enforces clean API validation contract",
        attempts_json=json.dumps([
            {
                "approach": "Return 1e-9 epsilon float value",
                "outcome": "failure",
                "reason": "Alters precision and violates contract"
            },
            {
                "approach": "Raise ValueError on non-positive rate",
                "outcome": "success",
                "reason": "Enforces clean API validation contract"
            }
        ]),
        python_version="3.11.0",
    ))
    assert rec["failures_stored"] == 1

    # Check under Python 3.11
    recall_py311 = json.loads(cognicore_recall_experience(
        query="Prevent divide by zero in calculate_rate",
        include_failures=True,
        python_version="3.11.0",
    ))
    assert len(recall_py311["failure_warnings"]) == 1

    # Check under Python 3.12 (different environment, but permanent failure remains active)
    recall_py312 = json.loads(cognicore_recall_experience(
        query="Prevent divide by zero in calculate_rate",
        include_failures=True,
        python_version="3.12.0",
    ))
    assert len(recall_py312["failure_warnings"]) == 1
    assert "1e-9 epsilon" in recall_py312["failure_warnings"][0]["problem"]
