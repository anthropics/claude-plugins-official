---
name: complex-debug
description: Complex debugging with Codex root-cause analysis and iterative review loop. Use for crashes, race conditions, intermittent failures.
---

# Complex Debug

Systematic debugging: Think (Codex RCA) → Build (fix) → Verify (regression review).

## Usage

```
/ksk:complex-debug <bug description, error message, or symptoms>
```

## Phase 1: Think — Codex Root Cause Analysis

Gather context (error logs, stack traces, relevant source files), then call Codex:

```bash
codex exec "Analyze this bug with maximum depth. Apply 5-Whys methodology.

## Context
<paste relevant error logs, stack traces, file paths>

## Task
1. Generate competing hypotheses
2. Identify evidence for/against each
3. Determine the single root cause
4. Propose a minimal fix (touch ONLY what is necessary)
5. Assess: are there other code paths with the same vulnerability?

## Output Format (IMPORTANT)
1. Summary (2-3 sentences) — this is ALL Sonnet reads
2. Detailed Analysis → save to .ksk/artifact/debug-<ts>.md
3. Fix Strategy (numbered steps)
4. Risk Assessment (what could break if we fix it)" --full-auto 2>/dev/null
```

Save result to `.ksk/artifact/debug-<ts>.md`. Sonnet reads ONLY the summary.

### Fallback (Codex unavailable)

```bash
gemini -p "Analyze this bug comprehensively. Consider logic errors, edge cases, and UX impact.

## Context
<same context>

## Output Format (IMPORTANT)
1. Summary (2-3 sentences) — this is ALL Sonnet reads
2. Details → save to .ksk/artifact/debug-<ts>.md" -y --output-format text 2>/dev/null
```

## Phase 2: Build — Sonnet Fix

Based on the Think summary:
- Read artifact file for detailed analysis if needed
- Touch ONLY what is necessary — no refactoring adjacent code
- Match existing code style
- Write a reproduction test for the original bug

## Phase 3: Verify — Codex Regression Review (max 3 rounds)

```bash
codex exec "Review this fix for regression risk.
1. Does the fix address the root cause (not just the symptom)?
2. Are there other code paths with the same vulnerability?
3. Does the fix introduce new edge cases?
4. Is the reproduction test adequate?

## Output Format (IMPORTANT)
1. Summary (verdict only) — PASS | FAIL_MINOR | FAIL_MAJOR | FAIL_CRITICAL
2. Details → save to .ksk/artifact/debug-review-<ts>.md

<paste ONLY the diff and relevant source>" --full-auto 2>/dev/null
```

Save to `.ksk/artifact/`. Read verdict only.

| Verdict | Action |
|--------|--------|
| PASS | Complete. Report results. |
| FAIL_MINOR | Sonnet self-fixes. Back to Phase 2 (max 3 total loops) |
| FAIL_MAJOR | Return to Phase 1 with new information |
| FAIL_CRITICAL | Stop. Escalate to user. |

## Error Handling
- CLI returns empty or error → try fallback CLI
- Both CLIs unavailable → Sonnet analyzes and fixes directly, note lack of external verification
- Rate limited → proceed without external model, inform user

## Verify Isolation
- Verify 프롬프트에 Phase 1의 분석 결과나 제안을 포함하지 마세요
- 오직 diff와 관련 소스 코드만 제공하세요
- 편향 없는 독립 리뷰여야 합니다

Task: {{ARGUMENTS}}
