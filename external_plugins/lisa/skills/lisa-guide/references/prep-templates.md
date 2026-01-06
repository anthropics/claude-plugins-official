# Lisa Prep File Templates

Templates for the preparation files that Lisa references.

---

## specs/overview.md

```markdown
# [Project Name]

[One paragraph: What is this project and what problem does it solve?]

## Key Features
- [Feature 1]
- [Feature 2]
- [Feature 3]
```

---

## specs/features.md

```markdown
# Features

## [Feature Name]
**Purpose**: [Why this feature exists]
**Acceptance Criteria**:
- [ ] [Specific testable requirement]
- [ ] [Specific testable requirement]

## [Feature Name]
**Purpose**: [Why this feature exists]
**Acceptance Criteria**:
- [ ] [Specific testable requirement]
- [ ] [Specific testable requirement]
```

---

## specs/tech-stack.md

```markdown
# Tech Stack

## Runtime
- [Language/Runtime]: [Version]

## Framework
- [Framework]: [Why chosen]

## Database
- [Database]: [Why chosen]

## Key Libraries
- [Library]: [Purpose]
- [Library]: [Purpose]
```

---

## specs/conventions.md

```markdown
# Code Conventions

## File Structure
- [Pattern for organizing files]

## Naming
- Files: [convention]
- Functions: [convention]
- Variables: [convention]

## Patterns
- [Pattern 1]: [When to use]
- [Pattern 2]: [When to use]

## Testing
- [Testing approach]
- [What to test]
```

---

## IMPLEMENTATION_PLAN.md

```markdown
# Implementation Plan

## Phase 1: [Phase Name]
- [ ] [Task 1 - atomic, verifiable]
- [ ] [Task 2 - atomic, verifiable]
- [ ] [Task 3 - atomic, verifiable]

## Phase 2: [Phase Name]
- [ ] [Task 1 - atomic, verifiable]
- [ ] [Task 2 - atomic, verifiable]

## Phase 3: [Phase Name]
- [ ] [Task 1 - atomic, verifiable]
- [ ] [Task 2 - atomic, verifiable]
```

---

## PROMPT.md (The Simple Prompt)

```markdown
Build [PROJECT_NAME].

Read specs/ for requirements.
Read IMPLEMENTATION_PLAN.md for tasks.
Pick the first uncompleted task, implement it, test it, mark done.
Commit after every completed task.

When all tasks are done, output: <promise>DONE</promise>
```

---

## Example: Invoicing SaaS (Quidbill)

### specs/overview.md
```markdown
# Quidbill

Invoicing SaaS for freelancers and small businesses. Create, send, and track invoices.

## Key Features
- Create and manage invoices
- Send invoices via email
- Track payment status
- Dashboard with analytics
```

### IMPLEMENTATION_PLAN.md
```markdown
# Implementation Plan

## Phase 1: Foundation
- [ ] Initialize Next.js with TypeScript
- [ ] Setup Supabase connection
- [ ] Configure authentication
- [ ] Create database schema

## Phase 2: Core
- [ ] Invoice CRUD API
- [ ] Invoice list page
- [ ] Invoice detail page
- [ ] Invoice create/edit form

## Phase 3: Features
- [ ] Email sending
- [ ] Payment tracking
- [ ] Dashboard stats

## Phase 4: Polish
- [ ] Error handling
- [ ] Loading states
- [ ] Tests
```

### PROMPT.md
```markdown
Build Quidbill, an invoicing SaaS.

Read specs/ for requirements.
Read IMPLEMENTATION_PLAN.md for tasks.
Pick the first uncompleted task, implement it, test it, mark done.
Commit after every completed task.

When all tasks are done, output: <promise>DONE</promise>
```
