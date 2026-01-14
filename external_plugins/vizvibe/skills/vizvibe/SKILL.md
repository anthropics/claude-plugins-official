---
name: vizvibe
description: |
  Trajectory management for vibe coding projects. Maintains vizvibe.mmd as a visual context map 
  that tracks project evolution, TODOs, and completed work. Use when managing project trajectory, 
  creating initial trajectory drafts, or updating work progress.
---

# Viz Vibe: Trajectory Management Skill

**Viz Vibe** is a graph-based navigator to track your coding trajectory and maintain context across threads. We make human-AI collaboration seamless by keeping coding context clear at a glance.

## What is `vizvibe.mmd`?

The `vizvibe.mmd` file is a **Mermaid flowchart** that serves as:

- A **visual map** of the project's evolution
- A **shared context** between human and AI
- A **TODO/hypothesis tracker** in graph form
- A **memory** that persists across conversation sessions

It's not a changelog or commit log — it's a **living document** that captures the high-level journey of a project.

---

## When to Update the Trajectory

**Code changes and trajectory updates are not always coupled:**

| Scenario                                                                   | Update .mmd? |
| -------------------------------------------------------------------------- | ------------ |
| Major discussion without code changes (e.g., planning, deciding direction) | ✅ Yes       |
| Small code fix or routine refactoring                                      | ❌ No        |
| New hypothesis or approach identified                                      | ✅ Yes       |
| Bug fix that doesn't change project direction                              | ❌ No        |
| Completing a significant milestone                                         | ✅ Yes       |

**Rule of thumb**: If it's something you'd want to remember when resuming work tomorrow, or when explaining the project to a new collaborator — it belongs in the trajectory.

---

## Node States: `[opened]` vs `[closed]`

Every node has a state in its metadata comment:

```mermaid
%% @node_id [ai-task, opened, 2026-01-14, username]
%% @node_id [ai-task, closed, 2026-01-14, username]
```

### `[opened]` — TODO

- Task is planned but **not yet started**
- Represents future work worth tracking

### `[closed]` — DONE

- ✅ Successfully completed
- ❌ Dead end (use `blocker` type)
- ⏭️ No longer needed

---

## Core Principles

### 1. Only Important Context

**DO NOT** add every small task:

- ✅ Major milestones and decisions
- ✅ Architectural changes
- ✅ Dead ends and blockers (valuable learnings)
- ❌ Trivial fixes
- ❌ Minor refactoring

### 2. Parallel vs Sequential Connections

**Parallel** (branch from same parent):

- Independent tasks, can happen in any order

```mermaid
parent --> option_a
parent --> option_b
```

**Sequential** (chain A → B):

- Task B depends on Task A

```mermaid
task_a --> task_b --> task_c
```

### 3. Always Update @lastActive

When you work on a node, update:

```mermaid
%% @lastActive: node_id_you_just_worked_on
```

---

## Node Content Format

Use title + description with `<sub>` tags:

```mermaid
%% @node_id [ai-task, closed, 2026-01-14, username]
node_id["Short Title<br/><sub>First line of description<br/>Second line of description<br/>Third line of description</sub>"]
```

---

## Style Reference (GitHub-inspired)

```mermaid
%% Start node (teal)
style node fill:#1a1a2e,stroke:#2dd4bf,color:#5eead4,stroke-width:2px

%% Closed tasks (soft purple - like GitHub merged)
style node fill:#1a1a2e,stroke:#a78bfa,color:#c4b5fd,stroke-width:1px

%% Open tasks (soft green - like GitHub open)
style node fill:#1a1a2e,stroke:#4ade80,color:#86efac,stroke-width:1px

%% Last active node (highlighted purple)
style node fill:#2d1f4e,stroke:#c084fc,color:#e9d5ff,stroke-width:2px

%% Blocker (soft red)
style node fill:#1a1a2e,stroke:#f87171,color:#fca5a5,stroke-width:1px

%% End/Goal (muted gray)
style node fill:#1a1a2e,stroke:#6b7280,color:#9ca3af,stroke-width:1px
```

---

## Creating Initial Trajectory

When creating the first draft:

1. **Read conversation history** - Extract milestones, decisions, pending work
2. **Check git history** - `git log --oneline -n 50` for recent commits
3. **Read README.md** - Understand project purpose and goals
4. **Ask user for feedback** - "Is anything incorrect? Any TODO lists to add?"

---

## Summary

1. **Read** `vizvibe.mmd` at session start
2. **Update** after completing significant work
3. **Update `@lastActive`** to the node you worked on
4. **Add future work** as `[opened]` nodes
5. **Close nodes** when done
6. **Keep it high-level** — this is a map, not a changelog
