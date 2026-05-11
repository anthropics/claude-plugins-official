---
name: matter-update
description: Append a dated event to a matter's history file and refresh the log row — captures new developments, status changes, risk re-assessments, deadline shifts, and settlement authority changes. Use when the user wants to log an update on a matter, note a development, or record a status change against the portfolio.
argument-hint: "[slug] [brief event description]"
---

# /matter-update

1. Follow the workflow and reference below.
2. Confirm slug exists in `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/` and `_log.yaml`.
3. Prompt for event type, date (default today), summary, and any log field updates (risk change, status change, next deadline shift, materiality reclassification).
4. Append dated entry to `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md`.
5. Update `_log.yaml` — set `last_updated` to today, apply any field updates.
6. Confirm.

---

# Matter Update

## Purpose

The portfolio only stays useful if it stays current. This skill makes logging an update cheap — two minutes of structured capture, no freeform drift.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — find the row
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md` — append target
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` — reference (don't rewrite)
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` — risk calibration (if re-assessing risk)

**Conflicts gate — unbypassable.** Before logging an update, check `_log.yaml` for the matter slug. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Run `/litigation-legal:matter-intake` first so the conflicts check runs and the matter workspace exists. I won't append history to an unmanaged matter — the conflicts check is the gate, and there's no `history.md` to append to until the matter is intaken."

## Input

Slug (required). If not provided, ask — with a short list of recently updated matters to pick from.

## The update

### 1. Event type

Offer categories:

- **Procedural** — motion filed/received, order issued, hearing held, deadline set
- **Discovery** — production made/received, depositions taken, subpoena served
- **Substantive** — new facts, key document surfaced, ruling on merits
- **Strategy** — posture shift, settlement offer made/received, authority update
- **Risk re-assessment** — severity or likelihood changed
- **Stakeholder** — new person looped in, outside counsel change
- **Administrative** — engagement letter executed, budget adjusted, hold refreshed

Or freeform if none fits.

### 2. Date

Default today. Accept an override (e.g., capturing an event from last week).

### 3. Summary

One-paragraph narrative. What happened, what it means, any immediate implication.

### 4. Log field changes

Walk through potentially affected fields:

- `status:` — has the stage shifted (e.g., pleadings → fact discovery)?
- `stage:` — substage update
- `risk:` — reassessment required?
- `materiality:` — any change (new facts might trigger reserve or disclosure)?
- `exposure_range:` — revise if new information
- `next_deadline:` — new upcoming date, if any
- `outside_counsel:` — change?
- `internal_owners:` — anyone new or removed?
- `legal_hold:` — refreshed, expanded, released?

Only prompt for fields likely affected by the event type. Procedural updates usually touch `stage` and `next_deadline` only; a settlement offer might touch `materiality`, `exposure_range`, `status`.

### 4pre. Settlement-acceptance gate

If the Strategy update is a **settlement acceptance** (the company is accepting a settlement offer, executing a settlement agreement, or authorizing acceptance in principle — not merely logging an offer made or received): Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Accepting a settlement has legal consequences — it resolves claims, typically requires a release, and can affect insurance, tax, and related matters. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the matter, proposed settlement terms (dollar, structural, release scope, confidentiality, non-disparagement), exposure at stake, authority ladder status (see `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` settlement authority), what could go wrong, what to ask the attorney before accepting.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not log the acceptance or flip materiality on acceptance basis without an explicit yes. Logging offers or counters does not require the gate — acceptance does.

### 4a. Materiality trigger — explicit prompt

Certain event types force a materiality re-check. When the event type is in this list, **always prompt** — don't let the user move on without an explicit answer:

| Event type | Materiality trigger prompt |
|---|---|
| Substantive (new facts, key document, merits ruling) | "This event is substantive. Does it push `materiality`? Current: `[current]`. Options: `reserved / disclosed / monitored / none`. Change?" |
| Strategy (posture shift, settlement offer made or received) | "Settlement activity often triggers materiality reclassification. Current: `[current]`. If the offer, counter, or acceptance moves exposure or shifts from contested to probable-and-estimable, reclassify." |
| Risk re-assessment (severity or likelihood changed) | "Risk moved. Materiality should track. Current: `[current]`. Reclassify?" |
| Regulatory / enforcement development | "Regulator action (subpoena, CID, enforcement notice) usually triggers disclosure analysis. Current: `[current]`. Change?" |

Acceptable answers include `no change` — but `no change` must be explicit, not implied by silence. Capture in the history entry:

```markdown
**Materiality check:** [no change / changed from X to Y]
**Reasoning:** [one sentence]
```

If materiality moves to `reserved` or `disclosed`, and the matter did not previously carry a reserve or disclosure, flag the event as requiring finance / audit-committee notification per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` materiality thresholds.

### 5. Seed doc prompt (optional)

If the update references a document (order, filing, correspondence), ask if there's a path to link. Not pushy.

## Writing

### Append to `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md`

Most recent at top, directly under the `---` that follows the header.

```markdown
## [YYYY-MM-DD] — [Event type]: [short title]

[Paragraph summary.]

**Fields changed:**
- [field]: [old → new]
- [field]: [old → new]

**Related doc:** [path, if provided]
```

If no fields changed, omit the "Fields changed" block.

### Update `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml`

- Apply any field changes.
- Set `last_updated: [today]` (or the event date if the user overrode — the log tracks when the record was last touched).

## Confirm

Show the user the history entry and the yaml diff before writing:

> Here's what I'll append and update. Good to commit?

## What this skill does not do

- Edit past history entries. Corrections are new entries that reference and correct prior ones.
- Silently change the log. Every field change is shown to the user before write.
- Decide whether a new development warrants reserve/disclosure. It surfaces the question ("this might push materiality — want to reclassify?"), the user answers.
