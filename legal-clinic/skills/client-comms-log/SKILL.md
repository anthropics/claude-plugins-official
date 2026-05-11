---
name: client-comms-log
description: >
  Log a client communication — call, email, text, letter, in-person, voicemail.
  Append-only per-case record with dated entries, direction, medium, summary,
  action items. Works alongside /client-letter and /status client. Use when
  logging a call or client email, reviewing a communication log, or asking
  "what did we tell [client] last time".
argument-hint: "[case-id] [--add (default) | --read | --summary | --patterns]"
---

# /client-comms-log

1. Use the workflow below.
2. Require case-id (prompt if not provided).
3. Route by flag:
   - `--add` (default): capture direction, medium, student, summary, action items, follow-up due. Confirm with user. Append (prepend most-recent-first) to `~/.claude/plugins/config/claude-for-legal/legal-clinic/client-comms/[case-id]/log.md`.
   - `--read`: show the most recent N entries.
   - `--summary`: one-paragraph condensed read.
   - `--patterns`: scan for unanswered comms, missed follow-ups, language gaps, tone shifts, contact gaps. Supervision-oriented.
4. Integration: offer `/legal-clinic:deadlines --add` if the log establishes a deadline; route to `/legal-clinic:semester-handoff` via `--summary` when relevant.

---

# Client Communications Log

## Purpose

Four reasons to keep this log:

1. **Malpractice defense.** If a client claims "no one ever told me [X]," a dated entry showing otherwise is the answer. Clinical professors carry professional liability on student work; contemporaneous records protect them.
2. **Continuity at handoff.** The next semester's student takes over and reads the log; they don't re-ask the client questions already answered.
3. **Supervision visibility.** Five unreturned voicemails over six weeks is a pattern. The log makes patterns visible that individual students might not flag on their own.
4. **File retention.** Law school clinics have obligations to maintain complete client files. Communication history is part of that.

Light. Append-only. The student's job is to write a two-sentence entry after every contact; the skill formats it and appends.

## Load context

- `~/.claude/plugins/config/claude-for-legal/legal-clinic/client-comms/[case-id]/log.md` (if exists) — append target
- `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → not heavily read; this skill is case-scoped

## Modes

Flag: `--add | --read | --summary | --patterns` (default: add)

### `--add` (default) — log a new entry

**Inputs:**
- Case ID (required — which case)
- Date + time (default: now)
- Direction: `in` (client → clinic) | `out` (clinic → client)
- Medium: `call | email | text | letter | in-person | video | voicemail-left | voicemail-received`
- Who (student): name
- Who (client side): client name, or "third-party: [description]" if from opposing counsel, family member, etc.
- Duration / length (e.g., "10 min call", "3-paragraph email", "45 min in-person meeting")
- Summary: 2-4 sentences. What happened, what was substantive.
- Action items:
  - What the student owes the client (with deadline)
  - What the client owes the student (with expected timing)
- Follow-up due: date if applicable
- Notes: anything that matters but doesn't fit above — language used, emotional tone, family dynamic observed

**Before writing:** show the user the formatted entry and ask for confirmation. Clinic records should be reviewed before they're written, not after.

**Append** to `~/.claude/plugins/config/claude-for-legal/legal-clinic/client-comms/[case-id]/log.md`. If the log doesn't exist, create it with a header:

```markdown
# Communications Log — [case name]

**Case ID:** [case-id]
**Client:** [name]
**Opened:** [YYYY-MM-DD]

Append-only. Most recent at top.

---
```

Then prepend new entries at the top (most recent first).

### `--read` — show recent entries

Print the most recent N entries (default 5). Useful when picking up a case mid-semester or before a client call.

### `--summary` — condensed read

Produce a one-paragraph summary of the log — most recent contact, total entries, common medium, any open action items from the student side, any unanswered communications. Feeds `/semester-handoff` and `/status`.

### `--patterns` — flag concerns across the log

Scan for:

- **Unanswered communications from client.** Client called or emailed N times without a response entry.
- **Missed follow-up.** Action item with follow-up due date, and no later entry resolving it.
- **Language / accommodation issues.** Client language noted as non-English; check whether outgoing communications have been in that language.
- **Escalation patterns.** Client tone shifting (frustrated / distressed) across entries.
- **Gaps.** Long stretches with no contact on an active case.

This is a supervision tool. Clinical professors running `--patterns` across their cases see which students might need support.

## Integration

- **`/client-letter`:** after generating and sending a letter, offer to log it as an outgoing comm.
- **`/status client`:** when producing a client-facing status summary, offer to log it (often these summaries go to clients).
- **`/client-intake`:** first entry in every new case's log is the intake contact.
- **`/semester-handoff`:** handoff memos read `--summary` for each case to populate the communications-history section.
- **`/deadlines`:** if a communication established a deadline ("client said they need to respond by Friday"), offer to `/deadlines --add`.

## What this skill does not do

- **Store substantive legal analysis.** That lives in intake, memo, and status files. The log is communication record — facts of contact, not legal strategy.
- **Auto-log from outside systems.** If the clinic uses a case management system (Clio), an integration could pull call logs and emails automatically. That's a future add; not v1.
- **Edit past entries.** Append-only. If an entry is wrong, write a new entry referencing and correcting it. The integrity of the log depends on not rewriting history.
- **Enforce log discipline.** If a student doesn't log a call, the skill can't know. Log hygiene is a clinic-culture problem; the skill just makes logging easy.
- **Handle privileged or attorney-only notes.** If the student needs to record strategic thinking, that goes in the case's internal analysis file, not the comms log.
