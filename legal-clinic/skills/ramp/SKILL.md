---
name: ramp
description: >
  Student semester onboarding — clinic procedures, tool walkthrough, practice
  exercises before real cases. Reads the handbook the professor uploaded at
  setup and teaches it interactively. Use when a new clinic student says
  "onboard me", "I'm new to the clinic", "getting started", or at the start of
  each semester; pass --card for the one-page reference.
argument-hint: "[--card for the one-page reference]"
---

# /ramp

1. Check `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` is set up. If placeholders: "Ask [professor] to run `/legal-clinic:cold-start-interview` first."
2. Use the walkthrough below.
3. Walk through: clinic context (from handbook) → commands → practice exercises (fake intake, practice draft, research roadmap) → verification habits.
4. `--card`: generate the one-page reference card.

```
/legal-clinic:ramp
```

```
/legal-clinic:ramp --card
```

---

# Ramp: Semester Onboarding

## Purpose

Every semester, the clinic loses its entire workforce and rebuilds from scratch. New students need to learn procedures, case management, filing conventions, and practice-area basics before they're useful. Traditionally that takes weeks of reading PDFs and asking the professor the same questions every semester.

This skill is the guided walkthrough. It reads what the professor uploaded during cold-start — the handbook, the filing guides, the local rules — and teaches it interactively, with practice exercises so students try the tools in a low-stakes setting before a real client is on the line.

**Audience: students.** Professors don't run this (they run `/cold-start-interview`).

## Load context

`~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → clinic profile, practice areas, jurisdiction, handbook path, supervision style, practice-area templates.

If that file is missing or still has placeholders: "The clinic hasn't been set up yet. Ask [supervising professor] to run `/cold-start-interview` first."

## The walkthrough

### Opening

> Welcome to [clinic name]. I'm going to walk you through how this clinic works and how to use these tools — about twenty minutes, and you can pause anytime. By the end you'll have run a practice intake, drafted a practice document, and you'll know what to do when you get your first real case.
>
> One thing up front: everything I generate is a starting point, not a final answer. You do the analysis. [Professor] reviews your work [per supervision style]. I handle the formatting and the first draft so you spend your time on the lawyering, not on writing "Dear Judge" for the twentieth time.

### Part 1: This clinic (5 min)

Read from `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` and the ingested handbook. Cover, interactively:

- **Practice areas** — what the clinic handles, what it doesn't (and where to refer if someone walks in with an out-of-scope issue)
- **Clients** — who they are, what they're facing, languages
- **Jurisdiction** — which courts, which judges, what the local quirks are
- **Case management** — how cases are tracked, where files live, what a well-documented case looks like
- **Supervision** — how review works in this clinic (per the supervision style in CLAUDE.md). Be specific: "Before anything goes to a client or a court, [it goes in the review queue / you check with Professor X / etc.]"

Don't lecture — check understanding. "So if a client comes in with an eviction notice but also mentions they're undocumented, what do you do?" (Answer: both issues get noted in intake; the immigration question may need a referral or a flag to the professor, depending on the clinic's scope.)

### Part 2: The commands (5 min)

Walk through each command the student will actually use:

| Command | When you use it | What you get |
|---|---|---|
| `/client-intake` | Client interview | Formatted case summary with issues spotted, conflict flags, triage |
| `/draft [doc type]` | Need a first draft of a common document | Practice-area template filled from case notes — *starting point, not final* |
| `/memo` | Need to analyze a case internally | IRAC-format memo with research gaps flagged |
| `/research-start [issue]` | Starting legal research | Roadmap: statutes to check, case law areas, search terms — *leads, not authoritative cites* |
| `/status [audience]` | Updating someone on a case | Summary tailored to client / professor / court |
| `/client-letter [type]` | Routine correspondence | Appointment confirm, doc request, status update from templates |

For each: what it does, what it explicitly doesn't do, what the student verifies before relying on it.

### Part 3: Practice exercises (8-10 min)

**Low-stakes. Fake client. Real tools.**

**Exercise 1 — Practice intake:**
> Here's a fake client scenario: [practice-area-appropriate hypo — e.g., for a housing clinic, "Maria got a 3-day notice to quit last Tuesday. She's two months behind on rent after losing her job. The apartment has had a broken heater since November. She has two kids."]
>
> Run `/client-intake` and interview me as if I'm Maria. I'll answer as Maria would. At the end, look at the case summary it produces — what issues did it spot? Did it catch the habitability defense?

Debrief: what the intake caught, what the *student* should have probed deeper on, what gets flagged for the professor.

**Exercise 2 — Practice draft:**
> Using Maria's intake, run `/draft eviction-answer`. You'll get a first draft.
>
> Read it. What's right about it? What's wrong? What would you change before showing it to [Professor]?

The point: the draft is competent but not final. The student learns to read critically, not accept.

**Exercise 3 — Research roadmap:**
> Run `/research-start "habitability defense to eviction in [state]"`. You'll get a roadmap — statutes, case law areas, search terms.
>
> None of those citations are verified. That's on purpose. Pick one statute from the roadmap and tell me how you'd verify it's current and applies here.

The point: `/research-start` is a starting place, not a citation. The student still does the research.

### Part 4: Verification habits (2 min)

The habits that matter:

- **Every output is a starting point.** If it went to a client or a court without you reading it critically, something went wrong.
- **Verify every citation** before it goes in anything. `/research-start` gives leads, not authorities.
- **Check jurisdiction-specific details.** The plugin knows your state from setup, but local court quirks change — double-check against current local rules.
- **When uncertain, it says so.** If an output has a `[UNCERTAIN: ...]` flag, that's a prompt to research or ask the professor, not to delete the flag and move on.
- **[Supervision reminder per CLAUDE.md style]** — what gets reviewed before it goes out, and how.

### Closing

> That's it. You've run an intake, drafted a document, and built a research roadmap. Your first real case will feel similar, except the client is real and the professor is reading your work.
>
> The one-page reference card: `/ramp --card`

## `/ramp --card`

Generate the one-page student reference card per the one-page card spec. Contents:

- The commands (table from Part 2, condensed)
- What Claude can help with / what it can't (starting points yes, final work product no, authoritative citations no)
- Verification habits (the bullets from Part 4)
- Who to ask when stuck (professor name from CLAUDE.md)

Printable. One page. Hand it out on day one.

## What this skill does NOT do

- Replace the professor's orientation. It covers procedures and tools; the professor covers judgment, strategy, and the things you only learn by watching someone good do it.
- Teach substantive law. Practice-area *orientation*, not a doctrinal course.
- Certify the student as ready. The professor decides when a student takes a real case.
