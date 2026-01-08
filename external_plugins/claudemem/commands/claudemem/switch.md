---
description: Switch to a different project
allowed-tools: Read, Write, Edit, Glob
argument-hint: <project-name>
---

# ClaudeMem Switch

Switch active context to a different project.

## Steps

1. **Check Current State**
   - Read `~/Vault/_manifest.md`
   - If task is in-progress, warn user

2. **Offer to Save**
   If there's an active session with work:
   ```
   You have work in progress on {current project}.

   Save session notes before switching? (y/n)
   ```

3. **Find Target Project**
   - Parse argument: `$ARGUMENTS`
   - Search `~/Vault/Projects/` for matching project
   - Match by id or name (fuzzy)

4. **If Project Not Found**
   ```
   Project not found: {argument}

   Available projects:
   - {project 1} ({status})
   - {project 2} ({status})

   Or use /claudemem plan to create a new one.
   ```

5. **Load New Project**
   - Read `Projects/{id}/_index.md`
   - Find current/next epic and task
   - Update manifest Active Context

6. **Announce**

```
SWITCHED TO: {Project Name}

Status: {status}
Current Epic: {epic name}
Current Task: {task or "None - pick one to start"}

Progress: {n}/{m} tasks complete

Use /claudemem start {task} to begin.
```

## If Switching to Paused Project

```
RESUMING: {Project Name}

Last worked: {date}
Left off at: {task description}

Session notes from last time:
{Brief from last session}

Continue with {task}? (y) or /claudemem status for full overview
```

## Argument

$ARGUMENTS
