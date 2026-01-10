# Show achievements and streaks

## Instructions

When the user runs `/task-achievements`, display their gamification stats:

1. **Run the achievements script**
   ```bash
   node .claude/plugins/task/scripts/achievements.js
   ```

2. **Display the output** which includes:

   **Earned Achievements:**
   - 🔥 Streak - Complete tasks X days in a row (3/7/14/30 days)
   - ⚡ Speed Demon - Complete X tasks in a single day (3/5/10)
   - 🏆 Centurion - Complete X tasks total (10/25/50/100)
   - 🌙 Night Owl - Complete X tasks after 10 PM (5/15/30)
   - 🌅 Early Bird - Complete X tasks before 8 AM (5/15/30)
   - 🐛 Bug Hunter - Complete X bugfix tasks (5/20/50)
   - 🏗️ Architect - Complete X feature tasks (5/15/30)
   - 🎯 Perfectionist - Complete X tasks without abandoning (5/10/25)

   **Active Streak:**
   - Shows current consecutive days with completed tasks

   **Next Milestones:**
   - Progress bars for upcoming achievements

   **Stats:**
   - Total completed tasks
   - Abandoned tasks
   - Success rate percentage

3. **If script fails**, manually calculate by:
   - Count tasks in `.claude/task/archive/`
   - Check `checklist.md` for status (COMPLETED vs ABANDONED)
   - Parse task IDs for dates/times

## Data Storage

Achievements are cached in `.claude/task/achievements.json`:
```json
{
  "lastUpdated": "ISO-TIMESTAMP",
  "stats": {
    "totalTasks": 12,
    "abandonedTasks": 2,
    "streak": 5,
    "maxDailyTasks": 3
  },
  "achievements": { ... }
}
```

## Tips for Users

- Complete at least one task per day to maintain your streak
- Use `/task-template bugfix` to track bug fixes for Bug Hunter badge
- Use `/task-template feature` to track features for Architect badge
- Avoid abandoning tasks to improve Perfectionist badge
