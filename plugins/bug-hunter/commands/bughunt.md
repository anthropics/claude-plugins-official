---
description: "Comprehensive multi-agent bug hunting with parallel specialist agents, deduplication, regression guard, and prioritized reporting"
argument-hint: "[--full] [--thorough] [--security] [path]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Bug Hunt Orchestrator

Run a comprehensive, multi-agent bug hunt on the codebase. Each specialist agent targets a different bug category. Results are deduplicated, scored, regression-checked, and reported.

**Arguments:** "$ARGUMENTS"

## Phase 0: Recon

### Parse Arguments

Parse "$ARGUMENTS" to determine:

- **`--full`**: Scan entire codebase (not just changed files)
- **`--thorough`**: Launch ALL 8 hunter agents (not just top 5)
- **`--security`**: Security-scanner only (deep security audit)
- **Path argument** (e.g., `src/auth/`): Limit scope to this directory
- Flags are combinable: `--thorough --full` means all agents on all files

If no arguments, default to **diff-based mode**: recently changed files, top 5 most relevant agents.

### Detect Language & Framework

Inspect the project root to detect the stack:

1. Use Glob to check for: `package.json`, `tsconfig.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `requirements.txt`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `.csproj`
2. Note the primary language and framework — this informs agent selection

### Determine File Scope

- **Diff mode (default)**: Run `git diff --name-only HEAD~5` and `git diff --name-only --cached` to get recently changed files. Also run `git diff --name-only` for unstaged changes. Combine and deduplicate.
- **`--full` mode**: Use Glob patterns to find all source files (exclude node_modules, vendor, build, dist, .git, etc.)
- **Path mode**: Limit to files under the specified path
- Create a deduplicated file list for agents to analyze

### Select Agents

**Always-run agents** (core 3): `logic-hunter`, `error-handler`, `edge-case-finder`

**Conditional agents** (selected based on what files are in scope):

| Agent | Trigger: file patterns in scope |
|---|---|
| `security-scanner` | Files matching: auth, login, session, token, crypto, password, secret, api, route, middleware, permission, sanitize, cors, csrf, cookie |
| `race-condition-detector` | Files matching: async, thread, worker, mutex, lock, channel, concurrent, parallel, queue, pool, transaction, atomic |
| `resource-leak-hunter` | Files matching: connection, pool, client, stream, socket, file, handle, cursor, session, cache, db, database, http |
| `api-contract-checker` | Files matching: api, route, endpoint, handler, controller, schema, type, interface, proto, graphql, grpc, openapi, swagger |
| `state-bug-finder` | Files matching: state, store, redux, context, cache, component, view, model, controller, hook, reducer, atom, signal, reactive |

**Selection logic**:
1. If `--thorough`: use all 8 hunters
2. If `--security`: use only `security-scanner`
3. Otherwise: use the core 3 + up to 2 conditional agents with the highest file-match count (cap at 5 total)

Announce to the user which agents were selected and why.

## Phase 1: Parallel Hunt

Launch the selected hunter agents **in parallel** using the Task tool. Send ALL Task calls in a single response to maximize parallelism.

For each agent, construct a prompt like:

```
You are the [agent-name] agent. Analyze the following files for [agent's specialty]:

Files to analyze:
[file list]

Language/Framework: [detected stack]

Read each file thoroughly and report findings in the standardized format. Only report findings with confidence >= 75.
```

Important:
- Use `subagent_type` matching the agent name from the agents/ directory (e.g., `bug-hunter:logic-hunter`)
- Set `model: "opus"` for all agents
- Launch all agents in ONE response for true parallelism
- Each agent runs independently with Glob, Grep, Read, and Bash tools

Wait for all agents to complete and collect their findings.

## Phase 2: Cross-Cutting Analysis

After collecting all agent results, perform deduplication and scoring:

### Deduplication
- If multiple agents flag the SAME file:line, merge into a single finding noting which agents flagged it (higher confidence)
- If agents flag the same function but different issues, keep as separate findings

### Scoring
Calculate priority 1-5 for each finding:

| Priority | Severity + Confidence | Description |
|---|---|---|
| 1 | CRITICAL + confidence >= 90 | Stop everything and fix this |
| 2 | CRITICAL + confidence 75-89, or HIGH + confidence >= 90 | Fix before next release |
| 3 | HIGH + confidence 75-89, or MEDIUM + confidence >= 90 | Should fix soon |
| 4 | MEDIUM + confidence 75-89 | Fix when convenient |
| 5 | LOW (any confidence) | Nice to fix |

### Bug Chain Detection
Look for causally related findings:
- Finding A's buggy output feeds into Finding B's input
- Finding A and B are in the same error handling chain
- Multiple findings in the same function suggest deeper structural issues

Group these as "bug chains" in the report.

### Confidence Filter
Remove any findings that slipped through with confidence < 75.

## Phase 3: Regression Guard

If there are any findings with priority 1-3, launch the `regression-guard` agent (single Task call) with ALL findings as context.

Prompt:
```
You are the regression-guard agent. Analyze the following bug findings and assess the regression risk of fixing each one.

[Include all findings from Phase 2 in full]

For each finding, check:
1. Test coverage of the affected function
2. Downstream consumers (callers)
3. Public API surface impact
4. Classify fix as SAFE / CAUTION / BREAKING
5. Suggest test cases before and after fix
```

Use `subagent_type: "bug-hunter:regression-guard"` and `model: "opus"`.

If all findings are priority 4-5 only, skip the regression guard and note this in the report.

## Phase 4: Final Report

Produce the final report in this exact structure:

```markdown
# Bug Hunt Report

## Executive Summary
- **Scope**: [diff/full/path] mode, [N] files analyzed
- **Agents deployed**: [list of agents used]
- **Findings**: [N] total — [P1] critical, [P2] urgent, [P3] should-fix, [P4-5] suggestions
- **Regression risk**: [N] SAFE, [N] CAUTION, [N] BREAKING

---

## Priority 1: Critical Issues
[Full finding detail including regression guard analysis for each]

## Priority 2: Urgent Issues
[Full finding detail including regression guard analysis for each]

## Priority 3: Should Fix
[Full finding detail including regression guard analysis for each]

## Priority 4-5: Suggestions
[Compact list: one line per finding with file:line, title, category]

---

## Bug Chains
[Groups of causally related findings, if any]

## Regression Risk Summary
[From regression-guard: SAFE/CAUTION/BREAKING breakdown]
[Recommended fix order]

## Files Most Affected
| File | Finding Count | Highest Priority |
|---|---|---|
[Table of files sorted by finding count]

## Recommended Fix Order
1. [SAFE fixes first, by priority]
2. [CAUTION fixes, with notes to verify callers]
3. [BREAKING fixes last, with migration notes]
```

## Scope Quick Reference

| Invocation | Behavior |
|---|---|
| `/bug-hunter:bughunt` | Diff-based: recently changed files, top 5 agents |
| `/bug-hunter:bughunt --full` | Full codebase, top 5 agents |
| `/bug-hunter:bughunt --thorough` | All 8 hunter agents, diff-based |
| `/bug-hunter:bughunt --security` | Security-scanner only (deep), diff-based |
| `/bug-hunter:bughunt src/auth/` | Specific path, top 5 agents |
| `/bug-hunter:bughunt --thorough --full` | All agents, full codebase |

## Important Notes

- Always use `model: "opus"` for all agent Task calls
- Always launch agents in parallel (multiple Task calls in ONE response)
- The regression-guard runs AFTER the hunters, not in parallel with them
- If the file scope is very large (>100 files), split into batches per agent to keep context manageable
- Announce progress to the user at each phase transition
