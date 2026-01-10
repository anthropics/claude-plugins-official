# Activate testing mode with checklist

## Instructions

When the user runs `/task-test-mode [type]`, add a testing checklist to the current task:

1. **Get the template type** (or ask if not provided):

   Available types:
   - `feature` - Comprehensive feature testing
   - `bugfix` - Bug fix verification
   - `refactor` - Refactor validation
   - `api` - API endpoint testing
   - `ui` - UI/UX testing
   - `security` - Security-focused testing
   - `deployment` - Pre-deployment checklist
   - `quick` - Minimal smoke test

2. **Load the template** from `.claude/plugins/task/scripts/test-templates.json`

3. **Append to checklist.md**:
   ```markdown

   ## Testing Checklist
   ## Type: [template type]

   - [ ] Test item 1
   - [ ] Test item 2
   - [ ] Test item 3
   ...
   ```

4. **Log the action** in decisions.log:
   ```
   [TIMESTAMP] Added testing checklist: [type]
   ```

5. **Show the user**:
   - The testing checklist that was added
   - Remind them to check off items as they test

## Template Details

### feature
Comprehensive testing for new features:
- Unit tests for new functions
- Integration tests for feature flow
- Edge case handling verified
- Error scenarios covered
- Performance acceptable (< 200ms response)
- No console errors or warnings
- Accessibility check
- Mobile/responsive verified
- Cross-browser tested

### bugfix
Bug fix verification:
- Bug reproduced before fix
- Bug no longer occurs after fix
- Root cause understood and documented
- Regression test added
- Related functionality still works
- No new console errors
- Performance not degraded

### refactor
Refactor validation:
- All existing tests pass
- No behavior changes
- Performance benchmark: before vs after
- Code coverage maintained
- No new linting errors
- Type checking passes
- Manual smoke test

### api
API endpoint testing:
- Happy path returns correct response
- Invalid input returns proper error
- Authentication/authorization works
- Rate limiting tested
- Response format matches schema
- Error responses consistent
- Performance under load
- API documentation updated

### ui
UI/UX testing:
- Visual appearance matches design
- Responsive on all devices
- Keyboard navigation works
- Focus states visible
- Loading/error states correct
- Animations smooth
- Dark/light mode works

### security
Security testing:
- Input validation
- SQL injection prevented
- XSS prevented
- CSRF protection
- Auth checks correct
- Sensitive data not logged
- Secrets not exposed

### deployment
Pre-deployment:
- All tests passing
- Build succeeds
- Environment configured
- Migrations ready
- Rollback plan
- Monitoring set up

### quick
Minimal smoke test:
- Change works
- No regressions
- Tests pass
- Builds successfully

## Usage Examples

```
/task-test-mode              # Show available types
/task-test-mode feature      # Add feature testing checklist
/task-test-mode bugfix       # Add bugfix verification checklist
/task-test-mode quick        # Add minimal smoke test
```

## Auto-Detection

If the task was created with `/task-template`, the testing type can be auto-detected:
- `bugfix` template → `bugfix` testing
- `feature` template → `feature` testing
- `refactor` template → `refactor` testing
- `hotfix` template → `quick` testing
