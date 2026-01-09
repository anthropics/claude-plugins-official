---
name: lisa-guide
description: Guide for writing effective prompts for the Lisa technique. Use this skill when the user wants to start a Lisa loop, prepare files for Lisa, write a PROMPT.md, or needs help structuring autonomous iterative tasks. Invoke with /lisa-prep to prepare groundwork files, then /lisa-loop to execute.
---

# Lisa Prompt Guide

## The Two-Phase Workflow

Lisa prompts are simple BECAUSE the complexity lives in preparation files.

```
Phase 1: PREPARE          Phase 2: EXECUTE
┌─────────────────┐       ┌─────────────────┐
│  /lisa-prep    │  ──▶  │  /lisa-loop    │
│                 │       │                 │
│  Creates:       │       │  Simple prompt  │
│  - specs/       │       │  references the │
│  - PLAN.md      │       │  prepared files │
│  - PROMPT.md    │       │                 │
└─────────────────┘       └─────────────────┘
```

## Phase 1: Preparation (/lisa-prep)

Before starting a Lisa loop, create the groundwork files. When user invokes `/lisa-prep`:

### Step 0: Ask About Version Control

Before creating files, ask the user how they want to handle Lisa artifacts:

**Question to ask:**
> "Do you want Lisa artifacts (PROMPT.md, IMPLEMENTATION_PLAN.md, specs/) to be committed or ignored in git?"

| Option | When to use |
|--------|-------------|
| **Commit** | Documentation matters, team project, want to preserve design decisions |
| **Ignore** | Personal project, temporary task, files will become obsolete |

If user chooses to ignore, add to `.gitignore`:
```gitignore
# Lisa loop artifacts
PROMPT.md
IMPLEMENTATION_PLAN.md
specs/
```

### Step 1: Analyze the Codebase

Explore the existing project structure, patterns, and conventions:
- What stack is being used?
- What patterns exist?
- What's already implemented?

### Step 2: Create specs/ Directory

Create `specs/` with clear, concise requirement files:

```
specs/
├── overview.md      # What the project does (1 paragraph)
├── features.md      # Feature list with acceptance criteria
├── tech-stack.md    # Technologies and why
└── conventions.md   # Code patterns to follow
```

Each file should be SHORT. Claude doesn't need essays, just facts.

### Step 3: Create IMPLEMENTATION_PLAN.md

A simple checklist of tasks:

```markdown
# Implementation Plan

## Phase 1: Foundation
- [ ] Setup project structure
- [ ] Configure database
- [ ] Add authentication

## Phase 2: Core Features
- [ ] Feature A
- [ ] Feature B
- [ ] Feature C

## Phase 3: Polish
- [ ] Error handling
- [ ] Tests
- [ ] Documentation
```

Tasks should be:
- **Atomic**: One clear thing to do
- **Verifiable**: Can check if done
- **Ordered**: Dependencies resolved by order

### Step 4: Create PROMPT.md

Generate the simple prompt that references the prepared files:

```markdown
Build [PROJECT_NAME].

Read specs/ for requirements.
Read IMPLEMENTATION_PLAN.md for tasks.
Pick the first uncompleted task, implement it, test it, mark done.
Commit after every completed task.

When all tasks are done, output: <promise>DONE</promise>
```

That's ~50 words. The complexity is in the files, not the prompt.

---

## Phase 2: Execution (/lisa-loop)

Once preparation is complete, start the loop:

```
/lisa-loop --max-iterations 30 PROMPT.md
```

The script will **auto-detect** `<promise>DONE</promise>` from PROMPT.md. You can also explicitly set it:

```
/lisa-loop --max-iterations 30 --completion-promise "DONE" PROMPT.md
```

Lisa will:
1. Read PROMPT.md
2. Read specs/ and IMPLEMENTATION_PLAN.md
3. Find first unchecked task
4. Implement it
5. Mark it done, commit
6. Repeat until all done

---

## Core Principle: Less Is More

The most important lesson from production use: **simple prompts beat complex ones**.

From the RepoMirror hackathon:
- 1500-word detailed prompt → Failed
- 103-word simple prompt → Won

Claude already knows how to code. Tell it WHAT to do, not HOW.

## How Lisa Actually Works

```
while true; do
  cat PROMPT.md | claude --continue
done
```

1. Claude receives the SAME prompt every iteration
2. Claude works and modifies FILES
3. Next iteration, Claude SEES those files
4. The "memory" is in the FILES, not the prompt

## Prompt Structure

### Minimal Effective Prompt (Recommended)

```markdown
# Mission
[One sentence describing the goal]

# Success Criteria
[How to know when done - be specific]

# Rules
- Commit after every file change
- Output <promise>DONE</promise> when complete
```

### Example: Port a Library

```markdown
# Mission
Port the Python library in /src to TypeScript in /ts-src.

# Success Criteria
All .py files have equivalent .ts files with passing type checks.

# Rules
- Commit after every file edit
- Run `tsc --noEmit` to verify
- Output <promise>DONE</promise> when all files ported and types pass
```

### Example: Build a Feature

```markdown
# Mission
Add user authentication to the Express API.

# Success Criteria
- POST /auth/register creates users
- POST /auth/login returns JWT
- Protected routes require valid token
- All tests pass

# Rules
- Commit after each endpoint
- Write tests for each endpoint
- Output <promise>DONE</promise> when tests pass
```

### Example: Fix Bugs

```markdown
# Mission
Fix all TypeScript errors in the codebase.

# Success Criteria
`npm run typecheck` exits with 0 errors.

# Rules
- Fix one file at a time
- Commit after each fix
- Output <promise>DONE</promise> when typecheck passes
```

## The Completion Promise

Lisa loops until it sees `<promise>DONE</promise>` in Claude's output.

**Auto-detection:** If your PROMPT.md contains `<promise>...</promise>` tags, the setup script will automatically extract and configure the promise. No need to pass `--completion-promise` separately.

Always include this rule in your prompt:
```markdown
Output <promise>DONE</promise> when [specific condition]
```

Be SPECIFIC about the condition. Not "when done" but "when tests pass" or "when all files are ported".

## Anti-Patterns (What NOT to Do)

### Too Much Detail
```markdown
# BAD - Don't do this
When implementing the authentication system, first analyze the existing
codebase structure. Look for patterns in how other features are implemented.
Consider using JWT tokens with RS256 algorithm. Make sure to handle edge
cases like expired tokens, invalid signatures, and missing headers...
[500 more words]
```

Claude knows all this. You're just confusing it.

### Vague Success Criteria
```markdown
# BAD
Output <promise>DONE</promise> when you're finished.
```

Finished with what? Be specific.

### No Commit Rule
```markdown
# BAD - Missing commits
Port the library to TypeScript.
```

Without "commit after every file", you lose the incremental progress that makes Lisa work.

## Good Patterns

### Phased Work in ONE Prompt
```markdown
# Mission
Build a CLI todo app.

# Phases (do in order)
1. Setup: Initialize project with package.json and TypeScript
2. Core: Implement add, list, complete, delete commands
3. Storage: Persist todos to ~/.todos.json
4. Polish: Add colors and help text

# Rules
- Complete each phase before moving to next
- Commit after each phase
- Output <promise>DONE</promise> when all phases complete and working
```

### With Verification Steps
```markdown
# Mission
Refactor the database layer to use connection pooling.

# Success Criteria
- All tests pass
- No direct db.connect() calls remain
- Pool configured in config.ts

# Verification
Run these after each change:
- `npm test`
- `grep -r "db.connect" src/` should return nothing

# Rules
- Commit after each file refactored
- Output <promise>DONE</promise> when verification passes
```

## Starting a Lisa Loop

Use the `/lisa-loop` command:

```
/lisa-loop "Your prompt here" --max-iterations 20 --completion-promise "DONE"
```

Or create a PROMPT.md file and run manually:
```bash
while :; do cat PROMPT.md | claude --continue; done
```

## File Management & Cleanup

Lisa generates artifacts. Whether to commit them depends on your project:

### The Decision: Commit vs Ignore

| Commit when... | Ignore when... |
|----------------|----------------|
| Team project needs context | Personal/solo project |
| Specs document architectural decisions | Task is temporary/one-off |
| You want historical record of "why" | Files will become obsolete |
| Onboarding future developers | Keeping repo clean matters |

### Files Lisa Creates

| File | Purpose |
|------|---------|
| `PROMPT.md` | Execution script for the loop |
| `IMPLEMENTATION_PLAN.md` | Task checklist with phases |
| `specs/` | Requirements and design specs |

### To Ignore (if chosen)

```gitignore
# Lisa loop artifacts
PROMPT.md
IMPLEMENTATION_PLAN.md
specs/
```

### To Remove Already-Committed Files

If you committed files but later decide to ignore:
```bash
git rm --cached PROMPT.md IMPLEMENTATION_PLAN.md specs/*
# Then add to .gitignore
git commit -m "chore: remove Lisa artifacts from tracking"
```

Files remain on disk but leave version control.

---

## Debugging Failed Loops

If Lisa isn't making progress:

1. **Prompt too complex?** Simplify it
2. **Success criteria unclear?** Make it measurable
3. **Missing commit rule?** Add it
4. **No completion promise?** Claude won't know when to stop

## Quick Reference

| Element | Required | Example |
|---------|----------|---------|
| Mission | Yes | "Port library to TypeScript" |
| Success Criteria | Yes | "All tests pass" |
| Commit rule | Recommended | "Commit after every file" |
| Completion promise | Yes | `<promise>DONE</promise>` |
| Detailed instructions | NO | Claude already knows |
