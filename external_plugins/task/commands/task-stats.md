# Show task analytics dashboard

## Instructions

When the user runs `/task-stats`, display comprehensive analytics:

1. **Run the analytics script**
   ```bash
   node .claude/plugins/task/scripts/analytics.js [days]
   ```
   Default: 30 days. User can specify: `/task-stats 7` for last 7 days.

2. **Display the dashboard** which includes:

   **Summary:**
   - Completed tasks count
   - In progress tasks
   - Abandoned tasks
   - Success rate percentage
   - Average task duration

   **Most Productive Hours:**
   - Bar chart showing task completion by hour
   - Top 4 most productive time slots

   **Productivity by Day:**
   - Tasks completed by day of week (Mon-Sun)

   **Task Types:**
   - Distribution of task types (bugfix, feature, refactor, etc.)

   **Fastest Completions:**
   - Top 3 quickest task completions with goal

   **Longest Tasks:**
   - Top 3 slowest task completions with goal

   **Recommendations:**
   - AI-generated tips based on patterns
   - "Break tasks > 6 hours into subtasks"
   - "High abandon rate - consider smaller scopes"

   **All Time Stats:**
   - Total tasks ever created
   - Total completed

3. **If script fails**, manually analyze by:
   - Count tasks in `.claude/task/` and `.claude/task/archive/`
   - Parse `decisions.log` for timestamps
   - Calculate durations from first to last entry

## Usage Examples

```
/task-stats         # Last 30 days (default)
/task-stats 7       # Last 7 days
/task-stats 90      # Last 90 days
```

## Data Storage

Stats are cached in `.claude/task/stats.json`:
```json
{
  "lastUpdated": "ISO-TIMESTAMP",
  "period": "Last 30 days",
  "summary": {
    "completed": 12,
    "inProgress": 1,
    "abandoned": 2,
    "successRate": 86
  },
  "avgDuration": 14400000,
  "hourlyStats": { "9": 5, "14": 3, ... },
  "dayStats": { "1": 4, "2": 3, ... },
  "typeStats": { "bugfix": 5, "feature": 7 }
}
```

## Insights

The analytics help identify:
- **Peak productivity times** - Schedule complex work accordingly
- **Optimal task size** - Avoid tasks that consistently get abandoned
- **Specialization patterns** - What types of tasks you do most
- **Improvement areas** - Success rate trends
