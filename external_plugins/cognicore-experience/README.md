# CogniCore Structured Validated Experience Plugin for Claude Code

A community plugin for Claude Code providing evidence-gated experience memory, multi-attempt failure tracking (`DO NOT REPEAT`), cross-session persistence, environment compatibility validation, and cross-agent memory transfer.

> **Claude Code's auto-memory preserves useful notes across sessions; this plugin adds a structured experience layer that records failed approaches, successful solutions, verification evidence, and environment conditions so experiences can be evaluated before reuse.**

## Overview

Unlike standard conversational memory that dumps raw transcripts into prompt context, **CogniCore Structured Validated Experience** captures concise, structured units of engineering knowledge:

1. **Problem Statement & Symptoms**
2. **Failed Attempts & Root Cause Explanations** (`DO NOT REPEAT`)
3. **Verified Successful Solution**
4. **Verifiable Execution Evidence** (Command & `exit_code == 0`)
5. **Runtime Environment Metadata** (Python version, dependencies, git commit)

Experiences are strictly gated: an experience **NEVER** becomes `VERIFIED` based on LLM claims alone—it requires verifiable command execution proof evaluated by CogniCore's `VerificationGate`.

---

## Architecture

```text
               Claude Code
                    │
            SessionStart Hook
                    │ (detects environment & repo)
                    ▼
     cognicore_recall_experience()
        ┌───────────┴───────────┐
        ▼                       ▼
DO NOT REPEAT Warnings    VERIFIED Solutions
        │                       │
        └───────────┬───────────┘
                    ▼
           Work on Coding Task
        ┌───────────┴───────────┐
        ▼                       ▼
     Failure                 Success
        │                       │
        └───────────┬───────────┘
                    ▼
      PostToolUse Hook (Buffers Evidence)
                    ▼
     cognicore_record_experience()  ──► CANDIDATE
                    ▼
     cognicore_verify_experience()
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    Exit Code != 0      Exit Code == 0
       REJECTED            PROMOTED
   (Stays Candidate)     (To VERIFIED)
                              │
                              ▼
                     CogniCore Persistent
                        SQLite Memory
                              │
                              ▼
                  Future Claude Code Session
                              │
                  Environment Compatibility
                              │
                  Verified Experience Recall
```

---

## The 5 MCP Tools

The plugin exposes 5 MCP tools powered by `cognicore-env`:

| Tool | Purpose | Reads/Writes | Verification Behavior |
|---|---|---|---|
| `cognicore_recall_experience` | Recalls verified solutions and past failure warnings | Reads Memory | Filters by verification state & environment compatibility |
| `cognicore_record_experience` | Records problem, attempts, failure reasons, and working fix | Writes Memory | Stored as `CANDIDATE` (unverified) |
| `cognicore_verify_experience` | Submits command execution evidence | Writes Memory | Evaluates via `VerificationGate`; promotes to `VERIFIED` on `exit_code == 0` |
| `cognicore_check_experience` | Validates experience validity against changed dependencies | Reads/Updates | Detects version breaks, returns `stale: true` and `revalidation_required` |
| `cognicore_share_experience` | Transfers verified experiences across agent instances | Cross-Agent | Enforces provenance and verified status before transfer |

### Strict Enforcement Invariants:
- **Unverified → Cannot Share**: Experiences in `candidate` status cannot be transferred across agents.
- **Verified → Can Share**: Only evidence-verified experiences with intact provenance transfer.
- **Stale → Cannot Blindly Share**: Dependency version mismatches require re-validation before reuse.
- **Superseded → Archival Only**: When a newer verified solution supersedes an older one, retrieval prioritizes the newer solution.

---

## Installation & Setup

### 1. Install CogniCore Environment
Ensure the published CogniCore package is installed with MCP and server extras:

```bash
pip install "cognicore-env[server,mcp]==0.10.3"
```

### 2. Plugin Configuration
The plugin is configured with automatic stdio MCP server spawning in `.mcp.json`:

```json
{
  "cognicore-experience": {
    "command": "python",
    "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/server.py"]
  }
}
```

## Core Workflows

### 1. Pre-Task Recall (`DO NOT REPEAT`)
Before attempting a non-trivial fix:
```python
cognicore_recall_experience(
    query="Fix ZeroDivisionError in calculate_ratio",
    include_failures=True,
    python_version="3.11.0",
    dependencies_json='{"math-lib": "1.0.0"}'
)
```

**Returned Guidance:**
- `failure_warnings`:
  - `FAILURE: Return a / (b + 1e-9)` — Reason: Alters numerical precision for valid inputs.
  - `FAILURE: Return float('inf') on zero` — Reason: Violates ValueError contract.
- `experiences`:
  - `VERIFIED: Explicit type check + raise ValueError('Denominator cannot be zero')`.

### 2. Task Recording & Verification Gate
When the task is complete and tests pass:

```python
# 1. Record Candidate
exp = cognicore_record_experience(
    task="Fix calculate_ratio divide-by-zero",
    problem="Unhandled divide-by-zero on b=0",
    solution="Add explicit guard and raise ValueError",
    why_it_worked="Enforces clean API contract",
    attempts_json='[{"approach": "1e-9 epsilon", "outcome": "failure", "reason": "Precision loss"}, {"approach": "ValueError guard", "outcome": "success", "reason": "Meets specification"}]',
    repository_id="acme/math_repo"
)

# 2. Verify with Evidence
cognicore_verify_experience(
    experience_id=exp["experience_id"],
    evidence_json='[{"command": "pytest tests/test_math_utils.py -q", "exit_code": 0}]'
)
```

### 3. Stale Environment Detection
When upgrading dependencies:
```python
cognicore_check_experience(
    experience_id="exp_123",
    python_version="3.11.0",
    dependencies_json='{"math-lib": "2.0.0"}'
)
```
**Outcome:**
`{"stale": true, "valid": false, "status": "revalidation_required", "staleness_reasons": ["Dependency major mismatch for math-lib: 1.0.0 vs 2.0.0"]}`.

---

## Proof-of-Concept Benchmark Results

> **Proof-of-concept result:** In the included three-session benchmark, the baseline required 3 attempts with 2 repeated failures, while verified experience retrieval required 1 attempt with 0 repeated failures. This is a single proof-of-concept scenario, not a general performance claim.

```text
Baseline (No Memory):
3 attempts
2 repeated failures

Verified experience:
1 attempt
0 repeated failures
```

---

## Running Tests

### Run Plugin Test Suite
```bash
python -m pytest external_plugins/cognicore-experience/tests/ -v
```
