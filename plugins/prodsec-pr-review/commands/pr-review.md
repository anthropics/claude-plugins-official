---
description: "Scan a Slack channel for PRs needing your attention, skip already-running reviews, and launch a parallel pr-security-reviewer agent per qualifying PR. Designed to run in /loop."
allowed-tools: Read, Write, Bash, mcp__claude_ai_Slack__slack_read_channel, Agent
---

# PR Review — Slack-Triggered Loop

Scan a Slack notifications channel (default: `prodsec-notifications`) for open GitHub PRs that need your attention, determine which ones qualify for review, skip any already being reviewed from a prior loop run, and launch a parallel `pr-security-reviewer` agent for each qualifying PR.

**Arguments**: `$ARGUMENTS`
- `--channel <name>` — override default channel (default: `prodsec-notifications`)
- `--hours <N>` — how far back to look in the channel (default: `48`)
- `--force <PR_URL>` — review a specific PR regardless of criteria

---

## State File

Loop-deduplication state is stored at:

```
~/.claude/projects/-Users-joerg-reichelt-workspace-pr-review/pr-review-running.json
```

Schema:
```json
{
  "running": [
    {
      "pr_url": "https://github.com/owner/repo/pull/N",
      "pr_number": 123,
      "repo": "owner/repo",
      "reason": "requested",
      "started_at": "2026-06-23T10:00:00Z"
    }
  ]
}
```

---

## Step 1: Get My GitHub Login

```bash
gh api user --jq '.login'
```

Store as `MY_LOGIN`.

---

## Step 2: Load and Clean State

Read the state file. If it does not exist, initialize as `{ "running": [] }` and write it.

For each entry in `running`, check whether the review has completed:

```bash
gh pr view <pr_number> --repo <repo> \
  --json reviews \
  --jq '.reviews[] | select(.author.login == "<MY_LOGIN>") | .submittedAt' 2>/dev/null
```

Remove an entry if any of these are true:
- A review from `MY_LOGIN` was submitted after `started_at`
- `started_at` is more than 4 hours ago (agent timed out)

Write the cleaned state back to the file.

---

## Step 3: Read Slack Channel for PR URLs

Parse arguments to get channel name (default: `prodsec-notifications`) and lookback hours (default: 48).

If `--force <PR_URL>` was passed, skip to Step 5 with just that URL.

Use `mcp__claude_ai_Slack__slack_read_channel` to read recent messages from the channel.

Extract all GitHub PR URLs matching: `https://github.com/[^/]+/[^/]+/pull/[0-9]+`

Deduplicate. Collect as `candidate_urls`.

If no URLs found, report "No PR URLs found in channel in the last N hours." and stop.

---

## Step 4: Fetch PR Metadata

Run in parallel — one `gh pr view` per URL:

```bash
gh pr view <N> --repo <OWNER>/<REPO> \
  --json number,title,state,isDraft,author,reviews,reviewRequests,headRefOid,additions,deletions \
  2>/dev/null
```

Filter out:
- `state != "OPEN"`
- `isDraft == true`
- `author.login == MY_LOGIN`
- PRs already in `running` (match by `pr_url`)

---

## Step 5: Apply Review Criteria

Check criteria in order. First match wins.

**Criterion 1 — Requested:**
`MY_LOGIN` in `reviewRequests[].requestedReviewer.login` AND no review from me.
→ `reason: "requested"`

**Criterion 2 — Re-review needed:**
I have a review where `state == "CHANGES_REQUESTED"` AND `commit.oid != headRefOid`.
→ `reason: "re-review"`

**Criterion 3 — Help unblock:**
PR has ≥ 1 APPROVED review on current HEAD, no CHANGES_REQUESTED on current HEAD, I have not reviewed, PR has < 3 approvals.
→ `reason: "unblock"`

If none match, skip.

---

## Step 6: Report Plan

```
=== PR Review Run: <timestamp> ===

Already being reviewed (skipping):
  - <PR_URL> (started <N>m ago)

Qualifying PRs to review:
  - <PR_URL> — <title> [reason: requested / re-review / unblock]

Skipped (no criteria matched): <N> PRs
```

---

## Step 7: Launch Review Agents

For each PR in `to_review`:

1. Add entry to state file:
```json
{
  "pr_url": "<PR_URL>",
  "pr_number": <N>,
  "repo": "<OWNER>/<REPO>",
  "reason": "<reason>",
  "started_at": "<ISO8601_NOW>"
}
```

2. Write updated state file.

3. Launch `pr-security-reviewer` agent in background with:
```
<PR_URL> --reason <reason> --login <MY_LOGIN>
```

Launch all agents in parallel.

---

## Step 8: Final Status

```
Launched <N> review agent(s):
  - <PR_URL> [<reason>]

Next loop run will skip these until their review is posted (or 4h timeout).
```

---

## Loop Notes

- Run with `/loop 30m /pr:review` to poll every 30 minutes.
- The state file persists across loop iterations.
- A review is considered complete once the agent posts a GitHub review.
- Entries older than 4 hours are auto-expired to handle crashed agents.
- To reset state: `echo '{"running":[]}' > ~/.claude/projects/-Users-joerg-reichelt-workspace-pr-review/pr-review-running.json`
