"""
Tests for CogniCore VerificationGate integration in Claude Code.
Ensures experiences are promoted ONLY with valid, successful execution evidence.
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


def test_case_a_claim_success_but_command_failed(temp_db):
    """Case A: Claude claims tests passed but command exited with code 1."""
    rec = json.loads(cognicore_record_experience(
        task="Fix race condition",
        problem="Deadlock on concurrent writes",
        solution="Use row-level locking",
        why_it_worked="Prevents table lock collision",
    ))
    exp_id = rec["experience_id"]

    # Attempt to verify with failing exit code
    ver = json.loads(cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([
            {"command": "pytest tests/race_test.py", "exit_code": 1, "stdout_hash": "err123"}
        ])
    ))
    assert ver["status"] == "failed"
    assert ver["passed"] is False
    assert len(ver["blockers"]) > 0
    assert "Non-zero exit code" in ver["blockers"][0]

    # Verify that memory state remains unverified/candidate
    recall = json.loads(cognicore_recall_experience(
        query="race condition deadlock",
        require_verified=True,
    ))
    assert len(recall["experiences"]) == 0, "Unverified experience must not be returned when require_verified=True"


def test_case_b_command_succeeds_promoted(temp_db):
    """Case B: Command succeeds with exit_code == 0."""
    rec = json.loads(cognicore_record_experience(
        task="Fix race condition",
        problem="Deadlock on concurrent writes",
        solution="Use row-level locking",
        why_it_worked="Prevents table lock collision",
    ))
    exp_id = rec["experience_id"]

    # Verify with success
    ver = json.loads(cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([
            {"command": "pytest tests/race_test.py", "exit_code": 0, "stdout_hash": "ok123"}
        ])
    ))
    assert ver["status"] == "verified"
    assert ver["passed"] is True
    assert len(ver["blockers"]) == 0

    # Recall should now find it when require_verified=True
    recall = json.loads(cognicore_recall_experience(
        query="race condition deadlock",
        require_verified=True,
    ))
    assert len(recall["experiences"]) >= 1
    assert recall["experiences"][0]["verification_status"] == "verified"


def test_case_c_build_succeeds(temp_db):
    """Case C: Build command succeeds."""
    rec = json.loads(cognicore_record_experience(
        task="Compile native extension",
        problem="Missing C++ header",
        solution="Include <cstdint> explicitly",
        why_it_worked="Defines uint64_t for MSVC",
    ))
    exp_id = rec["experience_id"]

    ver = json.loads(cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([
            {"command": "cmake --build . --config Release", "exit_code": 0}
        ])
    ))
    assert ver["status"] == "verified"
    assert ver["passed"] is True


def test_case_d_test_command_missing(temp_db):
    """Case D: Evidence has empty command string."""
    rec = json.loads(cognicore_record_experience(
        task="Fix CSS alignment",
        problem="Flexbox overflow",
        solution="Set flex-shrink: 0",
        why_it_worked="Prevents container squeeze",
    ))
    exp_id = rec["experience_id"]

    ver = json.loads(cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([
            {"command": "", "exit_code": 0}
        ])
    ))
    assert ver["status"] == "failed"
    assert ver["passed"] is False
    assert any("Missing command" in b for b in ver["blockers"])


def test_case_e_malformed_evidence_json(temp_db):
    """Case E: Evidence JSON is invalid / malformed."""
    rec = json.loads(cognicore_record_experience(
        task="Fix memory leak",
        problem="Unbounded cache growth",
        solution="Use LRU cache with maxsize=1024",
        why_it_worked="Evicts stale keys",
    ))
    exp_id = rec["experience_id"]

    ver = json.loads(cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json="not-a-json-string{{"
    ))
    assert ver["status"] == "error"
