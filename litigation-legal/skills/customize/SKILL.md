---
name: customize
description: >
  Guided customization of your litigation practice profile — change one thing
  without re-running the whole cold-start interview. Adjust practice role,
  side (plaintiff / defense / mixed), risk calibration, landscape, house
  style, escalation contacts, severity vocabulary, or matter workspace
  paths. Use when the user says "change my [thing]", "update my profile",
  "edit my config", or "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/litigation-legal:customize`. They want to change something
in their litigation profile — a risk calibration, a house style rule, an
escalation contact, a landscape note — without re-running the whole
cold-start interview and without hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`
   (and `~/.claude/plugins/config/claude-for-legal/company-profile.md` one
   level up). If the plugin config does not exist or still contains
   `[PLACEHOLDER]` values, say:

   > You haven't run setup yet. Run `/litigation-legal:cold-start-interview`
   > first — customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Company / who you are** — name, industry, jurisdictions, stage, practice
     setting *(shared across all 12 plugins — changes flow through
     `company-profile.md`)*
   - **Practice role** — in-house counsel / outside counsel / solo / clinic
   - **Side** — plaintiff / defense / mixed, and any posture nuances (class
     action defense, regulatory enforcement defense, commercial
     plaintiff, etc.)
   - **Risk calibration** — what counts as high / medium / low risk on an
     inbound demand, subpoena, or new matter; escalation triggers
   - **Landscape** — regular adversaries, friendly and unfriendly venues,
     judges to know, standing OC relationships
   - **House style** — brief style, declaration format, demand letter
     template, deposition outline structure, legal hold template
   - **Severity vocabulary map** — how you translate severity labels across
     client / internal / court-facing outputs
   - **People** — matter leads, in-house team, outside counsel by matter
     type, escalation chain
   - **Workflow** — matter workspaces, portfolio log, OC status cadence,
     legal hold refresh cadence
   - **Integrations** — document storage / e-filing / calendar / Slack
     status, fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Side mixed → defense-only:* "`/new-matter` intake will stop asking the
     plaintiff-side questions. `/demand-draft` will still work for
     defense-side pre-suit demands but the starting frame will be different."
   - *Risk calibration tightening high-risk threshold:* "More inbound
     demands and subpoenas will route through `/matter-briefing` and
     `/oc-status`."
   - *New standing OC for IP matters:* "`/oc-status` will include this firm
     in weekly sweeps for IP-tagged matters."

5. **For shared-profile changes** (company name, industry, jurisdictions,
   practice setting, stage): write to
   `~/.claude/plugins/config/claude-for-legal/company-profile.md` and note:

   > This change affects all 12 plugins — any plugin that reads your
   > jurisdiction footprint now sees [new value].

6. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/litigation-legal:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "remove" a matter type
  from scope, offer to mark it `[Not currently handled]` and explain what
  intake routing changes.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., plaintiff-only side + defense-only OC roster; or
  "high volume" portfolio + no matter workspaces configured), flag the
  tension.
- **Flag guardrail degradation.** The FRE 408 / privilege gate on
  `/demand-draft`, the privilege header on matter outputs, source
  attribution tags, and `[verify]` tags on cited authorities are load-
  bearing — do not remove. The `[review]` flag and the "do not file
  without attorney review" framing are load-bearing.
- **One change at a time.** Don't re-ask the whole interview.
