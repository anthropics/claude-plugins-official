---
name: Structured Experience Memory
description: Use this skill whenever tackling non-trivial coding tasks, debugging bugs, fixing test failures, refactoring components, or recording verified task outcomes. Provides structured validated experience retrieval (including DO NOT REPEAT failure warnings), candidate experience recording, evidence-backed VerificationGate promotion, environment compatibility checking, and cross-agent experience transfer.
version: 1.0.0
---

# CogniCore Structured Validated Experience Memory

CogniCore provides a verified, structured memory layer that persists across Claude Code sessions. It captures what problems occurred, what approaches failed (and why), what approach succeeded, and verifiable execution evidence (test commands and exit codes).

## Architecture & Workflow

```text
Claude Code Session
       │
       ▼
1. cognicore_recall_experience(query)
       │
       ├──► Inspect failure_warnings (DO NOT REPEAT)
       └──► Inspect experiences (VERIFIED solutions)
       │
       ▼
2. Execute Coding Task (try approaches, run tests)
       │
       ▼
3. cognicore_record_experience(task, problem, solution, attempts_json, why_it_worked)
       │  (Recorded as CANDIDATE)
       ▼
4. cognicore_verify_experience(experience_id, evidence_json)
       │
       ├──► Exit Code == 0 with evidence ──► Promoted to VERIFIED
       └──► Exit Code != 0 or no evidence ──► Remains CANDIDATE / REJECTED
```

## The 5 MCP Tools

### 1. `cognicore_recall_experience`
Call this **BEFORE** attempting a non-trivial problem or fix.

**Parameters:**
- `query`: Description of the bug, feature, or error message (e.g. `"Fix ZeroDivisionError in math_utils.py calculate_ratio"`).
- `include_failures`: `true` (default) to receive explicit `DO NOT REPEAT` warnings from previous failed attempts.
- `require_verified`: `false` to see all relevant experiences or `true` for only verified ones.
- `python_version` / `framework` / `dependencies_json`: Current runtime environment for compatibility matching.

**How to act on recall results:**
- If `failure_warnings` are present: **DO NOT REPEAT** those specific approaches.
- If `experiences` with status `verified` are present: Use the proven solution pattern as strong guidance.

### 2. `cognicore_record_experience`
Call this **AFTER** completing a coding task where you explored approaches or solved a non-trivial bug.

**Parameters:**
- `task`: High-level goal (e.g. `"Fix division by zero bug"`).
- `problem`: Specific failure mode or error symptom.
- `solution`: Concise description of the working fix.
- `why_it_worked`: Root cause explanation.
- `attempts_json`: JSON array documenting all attempts made during the session:
  ```json
  [
    {"approach": "Multiply denominator by 1.0", "outcome": "failure", "reason": "Still divides by 0 on zero input"},
    {"approach": "Wrap caller in try/except", "outcome": "failure", "reason": "Violates function API contract"},
    {"approach": "Add guard clause for zero denominator", "outcome": "success", "reason": "Safely handles boundary condition"}
  ]
  ```
- `repository_id`: Repository identifier.
- `commit`: Git commit hash.
- `python_version` / `dependencies_json`: Environment metadata.

### 3. `cognicore_verify_experience`
Call this to promote a candidate experience to `VERIFIED`.

> [!CRITICAL]
> Experiences are **NEVER** verified simply because of a text claim. Verification requires actual command execution evidence with `exit_code == 0`.

**Parameters:**
- `experience_id`: The ID returned by `cognicore_record_experience`.
- `evidence_json`: JSON array of execution evidence:
  ```json
  [
    {
      "command": "pytest tests/test_math.py -q",
      "exit_code": 0,
      "stdout_hash": "c0ffee1234",
      "commit": "abc1234"
    }
  ]
  ```

### 4. `cognicore_check_experience`
Call this when working with past experiences in an upgraded environment or when dependencies have changed.

**Parameters:**
- `experience_id`: The experience ID.
- `python_version` / `framework` / `dependencies_json`: The new environment details.

**Outcome:**
If dependencies or versions have breaking changes (e.g., `lib v1.0.0` vs `lib v2.0.0`), CogniCore returns `stale: true` and `status: "revalidation_required"`. Revalidate with fresh tests before relying on it as truth.

### 5. `cognicore_share_experience`
Call this to securely transfer verified experiences and failure warnings to another agent or workspace. Only verified experiences with intact provenance are transferred.

## Best Practices
1. **Never dump full conversation logs**: Only record concise problem statements, structured attempts, root causes, and verification proof.
2. **Never hide failures**: Failed attempts are first-class memory records that prevent future sessions from wasting time on dead ends.
3. **Always verify with test evidence**: Always run the relevant test command and supply its exit code to the verification gate.
