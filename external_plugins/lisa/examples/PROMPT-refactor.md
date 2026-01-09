# Mission

Refactor the codebase to use the new pattern defined in specs/architecture.md.

# Constraints

- Maintain 100% backwards compatibility
- All existing tests must continue to pass
- No new dependencies unless absolutely necessary
- Incremental changes (one file at a time)

# Process

1. Read specs/architecture.md for target pattern
2. Read IMPLEMENTATION_PLAN.md for refactoring tasks
3. Pick first unchecked task
4. Make the change
5. Run tests: `npm test`
6. If tests fail, fix without reverting the refactor
7. Run linter: `npm run lint`
8. Fix any lint errors
9. Mark task done: `- [x]`
10. Commit: `refactor: [description]`
11. Repeat

# Quality Checks

Before marking any task complete:
- [ ] Tests pass
- [ ] Lint passes
- [ ] Types check (`npm run typecheck`)
- [ ] No console warnings

# Completion

When all refactoring tasks are checked AND all quality checks pass:

<promise>REFACTOR COMPLETE</promise>
