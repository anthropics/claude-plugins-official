---
description: Use when the user asks Claude to inspect, plan, update, or execute work from Addness goals, tasks, comments, deliverables, notifications, or activity.
---

# Addness Goal Operations

Addness is the source of truth for goals, task status, progress, comments, deliverables, and execution context. Treat local files and other tools as working surfaces, not as the canonical goal system.

## Goal Semantics

- `description` means the current state.
- `definition_of_done` means the desired state.
- Subgoals are the actions that close the gap between the current state and the desired state.
- Apply this structure recursively. For each goal level, identify the gap, then act through the relevant child goals.

## Working Pattern

1. Read the relevant goal tree before recommending priorities or next actions.
2. Do not infer too much from goal titles alone. Fetch goal details, comments, deliverables, and activity when they are relevant and available.
3. If a goal has no `definition_of_done`, clarify the desired state or propose a concrete DoD before doing substantial work.
4. When progress changes the current state, update the goal `description`.
5. When an artifact is created, attach it as a deliverable instead of burying it in comments.
6. Use comments only when missing context must be collected from a person or when a discussion is needed.
7. Mark a goal complete only when the desired state is actually reached.

## Communication

- Refer to goals by title in user-facing text; include IDs only when useful for disambiguation.
- If Claude posts a comment in Addness, include a short AI signature such as `Claude Codeより`.
- Treat cancelled goals as paused, not permanently deleted or invalid.
