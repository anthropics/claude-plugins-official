---
name: gap-surfacer
description: >
  Reference: shared gap- and comment-tracker framework backing /regulatory-legal:gaps
  and /regulatory-legal:comments. Tracks open policy gaps with remediation status,
  ingests gaps from policy-diff, surfaces what's open and aging, routes to owners,
  and notifies gap owners via Slack with per-send confirmation. Loaded by the gaps
  and comments skills before doing substantive work.
user-invocable: false
---

# Gap Surfacer

> Owner notifications: on by default. To opt an owner out, leave `owner_slack` empty.

## Per-send confirmation — no exceptions

Before sending ANY Slack message (assignment notice, overdue reminder, bulk notification, status report):

1. Show the user exactly what you're about to send and to whom: "I'm about to send this to [N] people: [preview]."
2. Wait for an explicit yes.
3. If the message contains any citations, deadlines, or compliance conclusions, add: "⚠️ The citations in this message are unverified — I'm not confirming they're current before sending. Do you want me to add a 'verify before acting' line?"
4. Never send without the confirm. Not on a cadence. Not in a batch. Not because it was sent yesterday.

Auto-send without confirmation is the most irreversible action in this plugin, sending content this plugin's own footer says may be wrong, to people who have no way to check. That combination does not get to skip review.

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/regulatory-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Gaps get found and then forgotten. This skill tracks them until they're closed
and notifies the people responsible for closing them.

## The tracker

Lives at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/gap-tracker.yaml`:

> **Note on comment-tracker.yaml:** `~/.claude/plugins/config/claude-for-legal/regulatory-legal/comment-tracker.yaml` is a sibling file owned by the comments skill. It is written to by reg-feed-watcher (which logs NPRMs automatically) and the comments skill (which tracks user-initiated comment decisions). This skill does not read or cross-reference it. If you modify the comment-tracker schema, update both actual consumers.

```yaml
gaps:
  - id: GAP-001
    requirement: "[what the reg requires]"
    regulation: "[name + cite]"
    policy_affected: "[name or 'new policy needed']"
    gap_type: "partial"  # none | partial | full | new-policy | watch | comment-decision
    owner: "[name from policy index]"
    owner_slack: "[Slack user ID or handle, if known]"
    opened: 2026-03-01
    due: 2026-06-01  # reg effective date, internal deadline, or comment deadline
    status_verified: true  # false if upstream policy-diff could not confirm the rule is in force; unverified items never hit 🔴 Overdue
    status: "open"  # open | in-progress | closed | risk-accepted
    notified: false  # set to true after assignment notification sent
    resolution: ""  # filled on close
```

**Never classify a gap as Overdue on an unverified rule.** The 🔴 Overdue classification means "we missed a binding deadline." If the rule's status is unverified (policy-diff set `status_verified: false`, or the rule is >12 months old / past its applicability date with no currency confirmation), the deadline may not be binding. Use 🟡 "Review needed" and note: "If this rule is in force as published, this would be overdue by [N] days. Verify rule status before escalating." Route unverified-rule items to `watch`, not to the active overdue/due-soon buckets; the `watch` revisit cadence forces a rule-status check before the item can re-surface as a compliance gap.

**`gap_type` semantics:**

| Value | Meaning | Typical reminder cadence |
|---|---|---|
| `none` | Policy already covers the requirement. Logged for audit trail only. Should be rare — if most entries are `none`, the diff is probably running against the wrong policy. | No auto-reminder. |
| `partial` | Policy addresses the topic but doesn't fully cover the new requirement. Needs an amendment. | 30 days before due. |
| `full` | Policy contradicts or silently omits the new requirement. Needs a rewrite or new section. | 30 days before due. |
| `new-policy` | No existing policy covers this. Policy needs to be drafted. | 30 days before due. |
| `watch` | Forward-looking item — ANPR, RFI, proposed rule not yet final. No compliance obligation today; policy work waits for the final rule. `due:` is a revisit date (typically the NPRM expected date or a one-year horizon), not a compliance deadline. | No auto-reminder; re-evaluate when an NPRM drops or at the revisit date. |
| `comment-decision` | Pre-rulemaking comment decision pending — ANPR or NPRM where the team is deciding whether to file a comment. `due:` is the comment deadline. | 21 days before due (tighter than compliance gaps because comment-drafting windows are short). |

A `watch` or `comment-decision` entry is not a compliance gap — it's a tracking artifact for pre-rule items that the watch skill and comments skill produce. Surface them in the status report in their own bucket so counsel reading at 7am can tell at a glance which items are "fix this before a regulator notices" vs. "keep an eye on this."

## Modes

### Mode 1: Ingest from policy-diff

When policy-diff finds gaps, append them to gap-tracker.yaml. De-dupe — same
requirement + same policy = same gap, don't double-count.

**After ingesting, notify the owner:**

If Slack MCP is available and `owner_slack` is set:

Send a Slack DM to the gap owner — but only after the per-send confirmation at the top of this file. Preview the message to the user, wait for an explicit yes, then send:

```
📋 New compliance gap assigned to you

Gap: [GAP-ID] — [requirement, one sentence]
Regulation: [name + link]
Policy affected: [policy name or "new policy needed"]
Due: [reg effective date]

View full gap tracker: /regulatory-legal:gaps
```

Set `notified: true` in the tracker entry after sending.

If Slack MCP is not available: note in the status report that owner notification
was not sent and flag for manual follow-up.

### Mode 2: Status report

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Open Gaps — [date]

### Bottom line

[N gaps need action by [date] — top 3: X, Y, Z]

### 🔴 Overdue

| ID | Requirement | Policy | Owner | Due | Days over |
|---|---|---|---|---|---|

### 🟠 Due in <30 days

[same]

### 🟡 Open

[same]

### 👀 Watch items (forward-looking — pre-rule)

[Pre-rule tracking — `watch` and `comment-decision` entries. These are not
compliance gaps. Surface separately so the overdue / due-soon bands contain
only real compliance deadlines.]

| ID | Item | Type (ANPR/NPRM/RFI) | Comment deadline | Owner |
|---|---|---|---|---|

### In progress

[same]

### Recently closed

[last 5, with resolution]

---

**Oldest open gap:** [ID], [N] days
**Gaps by owner:** [breakdown]
**Owner notifications sent:** [N] / [N total gaps]

---

**Next step for each open gap:** `/regulatory-legal:policy-redraft` produces a marked-up policy redraft with `[verify]` tags and a change summary. It's a proposal for the policy owner's review — not a direct edit to source documents.

---

**Verify citations before relying on them.** Regulation citations in this tracker were AI-generated upstream (by reg-feed-watcher and policy-diff) and have not been checked against a primary source. Before closing or risk-accepting a gap — or citing one in an attestation, board report, or regulator response — confirm the underlying rule against Westlaw, your firm's research platform, or the issuing authority's website. AI-generated regulatory citations are sometimes fabricated, misquoted, or stale. Source tags carried forward from upstream (e.g., `[Federal Register]`, `[web search — verify]`) show where each citation originated; `verify` tags carry higher fabrication risk and should be checked first. Never strip the tags when surfacing gaps.
```

## Config-dependent fallbacks

This skill reads gap-response owners and the escalation path from `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`. When a value it needs is empty or still `[PLACEHOLDER]`:

- **Gap-response triager missing:** leave assignment open and append to the output: "No triager is set in `## Gap response process`. Assign one with `/regulatory-legal:cold-start-interview --redo` or by editing `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` so new gaps get routed."
- **Owner unknown for a newly-ingested gap (no owner in policy library):** log the gap with `owner: [unassigned]` and append: "[N] gaps were ingested without an owner because the policy library doesn't name one for the affected policy. Fill in the Owner column in the policy library to route them."
- **Escalation path missing for an overdue material gap:** still report it as overdue, and append: "No escalation path is set for material overdue gaps. Configure it with `/regulatory-legal:cold-start-interview --redo` or by editing `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`."

Say nothing about config when the values are populated.

**Due-date reminder logic (runs during status report and scheduled agent):**

Reminder cadence is a function of `gap_type` — compliance gaps get a 30-day heads-up, comment-decision items get 21 days (tighter because the drafting window is shorter), watch items get no auto-reminder (re-evaluate when an NPRM drops).

For each gap with status "open" or "in-progress":
- `partial`, `full`, `new-policy`, `none`: if due date is within 30 days and a reminder has not been sent in the last 7 days, PREVIEW a Slack DM (subject "⏰ Reminder: compliance gap due in [N] days") and wait for per-send confirm before sending.
- `comment-decision`: if comment deadline is within 21 days and a reminder has not been sent in the last 7 days, PREVIEW a Slack DM (subject "💬 Comment-decision deadline in [N] days") and wait for per-send confirm before sending.
- `watch`: no auto-reminder. Revisit when the tracker is reviewed or an NPRM is logged for the same regulation.
- If due date has passed on a compliance gap: flag as overdue in the report and PREVIEW a Slack DM — wait for per-send confirm before sending.
- If comment deadline has passed on a `comment-decision` item and no comment was filed: flag as overdue, PREVIEW a Slack DM (wait for per-send confirm), and ask the owner to update to `risk-accepted` (deliberate no-comment) or `closed` (comment filed) with a note.
- Record reminder timestamps in the tracker to avoid repeat nags.
- Batch reminders still require per-send confirm — previewing "you're about to send 12 DMs" and waiting for yes counts; silently firing a batch does not.

### Consequential-action gate (certify compliance)

**Before closing a gap as resolved, or producing any output that certifies compliance with a regulatory requirement (internal attestation, board report, audit response, regulator response):** Read `## Who's using this` in ~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md. If the Role is **Non-lawyer**:

> Certifying compliance — or closing a gap as resolved — has legal consequences. The certification can be used against the company if it's later shown to be wrong, and premature closure leaves exposure unaddressed. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> - The gap (requirement, source, what the policy diff found)
> - What the proposed resolution does and does not cover
> - Any residual gap or ambiguity
> - Open questions and what's unresolved
> - What could go wrong (overbroad certification, unresolved residual obligation, inconsistent prior position)
> - What to ask the attorney (is this truly closed; should we risk-accept with rationale instead; do we need outside-counsel concurrence)
>
> If you need to find a lawyer: your professional regulator's referral service is the fastest starting point (state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or your jurisdiction's equivalent).

Do not mark a gap closed or produce a compliance certification past this gate without an explicit yes. Status reports and tracking views do not require the gate.

### Mode 3: Close a gap

```
/regulatory-legal:gaps --close GAP-001
Resolution: "Policy updated v2.3, approved [date]"
```

Updates status to closed, records resolution and close date.

### Mode 4: Risk-accept a gap

Sometimes the answer is "we're not going to fix this." That's a valid decision
— but it should be documented.

```
/regulatory-legal:gaps --accept GAP-002
Rationale: "Requirement applies only to [condition we don't meet]. Revisit if [trigger]."
Accepted by: [name with authority]
```

Status → risk-accepted. Stays in the tracker (not deleted) but falls out of
the open-gaps report.

## Integration: reg-change-monitor agent

The agent's digest includes the gap count and oldest-open-gap age. If anything
goes overdue, that goes at the top of the digest. The agent also runs the
due-date reminder check and sends any outstanding Slack notifications.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

If the tracker surfaced more than ~10 open gaps, or any time the user asks: offer the dashboard (see CLAUDE.md `## Outputs → Dashboard offer for data-heavy outputs`). Shape the offer for this output — counts by severity, a timeline of gaps by due date, and a sortable grid with owner, status, and last-touched date.

## What this skill does not do

- Close gaps on its own. Closing requires the resolution note and the human
  action that the note describes.
- Send Slack notifications if the Slack MCP is not configured. Falls back to
  flagging in the status report.
- Send more than one reminder per 7-day period per gap. Nag once, not constantly.
