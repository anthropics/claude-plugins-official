# Mission

Build a REST API for a todo application.

# Requirements

- Express.js with TypeScript
- PostgreSQL database with Drizzle ORM
- JWT authentication
- Full CRUD for todos (create, read, update, delete)
- Input validation with Zod
- Error handling middleware
- Tests with Vitest (>80% coverage)

# Process

1. Read IMPLEMENTATION_PLAN.md for current task list
2. Find the first unchecked task `- [ ]`
3. Implement it completely
4. Run tests: `npm test`
5. If tests fail, fix the issue
6. Mark task complete: `- [x]`
7. Commit with descriptive message
8. Repeat until all tasks done

# Completion Criteria

All of the following must be true:
- All tasks in IMPLEMENTATION_PLAN.md are checked
- `npm test` passes with 0 failures
- `npm run typecheck` passes with 0 errors

When ALL criteria are met, output: <promise>DONE</promise>

# If Stuck

After 20 iterations without progress:
- Document what's blocking in BLOCKERS.md
- List all approaches tried
- Suggest alternative solutions
