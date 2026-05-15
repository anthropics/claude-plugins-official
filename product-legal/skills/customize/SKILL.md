---
name: customize
description: >
  Guided customization of your product counsel practice profile — change one
  thing without re-running the whole cold-start interview. Adjust risk
  calibration, escalation contacts, launch review framework, marketing
  claims posture, or matter workspace paths. Use when the user says
  "change my [thing]", "update my profile", "edit my framework", "retune
  my calibration", or "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/product-legal:customize`. They want to change something
in their product counsel profile — a risk calibration threshold, an
escalation contact, a framework section — without re-running the whole
cold-start interview and without hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md`
   (and `~/.claude/plugins/config/claude-for-legal/company-profile.md` one
   level up). If the plugin config does not exist or still contains
   `[PLACEHOLDER]` values, say:

   > You haven't run setup yet. Run `/product-legal:cold-start-interview`
   > first — customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Company / who you are** — name, industry, jurisdictions, stage, practice
     setting, product surface area *(shared across all 12 plugins — changes
     flow through `company-profile.md`)*
   - **Launch review process** — intake (Jira / Linear / Asana / doc),
     review SLA, launch tiering, PRD location
   - **Review framework** — the categories you review launches against
     (privacy, IP, safety, claims, regulatory, accessibility, security,
     etc.) and the depth you go on each
   - **Risk calibration** — what's P0 blocker / needs a real look / fine at
     your company, with examples that anchor the labels
   - **Marketing claims** — posture on puffery vs. substantiated, comparative
     claims framing, superlatives, house rules for AI-feature claims
   - **People** — product partners by surface, escalation chain (your
     manager, GC, risk committee), marketing counterpart
   - **Workflow** — matter workspaces, launch-radar watcher cadence, launch
     review template
   - **Integrations** — Jira / Linear / Asana / Slack / document storage
     status, fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Risk calibration tightening "fine" → "needs a real look" for a
     pattern:* "`/is-this-a-problem` and `/launch-review` will start flagging this
     pattern. Existing reviews stay as written; re-run if you want the new
     posture applied."
   - *New launch-review category:* "`/launch-review` will add a section for
     this category. `/is-this-a-problem` will pattern-match it in triage."
   - *Marketing claims posture tightening:* "`/marketing-claims-review` will flag more
     language as needing substantiation or reframing."

5. **For shared-profile changes** (company name, industry, jurisdictions,
   practice setting, stage): write to
   `~/.claude/plugins/config/claude-for-legal/company-profile.md` and note:

   > This change affects all 12 plugins — any plugin that reads your
   > jurisdiction footprint now sees [new value].

6. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/product-legal:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "remove" a review
  category, offer to mark it `[Not in scope — route elsewhere]` and name
  the plugin / team that picks it up.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., AI-feature claims scrutiny on + no AI policy
  commitments set in `/ai-governance-legal`; or "fast SLA" + "every
  launch requires GC sign-off"), flag the tension.
- **Flag guardrail degradation.** The `[review]` flag, source attribution
  tags, and `[verify]` tags on cited regulations are load-bearing — do not
  remove. The substantiation requirement on claims is the thing
  `/marketing-claims-review` exists for; weakening it defeats the skill.
- **One change at a time.** Don't re-ask the whole interview.
