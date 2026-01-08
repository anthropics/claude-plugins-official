---
description: Start working on a task or project
allowed-tools: Read, Write, Edit, Glob
argument-hint: <task-or-project>
---

# ClaudeMem Start

Begin working on a task or switch to a project.

## Steps

1. **Parse Argument**: `$ARGUMENTS`
   - If it matches a project name → switch to that project
   - If it matches a task description → find and start that task
   - If no argument → start next pending task in current epic

2. **Find the Task**
   - Read `~/Vault/_manifest.md` for current context
   - Search epic files for matching task
   - Identify the task to start

3. **Update Task Status**
   - In the epic file, change task from `#pending` to `#in-progress`
   - Only one task should be `#in-progress` at a time
   - If another task is in-progress, ask if user wants to switch

4. **Update Manifest**
   - Set `Active Context` → project, epic, task
   - Update timestamp

5. **Load Context**
   - Read project `_index.md`
   - Read current epic file
   - Read relevant sections of PRD if needed
   - Read recent decisions

6. **Announce**

```
STARTING: {Task description}

Project: {project}
Epic: {epic}

Context loaded. Ready to work.

Acceptance criteria:
- {criterion 1}
- {criterion 2}
```

## If No Tasks Found

```
No matching task found for: {argument}

Did you mean:
- {suggestion 1}
- {suggestion 2}

Or use /claudemem plan to create a new project.
```

## Argument

$ARGUMENTS
