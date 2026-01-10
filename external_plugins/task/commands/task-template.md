# Start a task from template

## Instructions

When the user runs `/task-template <type> "<goal>"`, do the following:

1. **Parse the arguments**
   - `type`: Template type (bugfix, feature, refactor, hotfix, research)
   - `goal`: Task description (in quotes)

2. **Validate the template type**
   Available templates:

   **bugfix** - For fixing bugs
   - Reproduce the issue
   - Debug and identify root cause
   - Implement the fix
   - Write/update tests
   - Document the fix

   **feature** - For new features
   - Design the feature
   - Implement core functionality
   - Add tests
   - Code review prep
   - Deploy/integrate

   **refactor** - For code improvements
   - Analyze current code
   - Plan refactoring strategy
   - Refactor incrementally
   - Ensure test coverage
   - Benchmark before/after

   **hotfix** - For urgent production fixes
   - Identify the issue
   - Implement minimal fix
   - Quick smoke test
   - Deploy to production

   **research** - For exploration tasks
   - Explore the problem space
   - Document findings
   - Create prototype if needed
   - Present recommendations

3. **Generate a task ID**
   - Use format: `task_YYYYMMDD_HHMMSS` (current timestamp)

4. **Create the task directory**
   ```
   .claude/task/<task_id>/
   ├── plan.md
   ├── checklist.md
   ├── handoff.md
   └── decisions.log
   ```

5. **Create plan.md** with template-specific content:
   ```markdown
   # Task Plan

   ## Type
   [template type]

   ## Goal
   [User's goal]

   ## Approach
   [Template-specific steps from above]

   ## Success Criteria
   [Template-specific criteria]
   ```

6. **Create checklist.md** with template steps:
   ```markdown
   # Task Checklist

   ## Status: IN_PROGRESS
   ## Template: [type]

   [Pre-filled checklist items based on template]
   ```

7. **Create handoff.md** and **decisions.log** as in /task-start

8. **Update .claude/CLAUDE.md** with imports

9. **Show the user**:
   - Task ID and template used
   - Pre-filled checklist
   - Remind to restart or check /memory

## Examples

```
/task-template bugfix "Fix login timeout issue"
/task-template feature "Add dark mode toggle"
/task-template refactor "Clean up authentication module"
/task-template hotfix "Fix payment gateway 500 error"
/task-template research "Evaluate caching strategies"
```

## Template Details

### bugfix
**Success Criteria:**
- Bug is reproducible before fix
- Bug no longer occurs after fix
- No regression in related features
- Test added to prevent recurrence

**Checklist:**
- [ ] Reproduce the bug consistently
- [ ] Identify root cause
- [ ] Implement fix
- [ ] Add/update tests
- [ ] Verify fix resolves issue
- [ ] Document in decisions.log

### feature
**Success Criteria:**
- Feature works as specified
- Tests cover happy path and edge cases
- Code follows project conventions
- No performance regression

**Checklist:**
- [ ] Design feature approach
- [ ] Implement core functionality
- [ ] Handle edge cases
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Update documentation
- [ ] Self code review

### refactor
**Success Criteria:**
- Code is cleaner/more maintainable
- All existing tests pass
- No behavior changes
- Performance equal or better

**Checklist:**
- [ ] Analyze current implementation
- [ ] Plan refactoring steps
- [ ] Refactor step 1
- [ ] Refactor step 2
- [ ] Run full test suite
- [ ] Compare before/after metrics

### hotfix
**Success Criteria:**
- Production issue resolved
- Minimal changes made
- No new issues introduced

**Checklist:**
- [ ] Identify exact issue
- [ ] Implement minimal fix
- [ ] Quick verification test
- [ ] Ready for deployment

### research
**Success Criteria:**
- Problem space understood
- Options documented with pros/cons
- Recommendation provided

**Checklist:**
- [ ] Define research scope
- [ ] Explore option 1
- [ ] Explore option 2
- [ ] Document findings
- [ ] Create prototype (optional)
- [ ] Write recommendations
