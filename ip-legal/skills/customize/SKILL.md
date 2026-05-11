---
name: customize
description: >
  Guided customization of your IP practice profile — change one thing without
  re-running the whole cold-start interview. Adjust risk posture, escalation
  contacts, portfolio scope, brand protection strategy, enforcement posture,
  clearance thresholds, OSS review rules, or matter workspace paths. Use when
  the user says "change my [thing]", "update my profile", "edit my config",
  or "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/ip-legal:customize`. They want to change something in their
practice profile — a risk posture, an escalation contact, a portfolio
position, an enforcement tactic — without re-running the whole cold-start
interview and without hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`
   (and `~/.claude/plugins/config/claude-for-legal/company-profile.md` one
   level up). If the plugin config does not exist or still contains
   `[PLACEHOLDER]` values, say:

   > You haven't run setup yet. Run `/ip-legal:cold-start-interview` first —
   > customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Company / who you are** — name, industry, jurisdictions, stage, practice
     setting *(shared across all 12 plugins — changes flow through
     `company-profile.md`)*
   - **IP practice profile** — which IP types are in scope (patent,
     trademark, copyright, trade secret, design), practice orientation
     (prosecution / transactions / enforcement / in-house portfolio)
   - **Risk posture** — conservative / middle / aggressive, what each means
     for clearance thresholds, FTO opinions, and cease-and-desist escalation
   - **People** — IP counsel, outside firms by IP type, enforcement
     escalation chain, invention committee
   - **Portfolio** — patent families, trademark classes, key marks, countries
     of registration, watch services
   - **Brand protection** — enforcement posture on marketplace takedowns,
     domain squatters, parody / fair use calls
   - **Enforcement posture** — when to send C&D vs. cure letter vs. suit;
     escalation triggers by infringement type
   - **Clearance and FTO** — search vendors, clearance confidence thresholds,
     FTO opinion format
   - **OSS review** — license tier policies, ship-blocker licenses, review
     cadence for new dependencies
   - **Workflow** — matter workspaces (matter IDs, family IDs), docket feed,
     invention intake form
   - **Integrations** — patent docket system / trademark office connectors /
     Slack / document storage status, fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Adding a new trademark watch class:* "`/portfolio` will include class
     XX in watch reports and `/infringement-triage` will route class-XX
     findings accordingly."
   - *Enforcement posture aggressive → middle:* "`/cease-desist` will offer
     cure-letter drafts as a first option for ambiguous cases instead of
     going straight to C&D."
   - *New ship-blocker OSS license:* "`/oss-review` will fail reviews that
     include this license rather than warning."

5. **For shared-profile changes** (company name, industry, jurisdictions,
   practice setting, stage): write to
   `~/.claude/plugins/config/claude-for-legal/company-profile.md` and note:

   > This change affects all 12 plugins — any plugin that reads your
   > jurisdiction footprint now sees [new value].

6. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/ip-legal:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "remove" an IP type from
  scope, set it to `[Not currently in scope]` and explain what drops out.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., trademark out of scope + trademark watch service
  configured; or aggressive enforcement posture + "all C&Ds go to outside
  counsel"), flag the tension.
- **Flag guardrail degradation.** The `[review]` flag, source attribution
  tags, and `[verify]` tags on cited authorities are load-bearing — do not
  remove. Clearance confidence is load-bearing on `/clearance` output — do
  not suppress.
- **One change at a time.** Don't re-ask the whole interview.
