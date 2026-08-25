"""
End-to-End Three-Session Real Coding Test for CogniCore Claude Code Plugin.

Validates the complete lifecycle across 3 distinct sessions:
1. Session 1: Real bug, multi-attempt failures, successful fix, pytest execution, VerificationGate promotion. Session terminates completely.
2. Session 2: Fresh session (zero context bleed), recalls verified solution + DO NOT REPEAT failure warnings, executes cleanly.
3. Session 3: Environment/dependency change, check_experience marks memory STALE / revalidation required.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from cognicore.extension.remote import (
    cognicore_record_experience,
    cognicore_verify_experience,
    cognicore_recall_experience,
    cognicore_check_experience,
)


@pytest.fixture
def test_repo_env():
    """Creates a realistic isolated code repository with genuine test suite and persistent DB."""
    temp_dir = tempfile.mkdtemp(prefix="cognicore_e2e_")
    repo_dir = Path(temp_dir) / "math_repo"
    repo_dir.mkdir(parents=True)
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()

    db_path = str(Path(temp_dir) / "cognicore_e2e.db")
    os.environ["COGNICORE_DB_PATH"] = db_path

    # Initial buggy math_utils.py
    (repo_dir / "math_utils.py").write_text(
        "def calculate_ratio(a, b):\n"
        "    # Bug: Unhandled divide by zero\n"
        "    return a / b\n",
        encoding="utf-8"
    )

    # Test file test_math_utils.py
    (tests_dir / "test_math_utils.py").write_text(
        "import pytest\n"
        "from math_utils import calculate_ratio\n\n"
        "def test_valid_ratio():\n"
        "    assert calculate_ratio(10, 2) == 5.0\n"
        "    assert calculate_ratio(7, 2) == 3.5\n\n"
        "def test_zero_denominator_raises_value_error():\n"
        "    with pytest.raises(ValueError, match='Denominator cannot be zero'):\n"
        "        calculate_ratio(10, 0)\n\n"
        "def test_type_validation():\n"
        "    with pytest.raises(TypeError, match='Inputs must be numeric'):\n"
        "        calculate_ratio('10', 2)\n",
        encoding="utf-8"
    )

    yield {
        "temp_dir": temp_dir,
        "repo_dir": repo_dir,
        "db_path": db_path,
    }

    # Cleanup
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def test_complete_three_session_workflow(test_repo_env):
    repo_dir = test_repo_env["repo_dir"]
    db_path = test_repo_env["db_path"]

    # =========================================================================
    # SESSION 1: Exploration, Multi-attempt Failures, Success, Verification
    # =========================================================================
    print("\n--- STARTING SESSION 1 ---")

    # Attempt A: a / (b + 1e-9) -> Fails tests (altered precision and wrong exception)
    (repo_dir / "math_utils.py").write_text(
        "def calculate_ratio(a, b):\n"
        "    return a / (b + 1e-9)\n",
        encoding="utf-8"
    )
    res_a = subprocess.run([sys.executable, "-m", "pytest", "tests/test_math_utils.py", "-q"], cwd=str(repo_dir), capture_output=True, text=True)
    assert res_a.returncode != 0, "Attempt A must fail test suite"

    # Attempt B: return float('inf') on zero -> Fails test_zero_denominator_raises_value_error
    (repo_dir / "math_utils.py").write_text(
        "def calculate_ratio(a, b):\n"
        "    if b == 0:\n"
        "        return float('inf')\n"
        "    return a / b\n",
        encoding="utf-8"
    )
    res_b = subprocess.run([sys.executable, "-m", "pytest", "tests/test_math_utils.py", "-q"], cwd=str(repo_dir), capture_output=True, text=True)
    assert res_b.returncode != 0, "Attempt B must fail test suite"

    # Attempt C: Proper guard and type validation -> PASSES!
    (repo_dir / "math_utils.py").write_text(
        "def calculate_ratio(a, b):\n"
        "    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n"
        "        raise TypeError('Inputs must be numeric')\n"
        "    if b == 0:\n"
        "        raise ValueError('Denominator cannot be zero')\n"
        "    return float(a) / float(b)\n",
        encoding="utf-8"
    )
    res_c = subprocess.run([sys.executable, "-m", "pytest", "tests/test_math_utils.py", "-q"], cwd=str(repo_dir), capture_output=True, text=True)
    assert res_c.returncode == 0, f"Attempt C must pass tests: {res_c.stdout}"

    # Record candidate experience in CogniCore
    rec_raw = cognicore_record_experience(
        task="Fix ZeroDivisionError in math_utils calculate_ratio",
        problem="calculate_ratio crashed on b=0 and accepted invalid string types",
        solution="Validate input types numeric and raise ValueError('Denominator cannot be zero') when b==0",
        why_it_worked="Enforces clean API contract and handles divide-by-zero boundary gracefully",
        attempts_json=json.dumps([
            {
                "approach": "Return a / (b + 1e-9)",
                "outcome": "failure",
                "reason": "Alters numerical precision for valid numbers and fails contract",
            },
            {
                "approach": "Return float('inf') on zero denominator",
                "outcome": "failure",
                "reason": "Fails contract requirement expecting ValueError exception",
            },
            {
                "approach": "Explicit type check + raise ValueError on b==0",
                "outcome": "success",
                "reason": "Satisfies all test invariants and preserves numerical precision",
            }
        ]),
        repository_id="acme/math_repo",
        python_version="3.11.0",
        dependencies_json=json.dumps({"math-lib": "1.0.0"}),
    )
    rec_data = json.loads(rec_raw)
    exp_id = rec_data["experience_id"]
    assert rec_data["failures_stored"] == 2

    # Verification Gate: Submit real test execution evidence
    ver_raw = cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([
            {
                "command": "pytest tests/test_math_utils.py -q",
                "exit_code": res_c.returncode,
                "stdout_hash": "e2e_pass_hash_123",
            }
        ])
    )
    ver_data = json.loads(ver_raw)
    assert ver_data["status"] == "verified"
    assert ver_data["passed"] is True

    print("SESSION 1 COMPLETE: Experience recorded & verified. Closing session.\n")

    # =========================================================================
    # SESSION 2: Fresh Session (Zero Context Bleed)
    # =========================================================================
    print("--- STARTING FRESH SESSION 2 ---")

    # Query CogniCore without any previous conversation history
    recall_raw = cognicore_recall_experience(
        query="calculate_ratio divide by zero issue",
        include_failures=True,
        require_verified=True,
        python_version="3.11.0",
        dependencies_json=json.dumps({"math-lib": "1.0.0"}),
    )
    recall_data = json.loads(recall_raw)

    # Validate failure warnings
    assert len(recall_data["failure_warnings"]) >= 2
    failure_messages = [f["problem"] for f in recall_data["failure_warnings"]]
    assert any("Return a / (b + 1e-9)" in msg for msg in failure_messages)
    assert any("Return float('inf')" in msg for msg in failure_messages)

    # Validate verified solution
    assert len(recall_data["experiences"]) >= 1
    exp = recall_data["experiences"][0]
    assert exp["verification_status"] == "verified"
    assert "raise ValueError" in exp["solution"]

    print("SESSION 2 COMPLETE: Fresh session retrieved verified guidance and failure warnings without context bleed.\n")

    # =========================================================================
    # SESSION 3: Environment / Dependency Change
    # =========================================================================
    print("--- STARTING SESSION 3 (ENVIRONMENT UPGRADE) ---")

    verified_exp_id = ver_data["experience_id"]
    # Environment changes to math-lib v2.0.0
    chk_raw = cognicore_check_experience(
        experience_id=verified_exp_id,
        python_version="3.11.0",
        dependencies_json=json.dumps({"math-lib": "2.0.0"}),
    )
    chk_data = json.loads(chk_raw)

    assert chk_data["stale"] is True
    assert chk_data["valid"] is False
    assert any("math-lib" in r for r in chk_data["staleness_reasons"])
    print(f"SESSION 3 COMPLETE: Staleness successfully detected ({chk_data['staleness_reasons']}).")
