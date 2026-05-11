---
name: matter-briefing
description: Deep briefing on one matter — current posture, what's changed, next deadline, open questions, and a risk re-assessment check, ready before a GC update or outside counsel call. Use when the user says "brief me on [matter]", "where are we on [matter]", or needs a read on a specific matter.
argument-hint: "[slug]"
---

# /matter-briefing

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → risk calibration + relevant stakeholders.
2. Follow the workflow and reference below.
3. Read `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` + `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md` + log row from `_log.yaml`.
4. Produce briefing: current posture, what's changed since last update, next deadline, open questions, risk re-assessment check ("does the `risk:` field still reflect reality?").
5. Flag staleness: if `last_updated` > 30 days, say so.

---

# Matter Briefing

## Purpose

Give the counsel a clean read on one matter in the time it takes to walk to a conference room. Current posture, what's changed, what's next, what's worth reconsidering.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — structured row
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` — narrative intake
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md` — event log
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` — risk calibration (so "risk: high" means something specific, not generic)

**Conflicts gate — unbypassable.** Before briefing, check `_log.yaml` for the matter slug. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Run `/litigation-legal:matter-intake` first so the conflicts check runs and the matter workspace is set up. I won't build a briefing on a matter that hasn't been intaken — the conflicts check is the gate."

## Input

Slug (required). If ambiguous or missing, ask the user to pick from a list of active matters.

## The briefing

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# [Matter Name] — Briefing as of [today]

**Status:** [status / stage]
**Risk:** [rating] ([severity] × [likelihood])
**Materiality:** [category]
**Outside counsel:** [firm — lead]
**Last updated:** [date] [flag ⚠️ STALE if >30d]
**Conflicts:** [status — flag ⚠️ if `pending` or `not-run`]

---

## One-paragraph summary

[Current posture. What are we doing and why. Name the pivot fact if one is captured.]

## What's changed recently

[Last 3-5 entries from history.md, most recent first. If history is thin, say so.]

## What's next

- **Immediate deadline:** [next_deadline + what it is]
- **Upcoming milestones:** [anything dated in matter.md or recent history]
- **Decisions pending:** [open questions flagged in matter.md]

## Exposure

[Range + any change since intake. If reserved, current reserve + whether recalibration is overdue.]

## Internal owners

[Who's looped in; whether anyone should be looped in and isn't]

## Risk re-assessment check

*A prompt, not an answer.*

- Does `risk: [rating]` still feel right, or has the case moved?
- Does `materiality: [category]` still match? (New facts might push toward reserve or disclosure.)
- Any new stakeholder the matter needs (e.g., CISO becomes relevant after a discovery development)?

## Open questions

[From matter.md and anything unresolved in history]

## For the conversation

[If user specified a purpose — "brief me before the call with outside counsel" — tailor the final section: questions to ask, decisions to get, updates to extract. If no purpose given, omit this section.]
```

## Staleness

If `last_updated > 30 days ago`: flag at the top AND suggest running `/litigation-legal:matter-update [slug]` after the meeting to capture whatever's discussed.

## Tone

This is not marketing. Say what's known; flag what's not. If a matter has thin history and was just opened, the briefing is short — and that's correct. Don't pad.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Predict outcomes. Risk rating is a captured judgment, not a forecast.
- Recommend strategy. Surfaces questions; the counsel answers them.
- Re-triage. If the user wants to re-triage, that's an `/matter-update` with field changes — this skill reads, doesn't write.
