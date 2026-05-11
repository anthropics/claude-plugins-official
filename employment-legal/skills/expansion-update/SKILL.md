---
name: expansion-update
description: >
  Update the status of an in-progress international expansion project —
  recalculates what is now unblocked, flags anything overdue, and surfaces
  the next priorities. Use when work has happened since the last session and
  the expansion tracker needs to reflect the current state.
argument-hint: "[country name]"
---

# /expansion-update

Returns to an open expansion tracker and updates item status based on what
has happened since the last session. Recalculates what is now unblocked,
flags anything overdue, and surfaces the next priorities.

## Instructions

1. Load `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`.

2. Identify the tracker file: `~/.claude/plugins/config/claude-for-legal/employment-legal/expansion-[slug].yaml`. If it doesn't
   exist, respond: "No expansion tracker found for [country]. Run
   `/employment-legal:expansion-kickoff [country]` to start one."

3. Read the tracker. Show the current state:

```
[Country] Expansion — last updated [date]
Open: [N] | In progress: [N] | Done: [N] | Blocked: [N]

Next priorities (open items with earliest due dates or highest-dependency):
  [item] — owner: [owner]
  [item] — owner: [owner]
  [item] — owner: [owner]
```

4. Ask for updates in a single prompt — do not ask about each item one by one:

   > Which items have moved since we last looked? Tell me what's changed
   > (e.g., "EOR decision made — going with Deel", "outside counsel engaged —
   > call scheduled for Thursday", "PE analysis still open, waiting on tax").
   > You can also add new items or change due dates.

5. Apply updates to the tracker file. For any item newly marked `done`,
   check whether it unblocks other items and flag those as now actionable.

6. If any item has a due date that has passed and is still `open` or
   `in-progress`, flag it:

```
⚠️ Overdue: [item] — was due [date], owner: [owner]
```

7. Write the updated tracker. Confirm:

```
Tracker updated — [N] items closed, [N] still open.
Next priority: [top open item].
```

## Examples

```
/employment-legal:expansion-update Germany
```

```
/employment-legal:expansion-update
(will ask which country if multiple trackers exist)
```

> Detailed tracker schema, item-status rules, and dependency logic live in the
> `international-expansion` reference skill — load it before doing substantive
> work.
