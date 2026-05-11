---
name: oc-status
description: Generate weekly status-request email drafts to outside counsel across the active portfolio — markdown per matter, plus Gmail drafts when the MCP is available. Use when the user asks for OC status requests, weekly outside counsel check-ins, or wants per-matter status emails drafted from the portfolio log.
argument-hint: "[--all | --slug=foo | --no-gmail]"
---

# /oc-status

To run weekly, set a recurring reminder to invoke `/litigation-legal:oc-status`. Automated scheduling requires a scheduled-tasks integration, which is not bundled.

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml`, filter per default rules (or per flags).
2. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → outside counsel directive style, signer defaults, budget posture.
3. Follow the workflow and reference below.
4. For each matter in scope: read `matter.md` + `history.md`, draft per-matter email.
5. Write markdown to `~/.claude/plugins/config/claude-for-legal/litigation-legal/oc-status/[YYYY-MM-DD]/[slug].md`.
6. If Gmail MCP authenticated: create Gmail drafts. Else: markdown-only, note in summary.
7. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/oc-status/[YYYY-MM-DD]/_summary.md` — what ran, what was skipped and why.

---

# OC Status

## Purpose

Writing the same status-request email to outside counsel every week across 5–15 matters is mechanical cognitive tax. The content is consistent per matter (status, decisions pending, budget check). The audience is consistent (OC lead partner). The tone is consistent (per house outside-counsel-directive style). A scheduled task drafts all of them; counsel reviews and sends.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — the filtering and field source
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` — matter context (current posture, open questions)
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md` — recent events to inform what to ask about
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → outside counsel directive style, signer name/email, budget posture

## Filtering — which matters?

Default filter:

- `status != closed`
- `outside_counsel.firm != null` AND `outside_counsel.lead != null`
- Either: last update more than 10 days old (time for something to have happened) OR has a `next_deadline` within 21 days

Skip matters that just had a status update in the last 10 days (no need to re-ping) and matters where `outside_counsel.email` is null (email addresses needed for Gmail draft; still produce markdown).

Flags:
- `--all` → draft for every active matter regardless of recency
- `--slug=[slug]` → draft for one matter only (ad-hoc request)
- `--no-gmail` → skip Gmail draft creation even if MCP is available

## Per-matter email draft

Each email has the same skeleton; content is matter-specific.

**Subject:** per house convention (from `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` outside counsel directive style; fallback: `[Matter: [matter name]] — Weekly status update`)

**Body skeleton:**

```
[lead partner first name],

[One sentence opener — natural, matches house tone.]

Checking in on [matter name]. A few items:

1. **Status since [date of last update captured in history.md]** — what's moved, what's pending? Any filings, hearings, correspondence, or calls since we last touched base?

2. **Upcoming deadlines** — I show [next_deadline from log + any deadlines in matter.md]. Confirm coverage plan and any dates we should add.

3. **Decisions pending** — [pull open questions from matter.md that require OC input; if none, omit this numbered item and renumber]

4. **Budget** — [monthly / quarterly / on-request per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` budget posture]. Where are we against [budget authorization from matter.md]? Any variance to flag?

[If material and relevant: 5. Specific ask — e.g., "Please send me the latest draft of the motion to dismiss before [date]" — drawn from matter.md open questions.]

[Signoff — name, role, contact. From `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` signer default for OC directives.]
```

Adapt tone per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` outside counsel directive style — some shops are "dear counsel" formal; others are first-name-and-bullets. Match.

## Output

### Markdown drafts

Write to: `~/.claude/plugins/config/claude-for-legal/litigation-legal/oc-status/[YYYY-MM-DD]/[slug].md`

Each file is one email, formatted as:

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# [Matter name] — OC status request — [YYYY-MM-DD]

**To:** [outside_counsel.email from log] ([outside_counsel.lead], [outside_counsel.firm])
**From:** [signer name / email from `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`]
**Subject:** [subject line]

> The work-product header above applies to this internal record. The outgoing email body below goes to outside counsel on a retained matter, which is itself a privileged communication — apply the house privilege marking (`~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` privilege conventions) at the top of the email sent, typically `Privileged & Confidential — Attorney-Client Communication / Attorney Work Product`, not this internal work-product header.

---

[body per skeleton]
```

### Send gate (closing note on every draft)

Append the following to each markdown draft, immediately below the body and above the run metadata — strip before sending:

> This is a draft status email for attorney review before sending to outside counsel. Check for privileged content you did not intend to share outside the engagement circle, factual accuracy, tone, and budget posture. Do not send unreviewed — even routine weekly check-ins can surface theory, strategy, or concessions the sender didn't mean to put in writing.

### Gmail drafts (if MCP available)

If the Gmail draft-creation MCP is authenticated:

- Create a draft in the user's Gmail per matter with `to`, `from`, `subject`, `body` populated
- The draft sits in Drafts folder; user reviews and sends Monday morning
- If Gmail MCP is NOT available or fails: fall back to markdown-only and tell the user

### Run summary

After processing all matters, write `~/.claude/plugins/config/claude-for-legal/litigation-legal/oc-status/[YYYY-MM-DD]/_summary.md`:

```markdown
# OC Status Run — [YYYY-MM-DD]

**Matters processed:** [N]
**Drafts created:** [N]
**Gmail drafts:** [created / skipped — reason]

## Drafted for

| Matter | OC lead | Last updated | Reason for inclusion |
|---|---|---|---|
| [slug] | [lead] | [date] | [stale / upcoming deadline / --all / --slug] |

## Skipped

| Matter | Reason |
|---|---|
| [slug] | recent update (last touched [date]) |
| [slug] | no OC email in log — update with `/matter-update [slug]` |

## Anomalies

- Matters without outside counsel assigned: [list — if any are high/critical risk, flagged]
- Matters with outside counsel but no email in log: [list]
```

## Scheduling

This skill is designed to run weekly. Automated scheduling requires a scheduled-tasks integration that is not bundled with the plugin. To run weekly, set a recurring reminder to invoke `/litigation-legal:oc-status` — e.g., Monday morning on your calendar.

Ad-hoc: `/oc-status` any time. `/oc-status --slug=foo` for a single matter.

## What this skill does not do

- **Send the emails.** Drafts only. Counsel reviews and sends.
- **Generate content it doesn't have.** If `matter.md` is thin, the email is short and asks broad-status questions. The skill doesn't invent specific questions from nothing.
- **Retry failures.** If Gmail draft creation fails mid-run, the skill logs the failure and continues with markdown. User can retry after fixing auth.
- **Rewrite history.md.** Reads it for context; doesn't modify. (If OC's response surfaces new events, use `/matter-update [slug]` to log them.)
- **Enforce a minimum template.** If the house tone is "one line, first name, done," the draft honors that and skips the bulleted structure. Match `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`.
