---
name: customize
description: >
  Guided customization of your legal clinic profile — change one thing without
  re-running the whole cold-start interview. Adjust clinic profile,
  jurisdiction, supervision style, practice-area templates, semester
  configuration, or output safeguards. Use when the user says "change my
  [thing]", "new semester", "add a practice area", "update my config", or
  "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/legal-clinic:customize`. They (usually the professor, sometimes
a student) want to change something in the clinic profile — a jurisdiction, a
supervision style, a practice-area template, a semester rollover — without
re-running the whole cold-start interview and without hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md`.
   If the plugin config does not exist or still contains `[PLACEHOLDER]`
   values, say:

   > You haven't run setup yet. Run `/legal-clinic:cold-start-interview`
   > first — customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Clinic profile** — clinic name, host school, faculty lead, active
     practice areas, case type limits
   - **Jurisdiction** — primary state, courts, agencies, local rules path
   - **Supervision style** — informal vs. formal review queue; if formal,
     who reviews what before it goes out
   - **Practice-area templates** — which templates are active (immigration,
     housing, small business, family, expungement, etc.) and any local
     overrides
   - **Semester** — current semester, active students, rollover rules,
     handoff memo format
   - **Output safeguards** — plain-language standards for client-facing
     outputs, deadline warning rules, privilege labeling
   - **Seed documents** — clinic handbook, jurisdiction rules, template
     letters, sample memos, form libraries
   - **Outputs** — supervisor guide format, client letter templates, memo
     scaffolds
   - **Workflow** — case directories, deadline tracker location, review
     queue channel
   - **Integrations** — document storage / Slack / court e-filing status,
     fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Adding a new practice area:* "`/intake` will route matters of this
     type through the new template. `/draft`, `/memo`, and `/client-letter`
     will use the practice-area prompts. `/research-start` will add the
     corresponding Westlaw search terms."
   - *Supervision style informal → formal review queue:* "`/queue` becomes
     active — student output will land there for supervisor sign-off before
     it goes to the client."
   - *New semester rollover:* "I'll archive the prior semester's active
     cases, carry forward matters you flag as continuing, and prompt the
     incoming students through `/ramp`."

5. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/legal-clinic:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "drop" a practice area,
  offer to mark it `[Archived]` and explain that archiving keeps case
  history accessible but hides the template from `/intake` routing.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., formal review queue on + informal supervision note;
  or practice area on + no jurisdiction rules configured), flag the
  tension.
- **Flag guardrail degradation.** These are load-bearing and should not be
  removed: the "NOT final work product" framing on `/draft`, plain-language
  standards on client-facing outputs, "does NOT decide case acceptance" on
  `/intake`, "NOT substantive advice" on `/client-letter`, and the
  scaffold-not-analysis framing on `/memo`. These exist because students
  ship work product — if the safeguards go, the risk of student work
  reaching a client without supervisor review goes up. Confirm the
  trade-off with the user, and if they're a student rather than the
  professor, suggest they discuss it with the supervisor first.
- **One change at a time.** Don't re-ask the whole interview.
