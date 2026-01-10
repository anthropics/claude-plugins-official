# Get AI task recommendations

## Instructions

When the user runs `/task-recommend`, analyze patterns and suggest next tasks:

1. **Run the recommender script**:
   ```bash
   node .claude/plugins/task/scripts/recommender.js
   ```

2. **Display recommendations** which include:

   **Current Task Context:**
   - Active task goal
   - Task type (bugfix, feature, etc.)

   **Suggested Next Tasks:**
   - Ranked by confidence (%)
   - Visual confidence bar
   - Reason for each suggestion

   **Tips:**
   - Based on task type patterns
   - Commonly skipped practices
   - Recent work trends

## Recommendation Types

### Follow-up Patterns
Based on what typically comes after a task type:

**After feature:**
- Add tests for new feature (95%)
- Update documentation (85%)
- Add error handling (75%)

**After bugfix:**
- Add regression test (90%)
- Check related code for similar issues (70%)
- Update error messages (60%)

**After refactor:**
- Run full test suite (95%)
- Update affected documentation (80%)
- Benchmark performance (70%)

**After hotfix:**
- Create proper fix for next release (90%)
- Add monitoring/alerting (85%)
- Post-mortem documentation (75%)

**After research:**
- Create proof of concept (85%)
- Document findings (90%)
- Present to stakeholders (70%)

### Missing Practices
Detects commonly skipped practices:
- Testing
- Documentation
- Code review
- Deployment checklists

### Trend Analysis
Based on recent work patterns:
- Many bugfixes → suggest refactoring
- No tests recently → suggest test coverage
- Repeated similar tasks → suggest automation

## Usage

```
/task-recommend
```

No arguments needed. The recommender analyzes:
- Current active task
- Last 10 completed tasks
- Task types and goals
- Decision logs

## Example Output

```
🤖 SUGGESTED NEXT TASKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current task: "Add OAuth login"
Type: feature

1. Add tests for new feature (95% match)
   █████████░
   Reason: Features need test coverage

2. Update documentation (85% match)
   ████████░░
   Reason: New features should be documented

3. Consider adding tests (80% match)
   ████████░░
   Reason: Skipped in 4 of last 10 tasks

💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Based on task type patterns
⚠️ Commonly skipped practices
```

## Benefits

- **Never forget follow-ups** - automated reminders
- **Improve practices** - catch skipped steps
- **Learn patterns** - see your work habits
- **Proactive guidance** - suggestions before you ask
