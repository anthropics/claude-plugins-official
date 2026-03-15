---
description: "Create a new development plan file from a high-level description. Generates a structured task list ready for /morpheus."
argument-hint: "[description-or-plan-path]"
---

The user wants to create or view a development plan.

## If the argument is a file path that exists:

Read the plan file and display a status summary:
```
Plan: [name]
Progress: N/M tasks (X%)

  [done]    1. Task one
  [done]    2. Task two
  [active]  3. Task three  <-- next
  [pending] 4. Task four
  [failed]  5. Task five
```

## If the argument is a description of work:

Create a structured plan file. Follow these steps:

1. **Gather project context** — Before designing tasks:
   - Call `sentinel_project_context` if available — learn conventions, hot files, architecture
   - Read relevant source files to understand the codebase
   - Identify the test command (from CLAUDE.md, package.json, CMakeLists.txt, Makefile, etc.)

2. **Analyze the description** — Break it into discrete, ordered tasks. Each task should be:
   - Completable in one focused coding session (15-60 min of AI work)
   - Independent where possible, ordered by dependency where not
   - Specific enough to have clear acceptance criteria

3. **Identify target files** — For each task, list the files that will need to be created or modified. Use project knowledge from step 1. If unsure, mark files with `?` and the dev-loop will refine during Phase 1 (CHECK).

4. **Write the plan file** at `plans/[kebab-case-name].md` in the current project directory (create `plans/` if needed):

```markdown
---
name: Plan Name
project: [current working directory]
created: [today's date]
test_command: "[the command to build and run tests]"
---

## 1. First Task Title
- **files**: path/to/file.cpp, path/to/other.h
- **do**: Clear description of what to implement
- **done-when**: Specific acceptance criteria that can be verified
- **status**: pending

## 2. Second Task Title
- **files**: path/to/file.cpp
- **do**: Clear description
- **done-when**: Acceptance criteria
- **status**: pending
```

5. **Display the plan** with the status summary format shown above.

6. Tell the user: `Run /morpheus plans/[filename].md to execute this plan.`

## Plan Design Principles

- **Small tasks**: 1-3 files per task. If a task touches more than 5 files, split it.
- **Test early**: If the plan adds new functionality, include a task for tests near the start, not the end.
- **Build order**: Place foundation tasks first, then features that depend on them.
- **One concern per task**: Don't mix refactoring with feature work in the same task.
- **Clear acceptance**: "done-when" should be verifiable by running tests or inspecting output — not subjective.
- **Include test_command**: Morpheus needs this to run Phase 3 (TEST). Always fill it in.

## Where Plans Live

Save plans to `plans/` in the project root. Name them with kebab-case: `plans/phase-4-visual-polish.md`.

Also create a symlink or copy at `.plan_file` in the project root pointing to the active plan, so `/morpheus` can find it without arguments.
