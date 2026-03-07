# Review Loop Protocol

Quality assurance flow applied at all scales.

## 3 Principles

1. **Implementer != Reviewer**: The agent who wrote it doesn't review it
2. **Reviewer is read-only**: No code modifications. Point out issues only, return to implementer for fixes
3. **Loop limit 3 cycles**: After 3 cycles, arbitrator (Opus) intervenes to decide continue or abort

## Flow

```
implement -> review(edit:false) -> [issues found] -> fix -> review -> ... (max 3 times)
                                   [no issues]    -> supervise -> COMPLETE
```

## Context Rot Prevention

During fix phases, don't carry over previous session responses. Share information via review report files.

## TDD Separation Principle

Running test creation and implementation in the same context causes Context Pollution (the test creator's analysis leaks to the implementer).

For platoon+, **separate test creation and implementation to different agents**:
```
genba-neko A: Create tests -> handoff(action:auto) -> genba-neko B: Implement -> kurouto-neko: Review
```

## External Tool Integration for Judge

Before kurouto-neko's rubric judgment, feed these external tool results as structured input:
- Lint/type check results
- Test execution results (pass/fail/coverage)
- Security scan results (gitleaks, semgrep, etc.)

Eliminates gut-feeling "YOSHI" without tool evidence.

## Agent-as-a-Judge (Structured Review)

Reviewer (kurouto-neko/QA) uses the rubric defined in `agents/kurouto-neko.md`.
Eliminates subjective "YOSHI!" with 4-aspect structured judgment (correctness, safety, maintainability, testing).
When confidence is `low`, escalate to arbitrator (Opus).

## Self-Verification Methods

| Method | When to use |
|--------|-------------|
| Test execution | After code changes, run `npm test` / `pytest` etc. |
| Expected output | Provide "this input -> this output is correct" for self-checking |
| Screenshot verification | For UI changes, use browser tools for visual check |
| Lint/type check | `tsc --noEmit` / `ruff check` for static verification |

## JiTTests - Just-in-Time Disposable Tests

Disposable tests auto-generated from PR diffs. Used as review aid.

### When to use
- 3+ files changed AND existing tests don't cover the changes
- Reviewer judges "insufficient test coverage"

### Procedure
1. Identify changed functions/methods from `git diff`
2. Generate boundary/error case tests (disposable)
3. Run tests -> feed failures back to implementer
4. After review passes, disposable tests can be deleted (permanent tests are separate)
