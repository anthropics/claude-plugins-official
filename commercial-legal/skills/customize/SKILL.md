---
name: customize
description: >
  Guided customization of your commercial contracts practice profile — change
  one thing without re-running the whole cold-start interview. Adjust risk
  posture, escalation contacts, playbook positions, NDA triage preferences,
  house style, review preferences, or matter workspace paths. Use when the
  user says "change my [thing]", "update my profile", "edit my playbook",
  "tune my config", or "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/commercial-legal:customize`. They want to change something
in their practice profile — a risk posture, an escalation contact, a playbook
position, a jurisdiction, an output format — without re-running the whole
cold-start interview and without hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`
   (and `~/.claude/plugins/config/claude-for-legal/company-profile.md` one
   level up). If the plugin config does not exist or still contains
   `[PLACEHOLDER]` values, say:

   > You haven't run setup yet. Run `/commercial-legal:cold-start-interview`
   > first — customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Company / who you are** — name, industry, jurisdictions, stage, practice
     setting, sales-side vs. purchasing-side orientation *(shared across all
     12 plugins — changes flow through `company-profile.md`)*
   - **Risk posture** — conservative / middle / aggressive, what each means
     for fallback positions and escalation triggers
   - **People** — escalation chain, approvers by dollar threshold and by
     clause type
   - **Playbook positions** — the substantive contract positions: liability
     caps, indemnity scope, IP ownership, data protection, termination,
     auto-renewal, price escalation, and the fallbacks for each
   - **NDA triage preferences** — what green / yellow / red looks like for
     inbound NDAs
   - **Review preferences** — redline style, explanation depth, whether to
     produce a stakeholder summary by default
   - **House style** — document format, signature block, renewal-alert
     channel, deviation-log format
   - **Workflow** — matter workspace paths, intake path, renewal watcher
     cadence
   - **Integrations** — Ironclad / DocuSign / Slack / document storage
     status, fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Liability cap fallback 12 months → 6 months:* "`/review` will now flag
     anything above 6 months as a deviation; existing deal-debrief entries
     stay as logged."
   - *New escalation approver:* "Any redline exceeding your own authority
     will now route to this approver — `/escalation-flagger` will include them by
     default for the matching risk band."
   - *Risk posture middle → aggressive:* "I'll accept more vendor-friendly
     positions without flagging them and shift the `[review]` bar higher."

5. **For shared-profile changes** (company name, industry, jurisdictions,
   practice setting, stage): write to
   `~/.claude/plugins/config/claude-for-legal/company-profile.md` and note:

   > This change affects all 12 plugins — any plugin that reads your
   > jurisdiction footprint now sees [new value].

6. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/commercial-legal:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "remove" something, set it
  to `[Not configured]` and explain what that means for the plugin's behavior.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., risk posture aggressive + "every redline needs GC
  approval"; or "sales-side" + a purchasing-side playbook position), flag the
  tension and ask which one they want.
- **Flag guardrail degradation.** If the user asks to turn off a guardrail
  (drop the `[review]` flag, skip the privilege header, remove `[verify]`
  tags), explain what the guardrail protects against and confirm they
  understand the trade-off. The `[review]` flag, source attribution tags, and
  `[verify]` tags on cited statutes are load-bearing and should not be
  removed.
- **One change at a time.** Don't re-ask the whole interview.
