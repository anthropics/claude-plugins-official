---
name: log-leave
description: >
  Add a new leave to the leave register with the minimum information needed to
  start tracking deadlines. Use when an employee goes on leave and you want the
  tracker to watch designation, certification, and exhaustion clocks from day
  one.
argument-hint: "[describe the leave — employee/role, type, jurisdiction, start date]"
---

# /log-leave

Adds a new leave entry to `~/.claude/plugins/config/claude-for-legal/employment-legal/leave-register.yaml` with the minimum
information needed to start tracking deadlines. Use when an employee goes on
leave and you want the tracker to watch the clocks from day one.

## Instructions

1. Read `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdiction table and Systems section.

2. Ask all of the following in a single prompt — do not drip them one at a time:

   > A few quick questions to set up leave tracking:
   >
   > - Employee name or role (anonymized is fine)
   > - Where do they work? (State — this determines which rules apply)
   > - Leave type: FMLA / state leave (which state) / USERRA / ADA accommodation
   > - Leave start date
   > - Is this intermittent leave?
   > - Expected return date (if known — leave blank if not)
   > - Has the designation notice been sent? If yes, when?
   > - Has medical certification been requested? If yes, when?

3. Using the jurisdiction table in `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`, look up the applicable leave
   entitlement (hours/weeks) for this leave type in this jurisdiction.

4. Compute the first upcoming deadline based on the information provided:
   - Designation not yet sent → deadline is 5 business days from leave start
   - Med cert requested but not received → deadline is 15 days from request date
   - Both sent and received → next deadline is at 75% exhaustion

5. Write a new entry to `~/.claude/plugins/config/claude-for-legal/employment-legal/leave-register.yaml` using the leave register
   format from the leave-tracker agent. If the file doesn't exist, create it.

6. Confirm with a single line:
   > "Logged. [Employee/Role] — [Leave type] — [Jurisdiction] — started [date].
   > First deadline: [what it is and when]. Leave tracker will alert automatically."

## Examples

```
/employment-legal:log-leave
```

```
/employment-legal:log-leave
Sarah (Sr. Engineer, works in California) just started FMLA today for a
serious health condition. Intermittent. No designation sent yet.
```
