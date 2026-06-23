# Prodsec PR Review

Autonomous, security-focused PR review loop for Product Security teams. Monitors a Slack notifications channel, identifies PRs that need attention, and launches parallel review agents that post structured security reviews and submit GitHub approvals or change requests — without human interaction.

## Overview

This plugin combines the multi-angle review approach from the [code-review plugin](../code-review) with a full Product Security analysis layer, producing reviews that match the depth and patterns of experienced security reviewers.

**The loop is fully autonomous**: start it with `/loop 30m /pr:review` and it will continuously monitor for new PRs, review them, and post findings — no prompts, no confirmations.

## Commands

### `/pr:review`

Scans a Slack notifications channel for open GitHub PRs, determines which ones need your attention, and launches a parallel `pr-security-reviewer` agent for each qualifying PR.

**What it does:**
1. Loads a state file to skip PRs already being reviewed by a prior loop run
2. Reads the `prodsec-notifications` Slack channel (configurable) for PR URLs
3. Fetches metadata for each PR and applies three review criteria
4. Launches one background review agent per qualifying PR (all in parallel)

**Review criteria:**
- **Requested**: You appear in `reviewRequests` and haven't reviewed yet
- **Re-review**: You had a `CHANGES_REQUESTED` review and the author pushed new commits
- **Unblock**: PR has ≥1 approval, no blockers, and would benefit from another approval

**Usage:**
```bash
/pr:review                         # one-shot scan
/loop 30m /pr:review               # poll every 30 minutes (recommended)
/pr:review --force <PR_URL>        # review a specific PR regardless of criteria
/pr:review --channel my-channel    # use a different Slack channel
/pr:review --hours 24              # look back 24h instead of 48h
```

**Loop deduplication:**

The skill writes a state file at startup and each launched agent removes its entry when done. If the loop fires again before a review is complete, that PR is skipped. Entries older than 4 hours are auto-expired to handle crashed agents.

State file: `~/.claude/projects/.../pr-review-running.json`

Reset: `echo '{"running":[]}' > <state-file-path>`

---

## Agents

### `pr-security-reviewer`

Performs the actual PR review. Receives a PR URL, reason, and reviewer login from the `/pr:review` command.

**Review architecture (8 parallel agents):**

| Agent | Focus | Source |
|-------|-------|--------|
| 1 | CLAUDE.md compliance | code-review plugin pattern |
| 2 | Bug detection (changed lines only) | code-review plugin pattern |
| 3 | Git history and prior commit patterns | code-review plugin pattern |
| 4 | Prior PR review comments on same files | code-review plugin pattern |
| 5 | Code comment accuracy | code-review plugin pattern |
| 6 | Security analysis (see below) | Product Security layer |
| 7 | Dependency security | Product Security layer |
| 8 | Re-review: prior feedback coverage | triggered when reason=re-review |

**Security analysis coverage (Agent 6):**
- Authentication and authorization gates (middleware, RBAC, privilege escalation paths)
- Input handling (IDOR, SSRF, path traversal, XXE, command injection)
- Session and cookie security (`httpOnly`, `secure`, `sameSite`, session fixation)
- Secrets and cryptography (hardcoded creds, weak algorithms, IV reuse)
- Error handling and information disclosure (stack traces, SQL errors in responses)
- Audit trail completeness (security events reaching SIEM)
- Environment-conditional security bypasses (`isDev` / `NODE_ENV` gates)
- CORS and CSP policy weakening
- Mass assignment vulnerabilities (ORM field allowlisting)
- Timing attacks in auth comparison operations
- Feature flag security (per-request vs init-time checks)

**Confidence scoring:**

All findings from agents 1–7 are scored 0–100. Only findings with confidence ≥ 75 are included in the review comment. Agent 8 (re-review compliance) is always included regardless of score.

**Review outcome:**
- Any Blocker or High finding → `gh pr review --request-changes`
- Medium/Low/Advisory only, or no findings → `gh pr review --approve`

**Review comment format:**

Structured markdown with severity-bucketed findings, a per-area summary table, and SHA-anchored code links. Posted directly as the body of the GitHub formal review (not a separate comment), so it counts toward branch protection rules.

---

## Installation

```bash
/plugin install prodsec-pr-review
```

Requires:
- GitHub CLI (`gh`) authenticated
- Slack MCP server configured with access to your notifications channel
- `jq` installed (for state file management)

---

## Design Notes

### Why autonomous?

Automated PR review from a security reviewer slot removes the synchronous review bottleneck for routine PRs. The agent targets PRs where human review is needed (requested, re-review after fixes, near-merge unblock), not every PR.

### Why both code-review and security layers?

Code-review plugin pattern (CLAUDE.md, bugs, history, prior comments, comment accuracy) catches quality and consistency issues. The security layer catches patterns that require security domain knowledge. Combined, the review matches what a human security reviewer would produce.

### Why /loop 30m?

30-minute polling is a reasonable balance between responsiveness and resource use. For higher-cadence teams, `/loop 15m /pr:review` works. The state file ensures no duplicate reviews even if a loop iteration overlaps with a running review.

---

## Author

Product Security, ID.me

## Version

1.0.0
