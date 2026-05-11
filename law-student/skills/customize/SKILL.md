---
name: customize
description: >
  Guided customization of your law-student study profile — change one thing
  without re-running the whole cold-start interview. Adjust current classes,
  learning style, outline preferences, bar prep subjects, seed materials,
  or study session cadence. Use when the user says "change my [thing]",
  "add a class", "update my profile", "new semester", or "customize".
argument-hint: "[section name, or describe what you want to change]"
---

# /customize

## When this runs

The user typed `/law-student:customize`. They want to change something in
their study profile — a class, a learning style preference, a bar prep
subject — without re-running the whole cold-start interview and without
hand-editing YAML.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md`.
   If the plugin config does not exist or still contains `[PLACEHOLDER]`
   values, say:

   > You haven't run setup yet. Run `/law-student:cold-start-interview`
   > first — customize is for adjusting a profile you already have.

2. **Show the customizable map.** List what's in the profile, grouped, with a
   one-line summary of the current value:

   - **Student profile** — name, school, year (1L/2L/3L/LLM), jurisdiction
     for bar, enrolled clinics or journals
   - **Current classes** — class name, professor, syllabus path, exam format
     (closed/open book, essay/MBE/mixed), cold-call style
   - **Learning style** — Socratic vs. summary, how much pushback you want,
     whether the plugin rewrites your work or only critiques structurally
   - **Outline preferences** — outline format (IRAC/CREAC/case-briefing
     style), level of rule detail, whether to include policy discussion,
     saved outline templates
   - **Bar prep** — which exam (UBE/state), subjects in rotation, weak-
     subject flagging, MBE vs. essay cadence
   - **Seed materials** — casebook paths, prior outlines, graded essays, old
     exams, MBE sets, syllabi, papers
   - **Study workflow** — session length, flashcard Leitner bucket schedule,
     exam forecast cadence, cold-call prep timing
   - **Integrations** — document storage / flashcard app (if any) status,
     fallbacks

3. **Ask what they want to change.**

   > What would you like to adjust? Pick a section, or describe the change in
   > your own words.

4. **Make the change.** Show the current value, ask for the new value, explain
   what changes downstream, confirm, write it to the config.

   Examples:
   - *Adding a new class:* "`/outline` will scaffold a new outline for this
     class. `/flashcards` will add a new subject bucket. `/cold-call-prep`
     will ask for a seat and a topic when you invoke it for this class."
   - *Learning style Socratic → summary-first:* "`/drill` won't ask you to
     answer first — it'll present the rule and example, then quiz you on
     application."
   - *Adding a bar subject:* "`/bar-prep` will include this subject in
     rotation and weight it higher if you mark it weak."

5. **Close.**

   > Done. Your next output will reflect the change. Anything else? You can
   > run `/law-student:customize` anytime.

## Guardrails

- **Never delete a section.** If the user wants to "drop" a class, offer to
  mark it `[Archived — retain seed materials]` and explain what flashcard
  and outline behavior changes.
- **Flag internal inconsistency.** If the change would make the profile
  inconsistent (e.g., "summary-first" learning style + "maximum pushback"
  Socratic setting), flag the tension.
- **Flag guardrail degradation.** The "no rewriting your writing" rule on
  `/write` and `/irac` is load-bearing — the value of the skill is
  structural feedback, not ghost-writing. If the user asks to turn that off,
  confirm they understand that the plugin will not write their work for
  them.
- **One change at a time.** Don't re-ask the whole interview.
