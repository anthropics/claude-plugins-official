---
name: test
description: Test strategy, execution, coverage analysis, and regression detection.
---

# Test Strategy & Execution

Test writing and analysis: Build (write tests) → Verify (Codex for complex failures).

## Usage

```
/ksk:test <what to test or test task description>
```

## Step 1: Test Strategy

Identify the testing scope:
- What changed? (files, modules, APIs)
- Unit / Integration / E2E classification
- Boundary value analysis and equivalence partitioning

## Step 2: Build — Write Tests

- Check existing test patterns and framework
- Unit tests first, integration tests as needed
- Test names: "should X when Y"
- Cover happy path + edge cases + error paths

## Step 3: Execute

```bash
# Framework-appropriate runner
npm test / npx vitest / npx jest / pytest / go test ./...
```

## Step 4: Verify — Codex Failure Analysis (if needed)

For complex test failures, call Codex for root-cause analysis:

```bash
codex exec "Analyze this test failure with maximum depth.

## Context
<paste error output, test code, relevant source>

## Task
1. Determine: Is this a test bug or a production bug?
2. If test bug: what's wrong with the test?
3. If production bug: what's the root cause?
4. Suggested fix (minimal, targeted)

## Output Format (IMPORTANT)
1. Summary (2-3 sentences) — this is ALL Sonnet reads
2. Detailed Analysis → save to .ksk/artifact/test-analysis-<ts>.md" --full-auto 2>/dev/null
```

Save result to `.ksk/artifact/test-analysis-<ts>.md`. Sonnet reads ONLY the summary.

### Fallback (Codex unavailable)

```bash
gemini -p "Analyze this test failure. Is it a test bug or production bug?

## Context
<same context>

## Output Format (IMPORTANT)
1. Summary (2-3 sentences)
2. Details → save to .ksk/artifact/test-analysis-<ts>.md" -y --output-format text 2>/dev/null
```

## Step 5: Coverage Gaps

- Check coverage report
- Identify missed boundary values or error paths
- Write additional tests for gaps

## Output

```
## Test Results
- Tests written: N
- Tests passing: N
- Tests failing: N
- Coverage: N%
- Gaps identified: [list]
- Artifacts: .ksk/artifact/test-*.md
```

## Error Handling
- CLI returns empty or error → try fallback CLI
- Both CLIs unavailable → Sonnet analyzes failure directly
- Rate limited → proceed without external analysis

Task: {{ARGUMENTS}}
