---
description: "Create PROMPT.md, IMPLEMENTATION_PLAN.md, and specs/ scaffolding for a new loop"
hide-from-slash-command-tool: "true"
---

# Lisa Prep

Prepare groundwork files for a Lisa loop. This command creates the scaffolding needed for effective autonomous iteration.

## Workflow

When user invokes `/lisa-prep`, follow this workflow:

### Step 1: Ask About Version Control

Before creating files, ask the user:

> "Do you want Lisa artifacts (PROMPT.md, IMPLEMENTATION_PLAN.md, specs/) to be committed or ignored in git?"

| Option | When to use |
|--------|-------------|
| **Commit** | Documentation matters, team project, want to preserve design decisions |
| **Ignore** | Personal project, temporary task, files will become obsolete |

If user chooses to ignore, add to `.gitignore`:
```gitignore
# Lisa Wiggum loop artifacts
PROMPT.md
IMPLEMENTATION_PLAN.md
specs/
```

### Step 2: Understand the Task

Ask the user what they want to build. Gather:
- What is the goal?
- What technologies/stack?
- Any specific requirements or constraints?
- How will we know when it's done?

### Step 3: Analyze Existing Codebase (if applicable)

If working in an existing project:
- Explore the project structure
- Identify existing patterns and conventions
- Note the tech stack being used
- Find similar implementations to follow

### Step 4: Create specs/ Directory

Create `specs/` with clear, concise requirement files:

```
specs/
├── overview.md      # What the project does (1 paragraph)
├── features.md      # Feature list with acceptance criteria
├── tech-stack.md    # Technologies and why
└── conventions.md   # Code patterns to follow
```

Each file should be SHORT. Claude doesn't need essays, just facts.

**Example specs/overview.md:**
```markdown
# Overview

A REST API for managing todo items with user authentication.
Supports CRUD operations, due dates, and task priorities.
Built with Express.js, PostgreSQL, and JWT auth.
```

**Example specs/features.md:**
```markdown
# Features

## Authentication
- [ ] POST /auth/register - Create user account
- [ ] POST /auth/login - Get JWT token
- [ ] Middleware to protect routes

## Todos
- [ ] GET /todos - List user's todos
- [ ] POST /todos - Create todo
- [ ] PUT /todos/:id - Update todo
- [ ] DELETE /todos/:id - Delete todo

## Acceptance Criteria
- All endpoints return proper HTTP status codes
- Input validation on all endpoints
- Tests with >80% coverage
```

### Step 5: Create IMPLEMENTATION_PLAN.md

A simple checklist of tasks:

```markdown
# Implementation Plan

## Phase 1: Foundation
- [ ] Setup project structure
- [ ] Configure database connection
- [ ] Add authentication middleware

## Phase 2: Core Features
- [ ] Implement user registration
- [ ] Implement login endpoint
- [ ] Implement CRUD endpoints

## Phase 3: Polish
- [ ] Add input validation
- [ ] Write tests
- [ ] Add API documentation
```

Tasks should be:
- **Atomic**: One clear thing to do
- **Verifiable**: Can check if done
- **Ordered**: Dependencies resolved by order

### Step 6: Create PROMPT.md

Generate the simple prompt that references the prepared files:

```markdown
# Mission

Build [PROJECT_NAME].

# Process

1. Read specs/ for requirements
2. Read IMPLEMENTATION_PLAN.md for tasks
3. Pick the first unchecked task
4. Implement it
5. Test it
6. Mark it done: `- [x]`
7. Commit with descriptive message
8. Repeat until all tasks complete

# Completion

When all tasks in IMPLEMENTATION_PLAN.md are marked `[x]`:

<promise>DONE</promise>
```

### Step 7: Confirm Ready

Show the user what was created:

```
✅ Lisa preparation complete!

Created:
  specs/overview.md
  specs/features.md
  specs/tech-stack.md
  specs/conventions.md
  IMPLEMENTATION_PLAN.md
  PROMPT.md

To start the loop:
  /lisa-loop PROMPT.md --max-iterations 50

The completion promise <promise>DONE</promise> will be auto-detected.
```

## Key Principles

1. **Simple prompts, rich context** - The complexity lives in specs/, not PROMPT.md
2. **Atomic tasks** - Each task should be completable in one iteration
3. **Clear completion** - Always define exactly when the loop should end
4. **Safety limits** - Always recommend --max-iterations
