"""
Unit tests for the 5 CogniCore MCP tools exposed to Claude Code.
"""

import json
import os
import tempfile
import pytest
from cognicore.integrations.claude_code import ClaudeCodeIntegration
from cognicore.extension.remote import (
    cognicore_record_experience,
    cognicore_verify_experience,
    cognicore_recall_experience,
    cognicore_share_experience,
    cognicore_check_experience,
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


def test_claude_code_integration_get_tools():
    integration = ClaudeCodeIntegration()
    tools = integration.get_tools()
    assert len(tools) == 5
    tool_names = [t.__name__ for t in tools]
    assert "cognicore_record_experience" in tool_names
    assert "cognicore_verify_experience" in tool_names
    assert "cognicore_recall_experience" in tool_names
    assert "cognicore_share_experience" in tool_names
    assert "cognicore_check_experience" in tool_names


def test_record_and_recall_experience(temp_db):
    # Record
    rec_raw = cognicore_record_experience(
        task="Fix database connection leak",
        problem="Connection pool exhausted under load",
        solution="Always close connections in a finally block",
        why_it_worked="Ensures socket release even when exceptions occur",
        attempts_json=json.dumps([
            {"approach": "Increase pool size to 100", "outcome": "failure", "reason": "Only delayed the exhaustion"},
            {"approach": "Use finally block around pool.release()", "outcome": "success", "reason": "Deterministic cleanup"}
        ]),
        repository_id="test/repo",
        python_version="3.11.0",
        dependencies_json=json.dumps({"sqlalchemy": "2.0.0"}),
    )
    rec = json.loads(rec_raw)
    assert rec["status"] == "recorded"
    assert rec["failures_stored"] == 1
    exp_id = rec["experience_id"]

    # Recall
    recall_raw = cognicore_recall_experience(
        query="database connection leak pool exhaustion",
        include_failures=True,
    )
    recall = json.loads(recall_raw)
    assert len(recall["experiences"]) >= 1
    assert len(recall["failure_warnings"]) >= 1
    assert "Increase pool size" in recall["failure_warnings"][0]["problem"]


def test_share_experience(temp_db):
    rec_raw = cognicore_record_experience(
        task="Fix auth header parsing",
        problem="Malformed bearer token causes 500 error",
        solution="Validate Bearer prefix length before slicing",
        why_it_worked="Prevents IndexError",
    )
    rec = json.loads(rec_raw)
    exp_id = rec["experience_id"]

    # Verify first (only verified experiences can be shared)
    cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([{"command": "pytest tests/auth.py", "exit_code": 0}]),
    )

    # Share
    share_raw = cognicore_share_experience(
        query="auth header parsing",
        target_agent_id="secondary_worker",
    )
    share = json.loads(share_raw)
    assert share["status"] == "transferred"
    assert share["target_agent"] == "secondary_worker"
