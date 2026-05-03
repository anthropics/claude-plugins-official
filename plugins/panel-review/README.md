# Panel Review

A 2-pass code review skill that classifies risk tier and runs structured reviews with exact file:line findings and named test signatures.

## What it does

Replaces the noisy multi-panel review pattern with two focused passes:

| Pass | Model | When |
|------|-------|------|
| **Defense** — correctness + tests + security | Sonnet | Every non-trivial change |
| **Adversary** — attack orientation | Opus | T1 only (auth, RLS, MCP schemas) |

## Tier classification

| Tier | Triggers | Passes |
|------|----------|--------|
| T1 | Auth, RLS, permissions, MCP tool schemas, major rewrites | Defense + Adversary |
| T2 | DB writes, external integrations, access-gating | Defense + §7 Performance |
| T3 | Logic/behavior change, no security surface | Defense only |
| T4 | Typo, comment, log wording | Skip |

## Usage

```
/panel-review
panel review this diff
run panels
```

Invoke after writing or editing security-critical code — the skill also triggers proactively before commits.

## Output format

**Defense pass:**
```
FIX [N]: <file>:<line>
Change: <exact description>
Test: test_regression_<name> — asserts <what>
```

**Adversary pass:**
```
EXPLOIT [N]: <file>:<line>
Attack: <how to exploit>
Fix: <correct defense>
Test: test_exploit_<name> — asserts <what blocks the attack>
```

Results are grouped as **CRITICAL** (fix before commit) and **STANDARD**.

## Defense pass checks

1. Execution path — traces entry point → I/O, flags dead safety code
2. Wiring gaps — unit tests on a function ≠ wiring verified at the route
3. Locked contracts — every spec requirement has an exact implementing line
4. Sibling instances — guards added here but missing on equivalent routes
5. Tests — HTTP boundary, mock discipline, pipeline coverage, behavior vs labels
6. Security — guard completeness, format injection, info disclosure, exception handling, input bounds
7. Performance *(T1/T2)* — N+1 queries, pool pressure, unbounded queries, transaction scope

## Adversary pass checks

1. Rationalizations — "safe because X": is X actually sufficient?
2. The sibling that wasn't fixed
3. Malicious input — full data flow end-to-end
4. Regression introduction — does the fix expose a sibling route?
5. Enumeration oracles — timing/response shape leaks
6. New format/variant audit — regex and match statements updated?
7. Wrong mechanism class — is this the right solution class?

## Source

[github.com/ragsvasan/panel-review](https://github.com/ragsvasan/panel-review)
