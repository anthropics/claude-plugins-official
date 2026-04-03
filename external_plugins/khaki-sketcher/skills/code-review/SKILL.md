---
name: code-review
description: Deep code review with PASS/FAIL verdict via Codex reasoning. Use before merge for quality and regression checks.
---

# Code Review

Structured code review: Think (Codex deep review) → Verify (verdict).

## Usage

```
/ksk:code-review <files to review, or PR description>
```

## Phase 1: Think — Codex Deep Review

Build context, then call Codex for structured review:

```bash
codex exec "You are a senior code reviewer. Review with maximum depth.

## Context
<paste the diff, or describe files to review>

## Review Checklist
1. Logic correctness (off-by-one, null refs, race conditions)
2. Security (OWASP Top 10: injection, XSS, auth bypass)
3. Performance anti-patterns (N+1, unnecessary re-renders, memory leaks)
4. Code style and convention adherence
5. Test coverage relative to change surface
6. Regression risk: other code paths affected?

## Output Format (IMPORTANT)
1. Summary (verdict + issue count) — this is ALL Sonnet reads
   Verdict: PASS | FAIL_MINOR | FAIL_MAJOR | FAIL_CRITICAL
2. Detailed Review → save to .ksk/artifact/review-<ts>.md
3. Issues (sorted by severity)
4. Suggested fixes for each issue" --full-auto 2>/dev/null
```

Save result to `.ksk/artifact/review-<ts>.md`. Sonnet reads ONLY the summary.

### Fallback (Codex unavailable)

```bash
gemini -p "Review this code change. Focus on readability, maintainability, and potential issues.

## Context
<same context>

## Output Format (IMPORTANT)
1. Summary (verdict + issue count)
2. Details → save to .ksk/artifact/review-<ts>.md" -y --output-format text 2>/dev/null
```

## Phase 2: Verify — Act on Verdict

| Verdict | Action |
|--------|--------|
| PASS | Report clean review. Done. |
| FAIL_MINOR | Sonnet self-fixes if authorized. Re-review once. |
| FAIL_MAJOR | List issues with suggested fixes. Escalate to user. |
| FAIL_CRITICAL | Stop. Do NOT proceed with merge/commit. |

## Output Format

```
## Code Review Summary
**Verdict**: [PASS|FAIL_*]
**Issues found**: N
**Recommendation**: [merge-ready | fix-minor-then-merge | requires-rework | escalate]
**Artifact**: .ksk/artifact/review-<ts>.md
```

## Error Handling
- CLI returns empty or error → try fallback CLI
- Both CLIs unavailable → Sonnet reviews directly, note lack of external verification
- Rate limited → proceed without external review, inform user

Task: {{ARGUMENTS}}
