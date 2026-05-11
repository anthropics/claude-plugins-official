# client-comms/ — per-case communication logs

One folder per case. Inside, a running `log.md` tracking every client contact — incoming and outgoing, across phone, email, text, letter, and in-person meetings. Produced and appended by `/legal-clinic:client-comms-log`.

## Layout

```
client-comms/
├── _README.md                     # this file
└── [case-id]/
    └── log.md                     # append-only running log
```

## Slug

Match the case's ID used elsewhere (intake record, `deadlines.yaml` `case_id`). One case = one folder.

## Why this exists

- **Malpractice defense** — "we communicated X on date Y" needs a record.
- **Continuity at handoff** — the incoming student can read the log and know the client's story without re-interviewing.
- **Pattern visibility** — five voicemails unreturned over six weeks is a supervision flag.
- **Client file-retention** — law school clinics have retention obligations; this is part of the complete file.

## What the log entries look like

```markdown
## [YYYY-MM-DD HH:MM] — [in / out] — [medium]

**Who (student):** [name]
**Who (client side):** [client name, or third-party if call from opposing counsel/etc]
**Duration / length:** [10 min call | 3-paragraph email | 2-page letter]

**Summary:**
[What happened, 2-4 sentences. Substance plus tone where it matters.]

**Action items:**
- [Item the student owes the client, with deadline]
- [Item the client owes the student, with expected timing]

**Follow-up due:** [date if applicable]

**Notes:**
[Anything that matters but doesn't fit above — language used, family dynamic observed, client anxiety level]
```

## What this folder does NOT contain

- Substantive case analysis (that's in the intake / memo / status files)
- Drafts of documents (those are in separate case folders)
- Privileged attorney-only notes (those stay in whatever the clinic uses for internal case notes)

The comms log is factual record of contact, not legal work product. Keep substance in the log; keep strategy and analysis elsewhere.

## Retention

Append-only. Never edit past entries — if something was wrong or needs clarification, add a new entry referencing the old one. The record of what was said and when is part of the client file; rewriting history defeats the purpose.
