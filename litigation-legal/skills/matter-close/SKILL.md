---
name: matter-close
description: Close a matter — capture outcome, final exposure, and lessons, then archive it out of the active portfolio without deleting the record. Use when the user wants to close a matter, says "[matter] is done", or needs to record a settlement, dismissal, judgment, withdrawal, or consolidation outcome.
argument-hint: "[slug]"
---

# /matter-close

1. Follow the workflow and reference below.
2. Confirm slug and current status.
3. Capture outcome: resolution type (settled, dismissed, judgment for/against, withdrawn, consolidated), date, final exposure/cost, lessons.
4. Update `_log.yaml`: `status: closed`, add `closed: YYYY-MM-DD` and `outcome:` fields.
5. Append final entry to `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md`.
6. Matter stays in `_log.yaml` and `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/` — not deleted. `/portfolio-status` filters it from active rollups.

---

# Matter Close

## Purpose

Matters end. The outcome is the single most valuable data point the portfolio generates — it calibrates the risk framework for future matters. Closing a matter captures the outcome structurally so the record is useful, not just archived.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — find the row
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` — reference (intake context)
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md` — append target

**Conflicts gate — unbypassable.** Before closing, check `_log.yaml` for the matter slug. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Nothing to close — either the slug is wrong or the matter was never intaken through `/litigation-legal:matter-intake`. Check the slug first; if it genuinely was never intaken, there's no row to update and no file structure to close."

## Input

Slug (required).

## The close

### 1. Resolution type

- `settled` — with counterparty, dollar amount, structural terms
- `dismissed` — with or without prejudice, by what mechanism
- `judgment-for-us` — at what stage, appeal exposure
- `judgment-against-us` — at what stage, appeal status, exposure crystallized
- `withdrawn` — by counterparty, circumstances
- `consolidated` — merged into another matter (provide slug of parent)
- `other` — with explanation

### 2. Resolution date

The date the matter actually ended (settlement executed, order issued, dismissal filed).

### 3. Final exposure

- Actual cost to company (settlement amount + fees + injunctive/structural cost)
- vs. initial exposure range at intake (did we call it?)
- Reserve accuracy (if reserved): booked vs. actual

### 4. Lessons

Two or three sentences. What did we get right? What did we misjudge? Anything the intake should have flagged earlier?

This is the part future counsel will reread. Be honest. "Misjudged likelihood — plaintiff firm was more aggressive than expected" is worth more than "resolved favorably."

### 5. Seed doc prompt

Settlement agreement, final order, dismissal — path if available. Not required.

## Writing

**Before closing the matter (the consequential act — the matter is archived and active tracking ends):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Closing a matter has legal consequences — it ends active tracking, may affect any associated legal hold (run `/legal-hold --release` separately if appropriate), and establishes the final record the company relies on. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the matter, resolution type and terms, final exposure vs. initial, reserve accuracy, related matters or appeals still live, what could go wrong with premature closure, what to ask the attorney.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not write the close fields or append the close entry without an explicit yes.

### Update `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml`

```yaml
status: closed
closed: [YYYY-MM-DD]
outcome: [resolution-type]
final_cost: [dollar amount]
last_updated: [today]   # close is the last touch; record it
```

Retain all existing fields. Do not delete the row.

### Append final entry to `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md`

```markdown
## [YYYY-MM-DD] — Matter closed: [resolution-type]

**Resolution:** [narrative — what happened, on what terms]
**Final cost:** [amount + structural terms if any]
**vs. initial exposure:** [compare to matter.md intake range]
**Reserve accuracy:** [if applicable]

**Lessons:**
[2-3 sentences — honest retrospective]

**Related doc:** [settlement agreement / final order / etc., if provided]
```

### Touch `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md`

Add a closing block at the end (don't modify earlier sections — they're the historical intake):

```markdown
---

## Closed [YYYY-MM-DD]

[Resolution summary in one paragraph. Pointer to the final history entry for detail.]
```

## Confirm

Show the user the full close entry and the yaml changes before writing.

## What this skill does not do

- Delete matters. Closed matters stay in `_log.yaml` and on disk — they're the training set for the portfolio's judgment.
- Re-open. If a closed matter comes back (appeal, related litigation), open a new matter that references the closed one in `matter.md`.
- Summarize lessons the user didn't say. If the user skips the lessons section, leave it empty rather than invent.
