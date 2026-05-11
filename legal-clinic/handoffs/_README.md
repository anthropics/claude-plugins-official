# handoffs/ — end-of-semester case handoff memos

Per-semester folder with one handoff memo per active case. Produced by `/legal-clinic:semester-handoff` at end of semester. Read by incoming students during `/ramp` for the cases they inherit.

## Layout

```
handoffs/
├── _README.md                             # this file
└── [YYYY-semester]/                       # e.g., 2026-spring, 2026-fall
    ├── _summary.md                        # cross-case rollup: what transitions, who to whom
    ├── [case-id].md                       # one per active case
    └── ...
```

## Slug / folder conventions

Semester folder: `[year]-[spring|summer|fall]`. Examples:
- `2026-spring`
- `2026-summer`
- `2026-fall`

Case memo: use the case_id (from `deadlines.yaml` or the intake record). Consistent with other files per case.

## What a handoff memo contains

- Case summary (facts, practice area, current posture)
- Outgoing student's name + relationship built with client (if relevant)
- Pending deadlines (pulled from `deadlines.yaml`)
- Open issues / decisions pending
- Communications history (pulled from `client-comms/[case-id]/log.md`)
- Documents drafted / filed to date (pointers to case files)
- What the incoming student needs to know / do first
- Professor's flags for incoming student (if any)

## Workflow

1. `/legal-clinic:semester-handoff` is run by the professor (or by departing students on their own cases) ~1-2 weeks before semester ends.
2. Outputs per-case memos + summary.
3. Incoming cohort runs `/legal-clinic:ramp` at start of next semester; `/ramp` surfaces the handoff memos for cases each new student is assigned.

## Retention

Handoff memos stay on disk. Historical handoffs are useful for the clinic's own record of case transitions and for students looking at how a case evolved across semesters.
