---
name: semester-handoff
description: >
  End-of-semester case handoff memos — the mirror of /ramp. Produces per-case
  transition memos and a cohort summary so the departing cohort hands work to
  the incoming cohort cleanly. Reads deadlines, client-comms, and case history.
  Use when the professor or departing students need to wrap up the semester,
  build transition memos, or offboard a graduating/withdrawing student.
argument-hint: "[--semester=YYYY-term (default: current)] [--case=[case_id] (for a single case)]"
---

# /semester-handoff

1. Load `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → clinic profile, semester dates, supervision style.
2. Load `~/.claude/plugins/config/claude-for-legal/legal-clinic/deadlines.yaml` and `~/.claude/plugins/config/claude-for-legal/legal-clinic/client-comms/[case-id]/log.md` per case.
3. Use the workflow below.
4. Take active-case list as input (ask if clinic doesn't have a central list). Map outgoing → incoming owners.
5. Generate per-case handoff memo → `~/.claude/plugins/config/claude-for-legal/legal-clinic/handoffs/[semester]/[case_id].md`.
6. Generate cohort summary → `~/.claude/plugins/config/claude-for-legal/legal-clinic/handoffs/[semester]/_summary.md`.
7. Route per supervision model — formal queue / configurable flags / lighter-touch.

---

# Semester Handoff

## Purpose

Every semester, clinics lose their entire workforce and rebuild. `/ramp` solves half the problem — it onboards the new cohort. This skill solves the other half: it offboards the departing cohort by producing handoff memos that capture what the next student needs to know about every active case.

Without this, case knowledge walks out the door with the student. The new student starts from the case file and intake summary, which is never enough. Two weeks are wasted re-learning the case before the new student can do anything useful. The client experiences the re-learning as a regression — calls go unanswered while the new student catches up, questions already answered get asked again.

## Audience

Professor or departing students. The professor runs it to orchestrate the full cohort offboarding; individual students can run it on their own cases if they're transitioning mid-semester (graduation, withdrawal).

## Load context

- `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → clinic profile, semester, practice areas, supervision style
- `~/.claude/plugins/config/claude-for-legal/legal-clinic/deadlines.yaml` → all active deadlines, grouped by case
- `~/.claude/plugins/config/claude-for-legal/legal-clinic/client-comms/[case-id]/log.md` (per case) → communications history
- Case files / intake summaries the clinic maintains
- Student roster — who owns what going into the handoff

## Workflow

### Step 1: Identify cases and owners

- Pull all active cases (from intake records + `~/.claude/plugins/config/claude-for-legal/legal-clinic/deadlines.yaml` case_ids + client-comms folders)
- For each case: who's the current owner student? Are they staying or leaving?
- Map: outgoing owner → incoming owner (if known; otherwise mark "TBD — professor to assign")

If the clinic doesn't maintain a central active-case list, the skill needs one input: a list of active cases. Ask for it. Don't guess.

### Step 2: Per-case handoff memo

For each case:

```markdown
# Case Handoff — [case name] — [semester ending]

**Case ID:** [case_id]
**Practice area:** [area]
**Outgoing student:** [name]
**Incoming student:** [name or "TBD"]
**Supervising attorney:** [professor]
**Client:** [name or client ID]

---

## Where we are

[One paragraph: current posture. What's been done, what's pending, where the case is heading. If the case is at a natural pause point or between filings, say so.]

## Pending deadlines

*Pulled from `~/.claude/plugins/config/claude-for-legal/legal-clinic/deadlines.yaml`. Incoming student's first job is to confirm these are accurate and owned.*

| Due | Type | Description | Notes |
|---|---|---|---|
| [date] | [type] | [one-line] | [if tight: "URGENT — due within [N] days of semester start"] |

## What's been done

- [Key actions this semester: intake, filings, hearings, major correspondence]
- [Documents produced — with pointers to where they live]

## What's open

- [Decisions pending: e.g., "client hasn't decided whether to accept settlement offer"]
- [Research gaps: e.g., "need to confirm whether [jurisdiction] allows [remedy]"]
- [Open communications: e.g., "awaiting response from opposing counsel's office"]

## Client relationship

- [How often has the student been in touch? Phone, email, in-person?]
- [Any relationship context the next student should know: language preference, trust-building notes, circumstances that affect scheduling]
- [Upcoming planned contact or appointments]

## Documents drafted / filed

*Pointers, not content.*

- [Date] [Document type] — [path or file reference] — [status: filed / drafted / in review queue]

## Communications history summary

*From `~/.claude/plugins/config/claude-for-legal/legal-clinic/client-comms/[case-id]/log.md`. Three-line summary here; incoming student reads the full log.*

[Short summary of recent contact patterns — e.g., "3 phone calls since intake, all in Spanish, client prefers evenings. Last contact: 2026-04-15, confirmed address for hearing notice."]

## Professor's flags for incoming student

*Added by professor review before the handoff memo goes to the incoming student. Could include: "this case has a sensitive family dynamic — read the intake carefully before calling client"; "client has requested all mail go to PO box not home address"; "there's a scope question here we haven't resolved — check with me in week 1."*

[flags, or "none"]

## First-week priorities for incoming student

1. [Specific — e.g., "Call [client] within 48 hours of taking the case. Introduce yourself. Confirm you've received the case file."]
2. [Deadline-driven — e.g., "Answer to eviction complaint is due [date]. Review outgoing student's draft, revise, file."]
3. [Knowledge-gap — e.g., "Read outgoing student's memo on the habitability defense before the 4/28 status conference."]

---

**Handoff prepared by:** [outgoing student]
**Date:** [YYYY-MM-DD]
**Reviewed by:** [supervising attorney, if applicable per supervision model]
```

### Step 3: Cohort summary

After all per-case memos, produce `~/.claude/plugins/config/claude-for-legal/legal-clinic/handoffs/[semester]/_summary.md`:

```markdown
# Cohort Handoff Summary — [semester ending]

**Departing students:** [N]
**Incoming students:** [N]
**Active cases transitioning:** [N]
**Cases closing at semester end (no transition):** [N]

---

## Transitions

| Case | Outgoing | Incoming | Practice area | Urgency |
|---|---|---|---|---|
| [case_id] | [name] | [name or TBD] | [area] | [standard / deadline within 2 weeks / urgent] |

## Unassigned

[cases whose incoming student is "TBD" — professor assigns before next semester]

## Deadlines within 30 days of semester start

[pulled from deadlines.yaml — these are the cases the new cohort hits running]

## Notes for professor

- [Any case that raised concern about student performance, flagged for closer supervision]
- [Any case where the outgoing student is willing to stay on consult — e.g., graduating 3L who wants to mentor the 2L taking over]
- [Patterns across handoffs — e.g., "three of six cases have active deadlines in first 14 days; consider front-loading ramp exercises on those practice areas"]
```

### Step 4: Professor review (if supervision model calls for it)

Closing a case or transitioning it to a new student is a consequential action. The gate is the supervision workflow in `## Supervision style` in `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md`, reinforced by the Part 0 role check confirming a licensed supervising attorney owns the setup. Case-closing memos always get professor sign-off before the case is marked closed in the handoff document, regardless of supervision-style choice.

Per `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` supervision style:

- **Formal review queue:** every handoff memo goes into the review queue before release to the incoming student. Professor approves, edits, or returns.
- **Configurable flags:** memos carry "CHECK WITH [PROFESSOR] BEFORE RELYING" — professor reviews informally, student responsible for checking in.
- **Lighter-touch:** memos carry standard AI-assisted label; professor reviews through existing structure. Case-closing memos still route to the professor before closure.

### Step 5: Hand off

Once reviewed, handoff memos live at `~/.claude/plugins/config/claude-for-legal/legal-clinic/handoffs/[semester]/[case_id].md`. The incoming student reads them during their `/ramp` run at the start of next semester — `/ramp` should surface the memos for cases the new student is assigned.

## Integration

- **`/ramp`:** at the start of next semester, reads `~/.claude/plugins/config/claude-for-legal/legal-clinic/handoffs/[most-recent-semester]/` and surfaces per-case memos for the cases each new student is taking on.
- **`/deadlines`:** feeds the pending-deadlines section of each memo.
- **`/client-comms-log`:** feeds the communications history summary.
- **`/supervisor-review-queue` (if formal review enabled):** handoff memos route here for professor approval.

## What this skill does not do

- **Close cases.** Handoff is for cases transitioning to the next cohort. Cases closing at semester end should get a final internal status memo (`/legal-clinic:status internal`) for the file and be marked closed in the handoff document; the status skill supports `client | internal | court` audiences.
- **Assign incoming students.** Professor assigns. Skill records what the assignment is; doesn't pick.
- **Generate handoffs from scratch without clinic data.** Needs the active case list as input. If the clinic doesn't maintain one, the skill surfaces that gap as a blocker rather than inventing.
- **Replace a conversation.** The written memo is the record. The outgoing student should also have a conversation with the incoming student where feasible — the memo captures facts; a conversation captures judgment and relationship context the memo can't.
