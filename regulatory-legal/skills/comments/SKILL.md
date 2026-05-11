---
name: comments
description: Review open NPRM comment periods, log decisions, track deadlines. Use when an NPRM has a comment window open and you need to surface deadlines, decide whether to file, or record a filing / not-filing / waived decision (--decide CMT-ID).
argument-hint: "[optional: --decide CMT-ID]"
---

# /comments

## Purpose

NPRMs have deadlines. The decision to file a comment or not is an attorney
call — but the deadline disappearing without a logged decision is the risk.
This skill surfaces open comment periods and records decisions.

## Load context

`~/.claude/plugins/config/claude-for-legal/regulatory-legal/comment-tracker.yaml` → all tracked NPRMs and their status.
`~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` → default comment decision owner.

## Default view — open comment periods

```markdown
## Comment Period Tracker — [date]

### ⏰ Deadline in <14 days

| ID | Regulation | Deadline | Days left | Decision | Owner |
|---|---|---|---|---|---|
| CMT-001 | [name] | [date] | [N] | Undecided | [owner] |

### 🟡 Open (>14 days)

[same table]

### Recently decided

| ID | Regulation | Decision | Rationale |
|---|---|---|---|
| CMT-002 | [name] | Not filing | [reason] |

---

**Total open:** [N]  **Undecided with deadline <30 days:** [N]
```

## Log a decision

```
/regulatory-legal:comments --decide CMT-001
Decision: [filing / not-filing / waived]
Rationale: "[brief — e.g., 'Rule doesn't apply to our model' or 'Filing comment on Section 3']"
```

Updates tracker. If decision is "filing": prompt for filing deadline reminder
(comment deadline minus 5 business days for internal review).

## Notifications

On first detection of an NPRM (populated by reg-feed-watcher): Slack DM to
comment decision owner if Slack MCP is configured and `owner_slack` is set.

Reminder at 14 days before deadline if decision is still "undecided."
Reminder at 3 days before deadline if still undecided — elevated urgency.

## Consequential-action gate (submit a regulatory comment / respond to a regulator)

**Before logging a decision as "filing" — and always before producing a comment letter or regulator-response draft for submission:** Read `## Who's using this` in ~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md. If the Role is **Non-lawyer**:

> Submitting a comment or response to a regulator has legal consequences. It's a public statement of the company's position, it's on the record in the rulemaking or enforcement matter, and positions taken here bind the company and can be used against it in subsequent proceedings. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> - The rulemaking or inquiry (regulator, docket, deadline)
> - What the proposed comment/response says and on what sections
> - Open questions and what's unresolved
> - What could go wrong (adverse admissions, inconsistent prior positions, coordination-of-comment concerns with trade associations)
> - What to ask the attorney (should we file at all; should we file jointly through a trade group; are there positions we should not take)
>
> If you need to find a lawyer: your professional regulator's referral service is the fastest starting point (state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or your jurisdiction's equivalent).

Do not log a "filing" decision or produce a submission-ready draft past this gate without an explicit yes. Tracking views, deadline reminders, and "not-filing / waived" decisions do not require the gate.

---

## What this skill does not do

- Draft the comment letter. That is a separate attorney task.
- Make the filing decision. It tracks the decision; the attorney makes it.
- Monitor post-comment activity. Once a decision is filed, this tracker's job
  is done — follow the rulemaking through `/regulatory-legal:reg-feed-watcher`.

> The `comment-decision` `gap_type` semantics, the per-send Slack confirmation rule, and the comment-tracker.yaml schema live in the **gap-surfacer** reference skill — load it before doing substantive work.
