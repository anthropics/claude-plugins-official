---
description: Show current project, epic, and task status
allowed-tools: Read, Glob
---

# ClaudeMem Status

Show the current workspace state.

## Steps

1. Read `~/Vault/_manifest.md`
2. Parse the Active Context section
3. If active project exists, read `~/Vault/Projects/{project}/_index.md`
4. If active epic exists, read the epic file
5. Display formatted status

## Output Format

### If Active Context Exists

```
PROJECT: {Project Name}
Status: {status} | Priority: {priority}

EPIC: {Epic Name}
Progress: {completed}/{total} tasks ({percentage}%)

CURRENT TASK:
{Task description}
Priority: {priority}
Status: {status}

NEXT UP:
1. {Next task}
2. {Following task}

BLOCKERS:
{List blockers or "None"}

SESSION:
Started: {time ago}
```

### If No Active Context

```
NO ACTIVE PROJECT

Recent Activity:
{List recent sessions}

Available Projects:
{List projects with status}

Use /claudemem start {project} to begin.
```
