---
name: code-reviewer
description: >
  Code review automation for TypeScript, JavaScript, Python, Go, Swift, Kotlin.
  Analyzes PRs for complexity and risk, checks code quality for SOLID violations
  and code smells, generates review reports. Use when reviewing pull requests,
  analyzing code quality, identifying issues, generating review checklists.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: engineering
  domain: code-quality
  updated: 2026-03-31
  tags: [code-review, pull-request, code-quality, best-practices]
---
# Code Reviewer

Automated code review tools for analyzing pull requests, detecting code quality issues, and generating review reports.

---

## Table of Contents

- [Tools](#tools)
  - [PR Analyzer](#pr-analyzer)
  - [Code Quality Checker](#code-quality-checker)
  - [Review Report Generator](#review-report-generator)
- [Reference Guides](#reference-guides)
- [Languages Supported](#languages-supported)

---

## Tools

### PR Analyzer

Analyzes git diff between branches to assess review complexity and identify risks.

```bash
# Analyze current branch against main
python scripts/pr_analyzer.py /path/to/repo

# Compare specific branches
python scripts/pr_analyzer.py . --base main --head feature-branch

# JSON output for integration
python scripts/pr_analyzer.py /path/to/repo --json
```

**What it detects:**
- Hardcoded secrets (passwords, API keys, tokens)
- SQL injection patterns (string concatenation in queries)
- Debug statements (debugger, console.log)
- ESLint rule disabling
- TypeScript `any` types
- TODO/FIXME comments

**Output includes:**
- Complexity score (1-10)
- Risk categorization (critical, high, medium, low)
- File prioritization for review order
- Commit message validation

---

### Code Quality Checker

Analyzes source code for structural issues, code smells, and SOLID violations.

```bash
# Analyze a directory
python scripts/code_quality_checker.py /path/to/code

# Analyze specific language
python scripts/code_quality_checker.py . --language python

# JSON output
python scripts/code_quality_checker.py /path/to/code --json
```

**What it detects:**
- Long functions (>50 lines)
- Large files (>500 lines)
- God classes (>20 methods)
- Deep nesting (>4 levels)
- Too many parameters (>5)
- High cyclomatic complexity
- Missing error handling
- Unused imports
- Magic numbers

**Thresholds:**

| Issue | Threshold |
|-------|-----------|
| Long function | >50 lines |
| Large file | >500 lines |
| God class | >20 methods |
| Too many params | >5 |
| Deep nesting | >4 levels |
| High complexity | >10 branches |

---

### Review Report Generator

Combines PR analysis and code quality findings into structured review reports.

```bash
# Generate report for current repo
python scripts/review_report_generator.py /path/to/repo

# Markdown output
python scripts/review_report_generator.py . --format markdown --output review.md

# Use pre-computed analyses
python scripts/review_report_generator.py . \
  --pr-analysis pr_results.json \
  --quality-analysis quality_results.json
```

**Report includes:**
- Review verdict (approve, request changes, block)
- Score (0-100)
- Prioritized action items
- Issue summary by severity
- Suggested review order

**Verdicts:**

| Score | Verdict |
|-------|---------|
| 90+ with no high issues | Approve |
| 75+ with ≤2 high issues | Approve with suggestions |
| 50-74 | Request changes |
| <50 or critical issues | Block |

---

## Reference Guides

### Code Review Checklist
`references/code_review_checklist.md`

Systematic checklists covering:
- Pre-review checks (build, tests, PR hygiene)
- Correctness (logic, data handling, error handling)
- Security (input validation, injection prevention)
- Performance (efficiency, caching, scalability)
- Maintainability (code quality, naming, structure)
- Testing (coverage, quality, mocking)
- Language-specific checks

### Coding Standards
`references/coding_standards.md`

Language-specific standards for:
- TypeScript (type annotations, null safety, async/await)
- JavaScript (declarations, patterns, modules)
- Python (type hints, exceptions, class design)
- Go (error handling, structs, concurrency)
- Swift (optionals, protocols, errors)
- Kotlin (null safety, data classes, coroutines)

### Common Antipatterns
`references/common_antipatterns.md`

Antipattern catalog with examples and fixes:
- Structural (god class, long method, deep nesting)
- Logic (boolean blindness, stringly typed code)
- Security (SQL injection, hardcoded credentials)
- Performance (N+1 queries, unbounded collections)
- Testing (duplication, testing implementation)
- Async (floating promises, callback hell)

---

## Languages Supported

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| TypeScript | `.ts`, `.tsx` |
| JavaScript | `.js`, `.jsx`, `.mjs` |
| Go | `.go` |
| Swift | `.swift` |
| Kotlin | `.kt`, `.kts` |

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Error: /path is not a git repository` | PR Analyzer requires a `.git` directory at the target path | Run from inside a git repo or pass the correct repo root path |
| No changes detected between branches | The `--base` and `--head` refs are identical, or the branch has no diverging commits | Verify branch names with `git branch -a`; use explicit `--base` and `--head` flags |
| Script times out on large repositories | `git diff` or file analysis exceeds the 30-second (PR Analyzer) or 300-second (Quality Checker) subprocess timeout | Narrow the scope with `--language` filter or analyze a subdirectory instead of the repo root |
| Unsupported file type error | Code Quality Checker only processes `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.go`, `.swift`, `.kt`, `.kts` | Use the `--language` flag to target a supported language, or add extensions to `LANGUAGE_EXTENSIONS` in the script |
| False-positive hardcoded secrets | Regex pattern matches test fixtures, example strings, or documentation | Review flagged lines manually; the pattern `(password\|secret\|api_key\|token)\s*[=:]\s*['"][^'"]+['"]` intentionally casts a wide net to avoid misses |
| Review Report shows score of 0 | Multiple critical and high findings compound deductions past the floor | Address critical findings first; each critical risk deducts 15 points and each high risk deducts 10 |
| Commit message issues flagged incorrectly | PR Analyzer enforces conventional commit format (`feat:`, `fix:`, etc.) | Adopt conventional commits or ignore the `commit_issues` section if your team uses a different convention |

---

## Success Criteria

- **Review turnaround under 4 hours:** Automated pre-screening with PR Analyzer reduces manual triage time so reviewers focus on logic, not hygiene.
- **Zero false-positive critical findings:** Every critical-severity flag (hardcoded secrets, SQL injection) corresponds to a genuine risk requiring human verification.
- **Code quality score above 80 on all merged PRs:** Teams gate merges on the Quality Checker score, ensuring consistent baseline quality.
- **100% of PRs reviewed with a structured report:** Every pull request gets a Review Report with verdict, score, and prioritized action items before merge.
- **Commit message compliance above 95%:** PR Analyzer commit validation drives adoption of conventional commit format across the team.
- **Reduction in post-merge defects by 30%+:** Systematic detection of code smells, SOLID violations, and risky patterns catches issues before they reach production.
- **Review order adoption by reviewers:** At least 80% of reviewers follow the suggested file priority order, ensuring security-sensitive files are inspected first.

---

## Scope & Limitations

**Covers:**
- Static pattern-based risk detection in git diffs (secrets, SQL injection, debug statements, lint bypasses)
- Structural code quality analysis: function length, class size, cyclomatic complexity, parameter count, SOLID violations
- PR metadata assessment: file categorization by risk priority, commit message validation, complexity scoring
- Consolidated review reports with verdicts, scores, and prioritized action items across text, markdown, and JSON formats

**Does NOT cover:**
- **Runtime or dynamic analysis** -- use `senior-qa` for test execution and `qa-browser-automation` for end-to-end testing
- **Security vulnerability scanning** (CVE databases, dependency audits) -- use `senior-security` or `senior-secops` for SAST/DAST and supply chain analysis
- **Performance profiling or benchmarking** -- use `senior-backend` or `senior-fullstack` for performance optimization workflows
- **Architecture-level review** (system design, service boundaries, API contract validation) -- use `senior-architect` for architectural decision records and design review

---

## Integration Points

| Skill | Integration | Data Flow |
|-------|-------------|-----------|
| `senior-security` | Feed PR Analyzer critical findings into security review workflows for deeper SAST/DAST analysis | `pr_analyzer.py --json` output `risks.critical[]` → security assessment input |
| `senior-qa` | Gate test execution on review report verdict; block test suites when verdict is `block` | `review_report_generator.py --json` output `summary.verdict` → QA pipeline gate |
| `senior-architect` | Escalate high-complexity PRs (score 7+) to architecture review | `pr_analyzer.py` output `summary.complexity_score` → architecture review trigger |
| `senior-fullstack` | Combine code quality scores with fullstack quality analyzer for end-to-end project health | `code_quality_checker.py --json` output → merged with `code_quality_analyzer.py` metrics |
| `tdd-guide` | Cross-reference review findings with test coverage; flag untested code paths flagged by quality checker | Quality checker `smells[]` by file → TDD coverage gap analysis |
| `senior-devops` | Integrate review reports into CI/CD pipelines as automated quality gates | `review_report_generator.py --json` output `summary.score` → pipeline pass/fail threshold |

---

## Tool Reference

### pr_analyzer.py

**Purpose:** Analyzes git diffs between branches to assess pull request complexity, detect risky patterns, prioritize files for review, and validate commit messages.

**Usage:**

```bash
python scripts/pr_analyzer.py [repo_path] [--base BASE] [--head HEAD] [--json] [--output FILE]
```

**Flags:**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `repo_path` | *(positional)* | `.` | Path to git repository |
| `--base` | `-b` | `main` | Base branch for comparison |
| `--head` | `-h` | `HEAD` | Head branch or commit for comparison |
| `--json` | | off | Output in JSON format |
| `--output` | `-o` | *(stdout)* | Write output to file |

**Example:**

```bash
python scripts/pr_analyzer.py /path/to/repo --base main --head feature-branch --json
```

```json
{
  "status": "analyzed",
  "summary": {
    "files_changed": 8,
    "total_additions": 142,
    "total_deletions": 37,
    "complexity_score": 4,
    "complexity_label": "Moderate",
    "commits": 3
  },
  "risks": {
    "critical": [],
    "high": [],
    "medium": [
      {"name": "console_log", "severity": "medium", "message": "Console statement found (remove for production)", "file": "src/api/handler.js", "count": 2}
    ],
    "low": []
  },
  "files": [ ... ],
  "commit_issues": [],
  "review_order": ["src/auth/middleware.ts", "src/api/handler.js", "..."]
}
```

**Output Formats:** Human-readable text report (default) or structured JSON (`--json`).

---

### code_quality_checker.py

**Purpose:** Analyzes source files or directories for structural code quality issues, code smells (long functions, god classes, deep nesting, magic numbers, commented code), SOLID principle violations, and cyclomatic complexity.

**Usage:**

```bash
python scripts/code_quality_checker.py <path> [--recursive] [--language LANG] [--json] [--output FILE]
```

**Flags:**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `path` | *(positional, required)* | | File or directory to analyze |
| `--recursive` | `-r` | `true` | Recursively analyze directories |
| `--language` | `-l` | *(all supported)* | Filter by language: `python`, `typescript`, `javascript`, `go`, `swift`, `kotlin` |
| `--json` | | off | Output in JSON format |
| `--output` | `-o` | *(stdout)* | Write output to file |

**Example:**

```bash
python scripts/code_quality_checker.py ./src --language typescript --json
```

```json
{
  "directory": "/absolute/path/to/src",
  "files_analyzed": 12,
  "average_score": 82.5,
  "overall_grade": "B",
  "total_code_smells": 7,
  "total_solid_violations": 1,
  "files": [
    {
      "file": "src/service.ts",
      "language": "typescript",
      "metrics": {
        "lines": {"total": 320, "code": 260, "blank": 40, "comment": 20},
        "functions": 14,
        "classes": 2,
        "avg_complexity": 5.3
      },
      "quality_score": 78,
      "grade": "C",
      "smells": [
        {"type": "long_function", "severity": "medium", "message": "Function 'processOrder' has 68 lines (max: 50)", "location": "processOrder"}
      ],
      "solid_violations": [],
      "function_details": [ ... ],
      "class_details": [ ... ]
    }
  ]
}
```

**Output Formats:** Human-readable text report (default) or structured JSON (`--json`). Files are sorted by quality score ascending (worst first).

---

### review_report_generator.py

**Purpose:** Generates comprehensive code review reports by combining PR analysis and code quality findings into a single structured report with verdict, score, prioritized action items, and suggested review order. Can run both sub-tools automatically or accept pre-computed JSON inputs.

**Usage:**

```bash
python scripts/review_report_generator.py [repo_path] [--pr-analysis FILE] [--quality-analysis FILE] [--format FORMAT] [--json] [--output FILE]
```

**Flags:**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `repo_path` | *(positional)* | `.` | Path to repository |
| `--pr-analysis` | | *(auto-run)* | Path to pre-computed PR analysis JSON file |
| `--quality-analysis` | | *(auto-run)* | Path to pre-computed code quality analysis JSON file |
| `--format` | `-f` | `text` | Output format: `text`, `markdown`, `json` |
| `--json` | | off | Output as JSON (shortcut for `--format json`) |
| `--output` | `-o` | *(stdout)* | Write output to file |

**Example:**

```bash
python scripts/review_report_generator.py . --format markdown --output review.md
```

```
# Code Review Report

**Generated:** 2026-03-21T14:30:00
**Repository:** /path/to/repo

## Executive Summary

**Verdict:** ✅ APPROVE WITH SUGGESTIONS
**Score:** 82/100
**Rationale:** Minor improvements recommended

### Issue Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 3     |
| Low      | 2     |

## Action Items

1. 🟠 **[P1]** Break down function into smaller, focused units
2. 🟡 **[P2]** Remove or replace console statements with proper logging
...
```

**Output Formats:** Plain text (default), markdown (`--format markdown`), or structured JSON (`--format json` or `--json`). When `--pr-analysis` and `--quality-analysis` are omitted, the tool automatically invokes `pr_analyzer.py` and `code_quality_checker.py` as subprocesses.
