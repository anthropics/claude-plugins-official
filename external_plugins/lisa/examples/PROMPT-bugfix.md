# Mission

Fix the failing tests in this project.

# Process

1. Run tests: `npm test`
2. Identify failing test(s)
3. Read the test file to understand what's expected
4. Find the source code being tested
5. Debug and fix the issue
6. Run tests again
7. If still failing, repeat from step 2
8. Commit fix with message: `fix: [description]`

# Rules

- Only modify source code, not tests (unless tests are clearly wrong)
- Make minimal changes to fix the issue
- Don't refactor unrelated code
- Each fix should be atomic and focused

# Completion

When `npm test` exits with code 0 and all tests pass:

<promise>ALL TESTS PASS</promise>

# Notes

- Check git history if you need context on recent changes
- Look for console.log or debugger statements to remove
- Verify TypeScript types are correct
