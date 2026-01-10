# Start a new task

## Instructions

When the user runs this command, do the following:

1. **Ask for the task goal** if not provided as argument
   - Get a clear, specific description of what they want to accomplish

2. **Generate a task ID** 
   - Use format: `task_YYYYMMDD_HHMMSS` (current timestamp)

3. **Create the task directory structure**
```
   .claude/task/<task_id>/
   ├── plan.md
   ├── checklist.md
   ├── handoff.md
   └── decisions.log
```

4. **Create plan.md** with:
```markdown
   # Task Plan
   
   ## Goal
   [User's goal here]
   
   ## Approach
   [Break down into steps]
   
   ## Success Criteria
   [How we know it's done]
```

5. **Create checklist.md** with:
```markdown
   # Task Checklist
   
   ## Status: IN_PROGRESS
   
   - [ ] Step 1
   - [ ] Step 2
   - [ ] Step 3
```

6. **Create handoff.md** with:
```markdown
   # Handoff Notes
   
   ## Current State
   Task just started.
   
   ## Next Actions
   [To be updated]
   
   ## Blockers
   None yet.
```

7. **Create decisions.log** with:
```
   [TIMESTAMP] Task created with goal: [goal]
```

8. **Update .claude/CLAUDE.md** to add imports:
```markdown
   # Active Task
   
   @.claude/task/<task_id>/plan.md
   @.claude/task/<task_id>/checklist.md
   @.claude/task/<task_id>/handoff.md
```

9. **Tell the user**:
   - Task created with ID
   - Remind them to restart Claude or check `/memory` to load the imports
   - Show the plan summary

## Important
- Always append to decisions.log, never overwrite
- Keep checklist.md updated as work progresses