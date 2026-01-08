# Commands Reference

## /claudemem

Smart dispatcher that reads context and suggests appropriate action.

**Usage**: `/claudemem`

**Behavior**:
- No active project → Shows dashboard
- Active project → Shows status, offers to continue
- After project discussion → Offers to plan

---

## /claudemem:setup

Initialize the vault structure. Run once after installing the plugin.

**Usage**: `/claudemem:setup`

**Creates**:
- `~/Vault/_manifest.md`
- `~/Vault/.schemas/` (project, epic, session schemas)
- `~/Vault/Projects/`
- `~/Vault/Sessions/`

---

## /claudemem:status

Shows current workspace state.

**Usage**: `/claudemem:status`

**Output (with active project)**:
```
PROJECT: My Project
Status: active | Priority: P0

EPIC: 01-foundation
Progress: 3/8 tasks (37%)

CURRENT TASK:
Set up database schema
Priority: P0 | Status: in-progress

NEXT UP:
1. Implement auth flow
2. Create API routes

BLOCKERS: None
```

**Output (no active project)**:
```
NO ACTIVE PROJECT

Recent Sessions:
- 2024-01-08: my-project - Completed auth setup

Available Projects:
- my-project (active)
- other-project (paused)
```

---

## /claudemem:plan

Creates a project from the current conversation.

**Usage**: `/claudemem:plan [project-name]`

**What it creates**:
- `Projects/{id}/_index.md` - Project overview
- `Projects/{id}/PRD.md` - Requirements document
- `Projects/{id}/Decisions.md` - Architecture decisions
- `Projects/{id}/Epics/*.md` - Epics with tasks

**Flow**:
1. Analyzes conversation for requirements
2. Generates project structure
3. Creates epics and tasks
4. Updates manifest
5. Announces: "Created {project}: {n} epics, {m} tasks"

---

## /claudemem:start

Begins working on a task.

**Usage**: `/claudemem:start [task-description]`

**Behavior**:
- No argument → Starts next pending task in current epic
- With argument → Finds matching task and starts it

**Actions**:
1. Marks task as `#in-progress`
2. Updates manifest active context
3. Loads relevant project context
4. Announces task and acceptance criteria

---

## /claudemem:done

Marks current task as complete.

**Usage**: `/claudemem:done`

**Actions**:
1. Marks task as `[x]` and `#done`
2. Updates epic progress
3. If epic complete, marks epic done
4. Suggests next task
5. Updates manifest

---

## /claudemem:save

Writes session notes and updates manifest.

**Usage**: `/claudemem:save`

**Creates**: `Sessions/{YYYY-MM-DD}.md`

**Contents**:
- Summary of session
- Tasks completed
- Decisions made
- Next steps

**Use when**:
- Ending work for the day
- Before switching projects
- After significant progress

---

## /claudemem:switch

Changes to a different project.

**Usage**: `/claudemem:switch <project-name>`

**Actions**:
1. Offers to save current session
2. Updates manifest active context
3. Loads new project context
4. Announces project state

---

## Task Status Tags

Use in epic task lists:

| Tag | Meaning |
|-----|---------|
| `#pending` | Not started |
| `#in-progress` | Currently working |
| `#done` | Completed |
| `#blocked` | Waiting on something |
| `#deferred` | Postponed |

## Priority Tags

| Tag | Meaning |
|-----|---------|
| `#P0` | Critical |
| `#P1` | High |
| `#P2` | Normal (default) |

## Dependency Tags

| Tag | Meaning |
|-----|---------|
| `#blocked-by:{task-id}` | Blocked by another task |
| `#blocks:{task-id}` | Blocks another task |
