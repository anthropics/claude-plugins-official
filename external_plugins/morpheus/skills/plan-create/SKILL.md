---
name: Plan Creation
description: "Activates when the user wants to create a development plan, break work into tasks, or structure a large feature into incremental steps. Generates plan files compatible with the /morpheus command."
version: 2.0.0
---

# Plan Creation

When the user describes a large piece of work and wants it broken into a structured plan, create a plan file following this format:

## Plan File Format

```markdown
---
name: Plan Name
project: /absolute/path/to/project
created: YYYY-MM-DD
test_command: "the command to build and run tests"
---

## 1. Task Title
- **files**: path/to/file.ext, path/to/other.ext
- **do**: What to implement (clear, specific)
- **done-when**: How to verify it's complete (testable)
- **status**: pending

## 2. Next Task Title
- **files**: path/to/file.ext
- **do**: Description
- **done-when**: Criteria
- **status**: pending
```

## Before Creating the Plan

Gather context first:
1. Call `sentinel_project_context` if available — learn conventions, hot files, architecture
2. Read key source files to understand the codebase structure
3. Identify the test command and include it in frontmatter

## Task Design Rules

1. **Granularity**: Each task = 1-3 files, ~50-200 lines of changes. If bigger, split it.
2. **Order**: Dependencies first. Foundation before features. Tests alongside or immediately after the code they test.
3. **Independence**: Where possible, tasks should be independently committable. Avoid tasks that leave the project in a broken state.
4. **Specificity**: "do" should be precise enough that two developers would produce similar results. "done-when" should be verifiable by running a command.
5. **No meta-tasks**: Don't create tasks like "plan the architecture" or "review the code". Every task produces committed code.
6. **Test command required**: The `test_command` in frontmatter is used by the Morpheus TEST phase. Always fill it in.

## Status Values

- `pending` — not started
- `in_progress` — currently being worked on
- `done` — completed and committed
- `failed` — attempted but could not complete (tests fail, grade too low)
- `skipped` — skipped because a dependency failed

## Where Plans Live

Save plans to `plans/` in the project root. Name them with kebab-case: `plans/phase-4-visual-polish.md`.

Also create `.plan_file` in the project root as a symlink or copy of the active plan, so `/morpheus` can find it without arguments.

After creating the plan, tell the user:
```
Run `/morpheus plans/[filename].md` to start autonomous execution.
```
