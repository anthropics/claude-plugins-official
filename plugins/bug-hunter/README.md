# Bug Hunter Plugin

Multi-agent bug hunting for Claude Code. Launches parallel specialist agents across 8 bug categories, deduplicates and scores findings, runs a regression guard, and produces a prioritized report.

## Usage

```
/bug-hunter:bughunt                     # Diff-based scan, top 5 agents
/bug-hunter:bughunt --full              # Full codebase, top 5 agents
/bug-hunter:bughunt --thorough          # All 8 agents, diff-based
/bug-hunter:bughunt --security          # Deep security audit only
/bug-hunter:bughunt src/auth/           # Specific path
/bug-hunter:bughunt --thorough --full   # All agents, full codebase
```

## Pipeline

1. **Recon** — Detect language/framework, determine file scope, select agents
2. **Parallel Hunt** — Launch specialist agents simultaneously via Task tool
3. **Cross-Cutting** — Deduplicate, score (priority 1-5), detect bug chains
4. **Regression Guard** — Assess fix risk: SAFE / CAUTION / BREAKING
5. **Report** — Prioritized findings, regression summary, recommended fix order

## Agents

| Agent | Hunts For |
|---|---|
| `logic-hunter` | Off-by-ones, wrong comparisons, inverted conditions, unreachable code |
| `error-handler` | Silent failures, swallowed exceptions, empty catches, fallback masking |
| `edge-case-finder` | Null paths, empty collections, boundary values, overflow, Unicode |
| `security-scanner` | Injection, auth bypass, path traversal, SSRF, hardcoded secrets |
| `race-condition-detector` | Shared mutable state, TOCTOU, deadlocks, async pitfalls |
| `resource-leak-hunter` | Unclosed files/connections, missing cleanup, thread leaks |
| `api-contract-checker` | Type mismatches, wrong arg order, schema drift, return value misuse |
| `state-bug-finder` | Stale state, missing UI updates, cache invalidation, state machine bugs |
| `regression-guard` | Test coverage gaps, downstream consumers, public API breaks, fix risk |

## Agent Selection (default mode)

**Always run**: logic-hunter, error-handler, edge-case-finder

**Conditional** (based on files changed): security-scanner, race-condition-detector, resource-leak-hunter, api-contract-checker, state-bug-finder — top 2 by file-match count are selected (5 total cap).

Use `--thorough` to run all 8 hunters regardless.

## Finding Format

All agents produce findings in a standardized format:
- File path and line number
- Severity: CRITICAL / HIGH / MEDIUM / LOW
- Confidence: 0-100 (threshold >= 75)
- Category, title, description, evidence, suggested fix
- Regression risk and notes

## Priority Scoring

| Priority | Criteria |
|---|---|
| 1 | CRITICAL severity + confidence >= 90 |
| 2 | CRITICAL 75-89, or HIGH >= 90 |
| 3 | HIGH 75-89, or MEDIUM >= 90 |
| 4 | MEDIUM 75-89 |
| 5 | LOW (any confidence) |

## Regression Guard

Runs after findings are collected (Phase 3). For each finding:
- Checks test coverage (COVERED / PARTIAL / UNCOVERED)
- Analyzes downstream consumers
- Checks public API surface impact
- Classifies fix as **SAFE** / **CAUTION** / **BREAKING**
- Suggests test cases before and after fix
