---
description: Mark current task as complete
allowed-tools: Read, Write, Edit
---

# ClaudeMem Done

Mark the current task as complete and suggest next steps.

## Steps

1. **Read Current State**
   - Read `~/Vault/_manifest.md`
   - Identify active task

2. **If No Active Task**
   ```
   No task currently in progress.

   Use /claudemem start {task} to begin one.
   ```

3. **Mark Complete**
   - Open the epic file
   - Change `- [ ]` to `- [x]` for the task
   - Change `#in-progress` to `#done`
   - Add completion date if desired

4. **Check Epic Status**
   - Count completed vs total tasks
   - If all tasks done, mark epic as `completed`
   - Update project `_index.md` if epic completed

5. **Find Next Task**
   - Look for next `#pending` task in same epic
   - If epic done, look at next epic
   - Consider priority order

6. **Update Manifest**
   - Clear current task (or set to next)
   - Update stats

7. **Announce**

```
COMPLETED: {Task description}

Epic: {epic name}
Progress: {n}/{m} tasks ({percentage}%)

{If epic complete:}
EPIC COMPLETE: {epic name}

NEXT UP:
{Next task description}
Priority: {priority}

Continue? (y) or /claudemem status for overview
```

## If Last Task in Project

```
COMPLETED: {Task description}

PROJECT COMPLETE: {project name}

All epics and tasks finished.

Summary:
- {n} epics completed
- {m} total tasks
- Started: {date}
- Finished: {today}

Use /claudemem save to write final session notes.
```
