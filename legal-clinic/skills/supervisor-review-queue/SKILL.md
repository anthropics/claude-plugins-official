---
name: supervisor-review-queue
description: >
  Professor's review queue — student output waits here for professor approval
  before going to clients or courts. Only active if "formal review queue"
  supervision style was chosen at setup; otherwise dormant. Use when the
  professor wants to see what's waiting for review, approve, edit-then-approve,
  or return an item.
argument-hint: "[--approve ID | --return ID 'note' | --edit ID]"
---

# /supervisor-review-queue

1. Check `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → supervision style. If NOT "formal review queue": explain the clinic is set up for [flags/lighter-touch], no formal queue exists, and how to switch.
2. Use the workflow below.
3. Default: show what's waiting, by urgency, by student.
4. Actions: approve / edit-then-approve / return with note. All logged.

```
/legal-clinic:supervisor-review-queue
```

```
/legal-clinic:supervisor-review-queue --approve Q-003
```

```
/legal-clinic:supervisor-review-queue --return Q-004 "Check the service requirement — local rules changed"
```

---

# Supervisor Review Queue (Optional)

## Purpose

Some clinics want a formal gate: student drafts, professor reviews, output releases. Others find that too prescriptive — they supervise through case rounds and one-on-ones, not through a queue.

**This skill is only active if `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → Supervision style is "formal review queue."** Otherwise it's dormant — the cold-start interview asks the professor which model they want, and this is one of three options.

Whether to use a formal review workflow is genuinely an open question for clinic adoption. It depends on student experience level, caseload, and how the professor already runs supervision. The professor decides at setup and can change it later.

## Load context

`~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → supervision style. If NOT "formal review queue": respond with "The clinic is set up for [flags/lighter-touch] supervision — there's no formal queue. [Professor] reviews through [the clinic's existing structure]. To switch to a formal queue, edit CLAUDE.md → Supervision style."

If formal queue IS enabled → read flag triggers and proceed.

## The queue

Lives at `references/review-queue.yaml`. Each entry:

```yaml
- id: Q-001
  type: "draft"  # intake | draft | memo | status | client-letter
  client: "[name or ID]"
  student: "[name]"
  submitted: [timestamp]
  flags:
    - rule: "Court filing"
      detail: "Eviction answer — always queued"
  content_path: "[path to the document]"
  status: "pending"  # pending | approved | edited-approved | returned
```

## Modes

### What's waiting

```markdown
## Review Queue — [date]

**Pending:** [N] | **Oldest:** [N] hours

### 🔴 Deadline-sensitive
| ID | Type | Client | Student | Why flagged | Waiting |
|---|---|---|---|---|---|

### Standard
[same table]

### By student
[Breakdown — spot patterns: who's queueing a lot, who might need a check-in]
```

### Review an item

Show full content + why it was flagged + student notes.

### Approve / edit-then-approve / return

- **Approve:** Status → approved, student notified, logged.
- **Edit then approve:** Professor edits inline, approved version is the edited one, original preserved in log so student sees the diff (teaching moment).
- **Return:** With a note. Student revises and resubmits.

## Logging

Every action logged. Approval logs are clinic records — they document that a licensed attorney, solicitor, barrister, or other authorised legal professional in the clinic's jurisdiction reviewed student work before it went to a client or court. That matters for the clinic's own compliance and for student evaluation.

## Teaching signal

The queue is also data. Pattern in returns ("Student X keeps missing the service requirement") is a coaching conversation. Pattern in edits ("Everyone's demand letters are too long") is a `/ramp` update for next semester.

## What this skill does NOT do

- **Run unless the professor chose it.** It's one of three supervision models, not the only one.
- **Auto-approve.** The professor approves.
- **Replace the clinic's existing supervision structure.** It's a gate for work product, not a substitute for case rounds, one-on-ones, or watching students in action.
