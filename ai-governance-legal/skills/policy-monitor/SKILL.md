---
name: policy-monitor
description: >
  Keep the AI policy current with practice — weekly sweep of saved AIAs, triage
  results, and vendor reviews to find policy drift, or direct query for a proposed
  new AI practice. Use when user says "policy sweep", "does our AI policy cover
  this", "we want to start doing X — does the policy need updating", "run the
  policy monitor", or on a recurring schedule.
argument-hint: "[describe a proposed new AI practice — or omit / use --sweep for crawl mode]"
---

# /policy-monitor

**Sweep mode** (no argument or `--sweep`):
1. Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → outputs folder path, AI policy document, last sweep date.
2. Use the framework below. Scan outputs folder for files since last sweep.
3. For each output: extract approved practices → diff against current policy commitments and use case registry.
4. Classify gaps: REQUIRED (policy misrepresents current practice) vs ADVISABLE (policy silent).
5. For each gap: quote current policy, describe gap, draft suggested language.
6. Flag any use cases in outputs not yet added to the `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` registry.
7. Present results to the human. Only after acknowledgment, update `Last policy sweep` and `gaps_found` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.

**Direct query mode** (with description argument):
1. Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → current policy commitments, use case registry, actual policy document.
2. Parse proposed practice. Diff against policy: use case coverage, automation level, affected parties, disclosure, vendor data use, oversight.
3. Output: covered / missing / conflicting + suggested language for each gap + registry entry if needed + timing recommendation.

**Recurring runs:**
Set up a recurring reminder in your own scheduler to run `/ai-governance-legal:policy-monitor` weekly. Scheduled execution requires a scheduled-tasks integration, which is not bundled with this plugin.

```
/ai-governance-legal:policy-monitor
/ai-governance-legal:policy-monitor "We want to use AI to automatically flag expense reports for review"
```

---

## Purpose

AI policies drift from practice faster than almost any other policy document — the
field moves quickly, use cases multiply, and each approved AIA or triage result
represents a new commitment the policy may not have caught up with. An AIA approves
a new AI use case with a human-oversight condition. A vendor AI agreement permits
data processing the policy doesn't mention. A triage result marks a new category
of deployment as conditional with a disclosure requirement. The policy sits there
unchanged.

This skill catches the drift — either by crawling the outputs folder weekly, or by
answering the direct question: "we're about to start doing X, what does that mean
for our AI policy?"

The output is always the same: here's the gap, here's the suggested language.

---

## Load current state

Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`:
- `## AI policy commitments` — commitments extracted from the published policy
- `## Use case registry` — approved, conditional, and never use cases
- `## Outputs` — outputs folder path, AI policy document location, last sweep date

If `## Outputs` contains `[PLACEHOLDER]`:
> "Outputs aren't configured yet. I can still run a direct-query check — describe
> what you're planning to do and I'll diff it against your current AI policy. To
> enable the crawl sweep, run `/ai-governance-legal:cold-start-interview` and provide the outputs
> folder path."

Read the actual AI or acceptable use policy document from the path in `## Outputs`
→ **AI policy document**. The commitments in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` are a summary; the actual
document is authoritative for suggesting edits.

---

## Mode detection

**Sweep mode:** No argument, `--sweep`, or triggered by schedule.
→ Scan the outputs folder. Diff all outputs since last sweep against current policy.

**Direct query mode:** User provides a description of a proposed new AI practice.
→ Diff that practice against current policy and use case registry. Suggest updates.

---

## Mode 1: Sweep

### Determine scope

Read `## Outputs` → **Last policy sweep** date. Scan for output files in the
outputs folder dated after that date. If no date is recorded, scan all files and
note: "First sweep — scanning all outputs."

If the outputs folder is empty or has no new files since the last sweep:
> "No new outputs since [last sweep date]. AI policy appears current with recent
> practice. Next scheduled sweep: [date]."

**Do not update `Last policy sweep` or `gaps_found` automatically.** After the sweep results are presented, wait for the human to acknowledge them ("sweep acknowledged," "results reviewed," or equivalent). Only then update `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`:

- `Last policy sweep: [date of acknowledgment]`
- `gaps_found: [N]` (number of REQUIRED + ADVISABLE gaps found in that sweep)

Updating the stamp before acknowledgment would let an unreviewed sweep silently roll forward and suppress the next sweep's attention to the same gaps.

### What to read in each output type

**AIAs (AI Impact Assessments):**
- Extract: use case approved, AI system description, deployment mode (assistive /
  augmentative / automated), conditions imposed, affected parties, vendor used,
  any disclosure requirements to affected individuals
- Flag: use cases not in the registry, use cases approved with conditions not
  reflected in policy, vendor added that policy doesn't cover, automated decision
  deployed where policy implies human oversight

**Triage results (CONDITIONAL / APPROVED outcomes):**
- Extract: use case classified, tier assigned, conditions imposed
- Flag: new use case categories not in registry, conditions that imply policy
  commitments (e.g., "must disclose to affected parties" — does the policy say you
  do this?), newly approved practices that expand policy scope

**Vendor AI reviews (signed / approved):**
- Extract: vendor added, data use terms agreed to, any AI-specific provisions
  accepted that differ from standard positions in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`
- Flag: vendors added whose data use terms the policy should reference (e.g., "we
  use third-party AI services and ensure they do not train on our data"), approved
  deviations from standard positions that the policy implies you hold

**Use case registry updates:**
- If new entries were added to the registry since the last sweep (directly, not
  through an AIA), check whether the policy reflects those approved categories.

### Gap identification

For each flagged item, assess:

**REQUIRED update** — the policy makes a commitment that an output contradicts, or
an approved use case has no policy coverage and affects external parties. Not
updating creates a material misrepresentation.

> Example: AI policy says "we do not use AI in employment decisions." An AIA
> approved an AI-assisted hiring screening tool with human review required. Policy
> needs updating — even with human review, AI is now involved in employment
> decisions. "We do not use AI" is no longer accurate.

**ADVISABLE update** — policy is silent but not in conflict. The practice is
defensible without updating, but cleaner with it. Important when the practice
affects external parties or creates a reasonable expectation.

> Example: Policy says "we use AI to improve our products and services." An AIA
> approved an AI feature for customer support drafts. Policy technically covers it
> but is vague. Advisable to be more specific so customers know what they're
> interacting with.

### Sweep output format

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

*This sweep is derived from AIAs, triage results, and vendor AI reviews that carry the plugin's privilege/confidentiality marking. The sweep inherits that status. Distribute deliberately — forwarding gap findings outside the privilege circle can waive privilege on the underlying assessments.*

# AI Policy Monitor — Sweep Report

**Date:** [date]
**Outputs scanned:** [N files] | **New since last sweep:** [N files]
**Gaps found:** [N] REQUIRED | [N] ADVISABLE

---

## REQUIRED updates

### [Gap 1 short name]

**Source:** [filename / output type that triggered this]
**What's happening:** [plain description of the new practice]
**Current policy:** [quote the relevant section — or "No coverage"]
**Gap:** [what's missing or inconsistent]

**Suggested language:**
> *Add to / update [section name]:*
> "[Drafted policy text — specific, consistent with house style of the actual policy]"

---

[repeat for each REQUIRED gap]

---

## ADVISABLE updates

### [Gap name]

**Source:** [filename]
**What's happening:** [description]
**Current policy:** [quote or "Silent"]
**Suggested language:**
> *Add to / update [section]:*
> "[Drafted text]"

---

## No action needed

[List outputs scanned where no gaps were found]

---

## Use case registry sync

[Any use cases approved since the last sweep that aren't yet in the `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`
registry — suggest registry entries to add]

---

## Next steps

- [ ] Review REQUIRED updates — decisions needed before the associated use cases
  go live (or immediately if already live)
- [ ] Review ADVISABLE updates — lower urgency, address at next policy refresh
- [ ] Add new use cases to registry (if any flagged above)
- [ ] Next scheduled sweep: [date]
```

---

## Mode 2: Direct query

### Parse the proposed practice

Extract from the user's description:
- What AI system or capability is being introduced?
- What does it do — assistive, automated decisions, content generation?
- Who does it affect — employees, customers, third parties?
- Which vendor or model is involved?
- Is there human review, or is it fully automated?
- Are affected parties told the AI is involved?
- Any data flowing to a vendor that wouldn't be expected?

If the description is vague, ask one clarifying question. Don't run a long intake
— direct query mode should be fast.

### Policy diff

Check the proposed practice against the current policy and use case registry:

| Check | Current policy / registry | Proposed practice | Verdict |
|---|---|---|---|
| Use case category | [registry — approved / conditional / never / not present] | [new use case] | 🟢 Covered / 🟡 Gap / 🔴 Conflict |
| Scope of AI use | [what policy says AI is used for] | [new use] | |
| Automated decisions | [policy position on automation] | [is this automated?] | |
| Disclosure to affected parties | [what policy commits to] | [what this requires] | |
| Vendor data use | [policy position on vendor AI] | [this vendor's terms] | |
| Human oversight | [policy statement if any] | [what's actually in place] | |

### Direct query output format

```markdown
# AI Policy Check: [Proposed practice in one line]

**Bottom line:** [POLICY UPDATE REQUIRED / ADVISABLE / NO UPDATE NEEDED]

---

## What's covered

[Aspects of the proposed practice already addressed — brief, confirms no change needed]

## What's missing

### [Gap 1]

**Current policy:** [quote or "Silent"]
**What's needed:** [why this gap matters — legal, reputational, or expectation reason]

**Suggested language:**
> *Add to [section]:*
> "[Drafted text]"

### [Gap 2]
[same format]

## What conflicts

### [Conflict 1 — if any]

**Current policy says:** [quote]
**Proposed practice does:** [what conflicts]
**Resolution:** [which one needs to change — usually practice adjusts to match policy,
or policy is updated to a defensible new position; never silently accept both]

---

## Use case registry

[If this use case isn't in the registry: "Add to `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → Use case registry:"]
```
| [use case] | [Approved/Conditional] | [conditions] | — |
```

---

## Timing

[REQUIRED: "Policy update should happen before this practice goes live — or
immediately if it's already running."
ADVISABLE: "Can proceed; update at next policy refresh."]
```

---

## Suggested language quality standards

AI policy language is unusually prone to becoming outdated — the field moves fast
and vague language ages better than specific commitments. When drafting:

- Match the voice and style of the existing policy (read the actual document)
- Prefer durable language: "AI-assisted" rather than naming specific models that
  will change; "automated or AI-assisted decisions" rather than technical descriptions
- Don't draft commitments the team can't keep — "we always have a human review
  AI outputs" is broken the moment one automated workflow ships
- When a policy position is genuinely changing (not just extending), say so
  explicitly: "This update reflects that we now use AI in [new category] — the
  previous language did not cover this."
- For disclosure language: draft it to be readable by the affected party (employee,
  customer), not just legally accurate

Always say which section to add to. If the right section doesn't exist, suggest
creating it and draft the header.

---

## Schedule integration

The weekly sweep is designed to run on a recurring cadence. Set up a recurring reminder in your own scheduler to run `/ai-governance-legal:policy-monitor` weekly. Scheduled execution requires a scheduled-tasks integration, which is not bundled with this plugin.

After each sweep, the **Last policy sweep** and **gaps_found** fields in `## Outputs` are updated only once the human has acknowledged the sweep results (see "Determine scope" above).

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It doesn't update the policy itself — it drafts suggested language and flags
  decisions, but a human reviews and approves every change.
- It doesn't catch incoming regulations — that's `reg-gap-analysis`. This skill
  monitors internal practice drift, not external legal changes.
- It doesn't enforce that outputs are saved — if AIAs and triage results aren't
  being saved to the configured folder, the sweep won't find them. Direct-query
  mode works without saved outputs.
- It doesn't read email, Slack, or informal decisions — only structured outputs
  saved to the configured folder.
- It doesn't update the use case registry automatically — it flags registry gaps
  and drafts entries for human review before adding.
