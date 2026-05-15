---
name: customize
description: >
  Guided customization of your privacy practice profile — change one thing
  without re-running the whole cold-start interview. Adjust risk posture,
  escalation contacts, DPA playbook, privacy policy commitments, PIA house
  style, DSAR process, or matter workspace paths. Use when the user says
  "change my [thing]", "update my profile", "edit my playbook", or
  "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/privacy-legal:customize`. They want to change something in
their privacy profile — a risk posture, an escalation contact, a DPA
position, a PIA section, a DSAR timeline — without re-running the whole
cold-start interview and without hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`
   (and `~/.claude/plugins/config/claude-for-legal/company-profile.md` one
   level up). If the plugin config does not exist or still contains
   `[PLACEHOLDER]` values, say:

   > You haven't run setup yet. Run `/privacy-legal:cold-start-interview`
   > first — customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Company / who you are** — name, industry, jurisdictions, stage, practice
     setting, controller vs. processor orientation *(shared across all 12
     plugins — changes flow through `company-profile.md`)*
   - **Risk posture** — conservative / middle / aggressive, what each means
     for processor obligations, cross-border transfers, and retention
   - **People** — DPO, privacy team, engineering liaison, outside counsel,
     escalation chain
   - **DPA playbook** — positions on sub-processor notice, deletion, audit,
     liability, international transfers, SCCs — as processor and as
     controller
   - **Privacy policy commitments** — the commitments your privacy notice
     has made that `/policy-monitor` watches practice against
   - **PIA house style** — section order, risk scoring, stakeholder framing,
     when DPIA triggers apply
   - **DSAR process** — verification, statutory timelines per regime,
     exemption application, template response structure
   - **Workflow** — intake path, matter workspaces, policy-monitor sweep
     cadence
   - **Integrations** — document storage / privacy tool / Slack status,
     fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Sub-processor notice 30 days → 14 days:* "`/dpa-review` will now flag
     anything shorter than 14 days as a deviation. Existing DPAs stay as
     logged."
   - *New DSAR exemption in the playbook:* "`/dsar-response` will surface this
     exemption in the assessment step where the facts match."
   - *Risk posture middle → conservative:* "I'll flag more activities for
     PIA escalation, recommend stricter SCC clauses, and be more
     conservative on retention."

5. **For shared-profile changes** (company name, industry, jurisdictions,
   practice setting, stage): write to
   `~/.claude/plugins/config/claude-for-legal/company-profile.md` and note:

   > This change affects all 12 plugins — any plugin that reads your
   > jurisdiction footprint now sees [new value].

6. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/privacy-legal:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "remove" a regime from
  scope, offer to mark it `[Not currently in scope]` and explain what
  flagging drops.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., "processor only" + controller playbook positions
  active; or "no EU nexus" + SCCs in the default template), flag the
  tension.
- **Flag guardrail degradation.** The `[review]` flag, source attribution
  tags, `[verify]` tags on cited regulations, and the DPIA-trigger
  mandatory-check on `/use-case-triage` are load-bearing — do not remove. If
  statutory DSAR timelines are adjusted below the regulatory minimum,
  refuse and explain why.
- **One change at a time.** Don't re-ask the whole interview.
