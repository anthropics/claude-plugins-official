"""
Tests for Staleness Detection, Environment Compatibility, and Supersession in CogniCore.
"""

import json
import os
import tempfile
import pytest
from cognicore.extension.remote import (
    cognicore_record_experience,
    cognicore_verify_experience,
    cognicore_check_experience,
    cognicore_recall_experience,
)
from cognicore.experience.manager import ExperienceManager
from cognicore.experience.schema import StructuredExperience, RepositoryContext, EnvironmentContext, VerificationStatus
from cognicore.memory import SQLiteMemoryBackend


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


def test_staleness_on_dependency_major_bump(temp_db):
    """Part 9 / 14: Dependency major bump causes experience to become stale."""
    # Session 1 with math-lib v1.0.0
    rec = json.loads(cognicore_record_experience(
        task="Calculate matrix eigenvalues",
        problem="Deprecated API in matrix solver",
        solution="Use math_lib.linalg.eigvals()",
        why_it_worked="New standard function in v1",
        python_version="3.11.0",
        dependencies_json=json.dumps({"math-lib": "1.0.0"}),
    ))
    exp_id = rec["experience_id"]

    ver = json.loads(cognicore_verify_experience(
        experience_id=exp_id,
        evidence_json=json.dumps([{"command": "pytest tests/linalg.py", "exit_code": 0}]),
    ))
    verified_id = ver["experience_id"]

    # Session 2 with math-lib v2.0.0
    chk = json.loads(cognicore_check_experience(
        experience_id=verified_id,
        python_version="3.11.0",
        dependencies_json=json.dumps({"math-lib": "2.0.0"}),
    ))

    assert chk["stale"] is True
    assert chk["valid"] is False
    assert "Re-validation required" in chk.get("reason", "") or any("math-lib" in r for r in chk.get("staleness_reasons", []))
    assert any("math-lib" in r for r in chk["staleness_reasons"])


def test_supersession_prefers_newer_solution(temp_db):
    """Part 11: Supersession replaces older solution with newer validated solution."""
    backend = SQLiteMemoryBackend(temp_db)
    manager = ExperienceManager(backend)

    # Experience A (Old solution)
    exp_a = StructuredExperience(
        task="Sort large dataset",
        problem="OOM on 10M rows",
        solution="Use external merge sort with 500MB chunk files",
        why_it_worked="Fits chunks in RAM",
        verification_status=VerificationStatus.VERIFIED.value,
        repository=RepositoryContext(repo_id="repo-analytics"),
    )
    id_a = manager.record(exp_a)

    # Experience B (Newer superseding solution using Polars/DuckDB)
    exp_b = StructuredExperience(
        task="Sort large dataset",
        problem="OOM on 10M rows",
        solution="Use DuckDB streaming query with memory_limit='2GB'",
        why_it_worked="Native vectorized out-of-core execution is 10x faster and bounded",
        verification_status=VerificationStatus.VERIFIED.value,
        repository=RepositoryContext(repo_id="repo-analytics"),
    )
    id_b = manager.record(exp_b)

    # Supersede A with B
    manager.supersede(id_a, id_b, reason="DuckDB streaming replaces legacy chunk files")

    # Retrieval should prefer Experience B
    results = manager.retrieve(query="Sort large dataset OOM memory", top_k=5)
    retrieved_ids = [e.experience_id for e in results.experiences]

    assert id_b in retrieved_ids
    # Experience A was superseded, so it should not be the top current active guidance
    if id_a in retrieved_ids:
        assert retrieved_ids.index(id_b) < retrieved_ids.index(id_a)
