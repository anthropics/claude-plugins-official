# Scheduled Tasks Pattern

**Use Case**: Recurring automation workflows that run automatically on a schedule.

---

## Pattern Structure

```
Schedule Trigger → [Fetch Data] → [Process] → [Deliver] → [Log/Notify]
```

**Key Characteristic**: Time-based automated execution

---

## Core Components

### 1. Schedule Trigger
**Purpose**: Execute workflow at specified times

**Modes**:
- **Interval** - Every X minutes/hours/days
- **Cron** - Specific times (advanced)
- **Days & Hours** - Simple recurring schedule

### 2. Data Source
**Common sources**:
- HTTP Request (APIs)
- Database queries
- File reads
- Service-specific nodes

### 3. Processing
**Typical operations**:
- Filter/transform data
- Aggregate statistics
- Generate reports
- Check conditions

### 4. Delivery
**Output channels**:
- Email
- Slack/Discord/Teams
- File storage
- Database writes

### 5. Logging
**Purpose**: Track execution history

**Methods**:
- Database log entries
- File append
- Monitoring service

---

## Schedule Configuration

### Interval Mode
**Best for**: Simple recurring tasks

**Examples**:
```javascript
// Every 15 minutes
{
  mode: "interval",
  interval: 15,
  unit: "minutes"
}

// Every 2 hours
{
  mode: "interval",
  interval: 2,
  unit: "hours"
}

// Every day at midnight
{
  mode: "interval",
  interval: 1,
  unit: "days"
}
```

### Days & Hours Mode
**Best for**: Specific days and times

**Examples**:
```javascript
// Weekdays at 9 AM
{
  mode: "daysAndHours",
  days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
  hour: 9,
  minute: 0
}

// Every Monday at 6 PM
{
  mode: "daysAndHours",
  days: ["monday"],
  hour: 18,
  minute: 0
}
```

### Cron Mode (Advanced)
**Best for**: Complex schedules

**Examples**:
```javascript
// Every weekday at 9 AM
{
  mode: "cron",
  expression: "0 9 * * 1-5"
}

// First day of every month at midnight
{
  mode: "cron",
  expression: "0 0 1 * *"
}

// Every 15 minutes during business hours (9 AM - 5 PM) on weekdays
{
  mode: "cron",
  expression: "*/15 9-17 * * 1-5"
}
```

**Cron format**: `minute hour day month weekday`
- `*` = any value
- `*/15` = every 15 units
- `1-5` = range (Monday-Friday)
- `1,15` = specific values

**Cron examples**:
```
0 */6 * * *      Every 6 hours
0 9,17 * * *     At 9 AM and 5 PM daily
0 0 * * 0        Every Sunday at midnight
*/30 * * * *     Every 30 minutes
0 0 1,15 * *     1st and 15th of each month
```

---

## Common Use Cases

### 1. Daily Reports
**Flow**: Schedule → Fetch data → Aggregate → Format → Email

**Example** (Sales report):
```
1. Schedule (daily at 9 AM)

2. Postgres (query yesterday's sales)
   SELECT date, SUM(amount) as total, COUNT(*) as orders
   FROM orders
   WHERE date = CURRENT_DATE - INTERVAL '1 day'
   GROUP BY date

3. Code (calculate metrics)
   - Total revenue
   - Order count
   - Average order value
   - Comparison to previous day

4. Set (format email body)
   Subject: Daily Sales Report - {{$json.date}}
   Body: Formatted HTML with metrics

5. Email (send to team@company.com)

6. Slack (post summary to #sales)
```

### 2. Data Synchronization
**Flow**: Schedule → Fetch from source → Transform → Write to target

**Example** (CRM to data warehouse sync):
```
1. Schedule (every hour)

2. Set (store last sync time)
   SELECT MAX(synced_at) FROM sync_log

3. HTTP Request (fetch new CRM contacts since last sync)
   GET /api/contacts?updated_since={{$json.last_sync}}

4. IF (check if new records exist)

5. Set (transform CRM schema to warehouse schema)

6. Postgres (warehouse - INSERT new contacts)

7. Postgres (UPDATE sync_log SET synced_at = NOW())

8. IF (error occurred)
   └─ Slack (alert #data-team)
```

### 3. Monitoring & Health Checks
**Flow**: Schedule → Check endpoints → Alert if down

**Example** (Website uptime monitor):
```
1. Schedule (every 5 minutes)

2. HTTP Request (GET https://example.com/health)
   - timeout: 10 seconds
   - continueOnFail: true

3. IF (status !== 200 OR response_time > 2000ms)

4. Redis (check alert cooldown - don't spam)
   - Key: alert:website_down
   - TTL: 30 minutes

5. IF (no recent alert sent)

6. [Alert Actions]
   ├─ Slack (notify #ops-team)
   ├─ PagerDuty (create incident)
   ├─ Email (alert@company.com)
   └─ Redis (set alert cooldown)

7. Postgres (log uptime check result)
```

### 4. Cleanup & Maintenance
**Flow**: Schedule → Find old data → Archive/Delete → Report

**Example** (Database cleanup):
```
1. Schedule (weekly on Sunday at 2 AM)

2. Postgres (find old records)
   SELECT * FROM logs
   WHERE created_at < NOW() - INTERVAL '90 days'
   LIMIT 10000

3. IF (records exist)

4. Code (export to JSON for archive)

5. Google Drive (upload archive file)
   - Filename: logs_archive_{{$now.format('YYYY-MM-DD')}}.json

6. Postgres (DELETE archived records)
   DELETE FROM logs
   WHERE id IN ({{$json.archived_ids}})

7. Slack (report: "Archived X records, deleted Y records")
```

### 5. Data Enrichment
**Flow**: Schedule → Find incomplete records → Enrich → Update

**Example** (Enrich contacts with company data):
```
1. Schedule (nightly at 3 AM)

2. Postgres (find contacts without company data)
   SELECT id, email, domain FROM contacts
   WHERE company_name IS NULL
   AND created_at > NOW() - INTERVAL '7 days'
   LIMIT 100

3. Split In Batches (10 contacts per batch)

4. HTTP Request (call Clearbit enrichment API)
   - For each contact domain
   - Rate limit: wait 1 second between batches

5. Set (map API response to database schema)

6. Postgres (UPDATE contacts with company data)

7. Wait (1 second - rate limiting)

8. Loop (back to step 4 until all batches processed)

9. Email (summary: "Enriched X contacts")
```

### 6. Backup Automation
**Flow**: Schedule → Export data → Compress → Store → Verify

**Example** (Database backup):
```
1. Schedule (daily at 2 AM)

2. Code (execute pg_dump)
   const { exec } = require('child_process');
   exec('pg_dump -h db.example.com mydb > backup.sql')

3. Code (compress backup)
   const zlib = require('zlib');
   // Compress backup.sql to backup.sql.gz

4. AWS S3 (upload compressed backup)
   - Bucket: backups
   - Key: db/backup-{{$now.format('YYYY-MM-DD')}}.sql.gz

5. AWS S3 (list old backups)
   - Keep last 30 days only

6. AWS S3 (delete old backups)

7. IF (error occurred)
   ├─ PagerDuty (critical alert)
   └─ Email (backup failed!)
   ELSE
   └─ Slack (#devops: "✅ Backup completed")
```

### 7. Content Publishing
**Flow**: Schedule → Fetch content → Format → Publish

**Example** (Automated social media posts):
```
1. Schedule (every 3 hours during business hours)
   - Cron: 0 9,12,15,18 * * 1-5

2. Google Sheets (read content queue)
   - Sheet: "Scheduled Posts"
   - Filter: status=pending AND publish_time <= NOW()

3. IF (posts available)

4. HTTP Request (shorten URLs in post)

5. HTTP Request (POST to Twitter API)

6. HTTP Request (POST to LinkedIn API)

7. Google Sheets (update status=published)

8. Slack (notify #marketing: "Posted: {{$json.title}}")
```

---

## Timezone Considerations

### Set Workflow Timezone
```javascript
// In workflow settings
{
  timezone: "America/New_York"  // EST/EDT
}
```

### Common Timezones
```
America/New_York    - Eastern (US)
America/Chicago     - Central (US)
America/Denver      - Mountain (US)
America/Los_Angeles - Pacific (US)
Europe/London       - GMT/BST
Europe/Paris        - CET/CEST
Asia/Tokyo          - JST
Australia/Sydney    - AEDT
UTC                 - Universal Time
```

### Handle Daylight Saving
**Best practice**: Use timezone-aware scheduling

```javascript
// ❌ Bad: UTC schedule for "9 AM local"
// Will be off by 1 hour during DST transitions

// ✅ Good: Set workflow timezone
{
  timezone: "America/New_York",
  schedule: {
    mode: "daysAndHours",
    hour: 9  // Always 9 AM Eastern, regardless of DST
  }
}
```

---

## Error Handling

### Pattern 1: Error Trigger Workflow
**Main workflow**: Normal execution
**Error workflow**: Alerts and recovery

**Main**:
```
Schedule → Fetch → Process → Deliver
```

**Error**:
```
Error Trigger (for main workflow)
  → Set (extract error details)
  → Slack (#ops-team: "❌ Scheduled job failed")
  → Email (admin alert)
  → Postgres (log error for analysis)
```

### Pattern 2: Retry with Backoff
```
Schedule → HTTP Request (continueOnFail: true)
  → IF (error)
    ├─ Wait (5 minutes)
    ├─ HTTP Request (retry 1)
    └─ IF (still error)
      ├─ Wait (15 minutes)
      ├─ HTTP Request (retry 2)
      └─ IF (still error)
        └─ Alert admin
```

### Pattern 3: Partial Failure Handling
```
Schedule → Split In Batches
  → Process (continueOnFail: true)
  → Code (track successes and failures)
  → Report:
    "✅ Processed: 95/100"
    "❌ Failed: 5/100"
```

---

## Performance Optimization

### 1. Batch Processing
For large datasets:

```
Schedule → Query (LIMIT 10000)
  → Split In Batches (100 items)
  → Process batch
  → Loop
```

### 2. Parallel Processing
When operations are independent:

```
Schedule
  ├─ [Branch 1: Update DB]
  ├─ [Branch 2: Send emails]
  └─ [Branch 3: Generate report]
  → Merge (wait for all) → Final notification
```

### 3. Skip if Already Running
Prevent overlapping executions:

```
Schedule → Redis (check lock)
  → IF (lock exists)
    └─ End (skip this execution)
  → ELSE
    ├─ Redis (set lock, TTL 30 min)
    ├─ [Execute workflow]
    └─ Redis (delete lock)
```

### 4. Early Exit on No Data
Don't waste time if nothing to process:

```
Schedule → Query (check if work exists)
  → IF (no results)
    └─ End workflow (exit early)
  → ELSE
    └─ Process data
```

---

## Monitoring & Logging

### Pattern 1: Execution Log Table
```sql
CREATE TABLE workflow_executions (
  id SERIAL PRIMARY KEY,
  workflow_name VARCHAR(255),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status VARCHAR(50),
  records_processed INT,
  error_message TEXT
);
```

**Log execution**:
```
Schedule
  → Set (record start)
  → [Workflow logic]
  → Postgres (INSERT execution log)
```

### Pattern 2: Metrics Collection
```
Schedule → [Execute]
  → Code (calculate metrics)
    - Duration
    - Records processed
    - Success rate
  → HTTP Request (send to monitoring system)
    - Datadog, Prometheus, etc.
```

### Pattern 3: Summary Notifications
Daily/weekly execution summaries:

```
Schedule (daily at 6 PM) → Query execution logs
  → Code (aggregate today's executions)
  → Email (summary report)
    "Today's Workflow Executions:
     - 24/24 successful
     - 0 failures
     - Avg duration: 2.3 min"
```

---

## Testing Scheduled Workflows

### 1. Use Manual Trigger for Testing
**Development pattern**:
```
Manual Trigger (for testing)
  → [Same workflow logic]
  → [Outputs]

// Once tested, replace with Schedule Trigger
```

### 2. Test with Different Times
```javascript
// Code node - simulate different times
const testTime = new Date('2024-01-15T09:00:00Z');
return [{ json: { currentTime: testTime } }];
```

### 3. Dry Run Mode
```
Schedule → Set (dryRun: true)
  → IF (dryRun)
    └─ Log what would happen (don't execute)
  → ELSE
    └─ Execute normally
```

### 4. Shorter Interval for Testing
```javascript
// Testing: every 1 minute
{
  mode: "interval",
  interval: 1,
  unit: "minutes"
}

// Production: every 1 hour
{
  mode: "interval",
  interval: 1,
  unit: "hours"
}
```

---

## Common Gotchas

### 1. ❌ Wrong: Ignoring timezone
```javascript
Schedule (9 AM)  // 9 AM in which timezone?
```

### ✅ Correct: Set workflow timezone
```javascript
// Workflow settings
{
  timezone: "America/New_York"
}
```

### 2. ❌ Wrong: Overlapping executions
```
Schedule (every 5 min) → Long-running task (10 min)
// Two executions running simultaneously!
```

### ✅ Correct: Add execution lock
```
Schedule → Redis (check lock)
  → IF (locked) → Skip
  → ELSE → Execute
```

### 3. ❌ Wrong: No error handling
```
Schedule → API call → Process (fails silently)
```

### ✅ Correct: Add error workflow
```
Main: Schedule → Execute
Error: Error Trigger → Alert
```

### 4. ❌ Wrong: Processing all data at once
```
Schedule → SELECT 1000000 records → Process (OOM)
```

### ✅ Correct: Batch processing
```
Schedule → SELECT with pagination → Split In Batches → Process
```

### 5. ❌ Wrong: Hardcoded dates
```javascript
query: "SELECT * FROM orders WHERE date = '2024-01-15'"
```

### ✅ Correct: Dynamic dates
```javascript
query: "SELECT * FROM orders WHERE date = CURRENT_DATE - INTERVAL '1 day'"
```

---

## Real Template Examples

From n8n template library:

**Template #2947** (Weather to Slack):
```
Schedule (daily 8 AM)
  → HTTP Request (weather API)
  → Set (format message)
  → Slack (post to #general)
```

**Daily backup**:
```
Schedule (nightly 2 AM)
  → Postgres (export data)
  → Google Drive (upload)
  → Email (confirmation)
```

**Monitoring**:
```
Schedule (every 5 min)
  → HTTP Request (health check)
  → IF (down) → PagerDuty alert
```

Use `search_templates({query: "schedule"})` to find more!

---

## Checklist for Scheduled Workflows

### Planning
- [ ] Define schedule frequency (interval, cron, days & hours)
- [ ] Set workflow timezone
- [ ] Estimate execution duration
- [ ] Plan for failures and retries
- [ ] Consider timezone and DST

### Implementation
- [ ] Configure Schedule Trigger
- [ ] Set workflow timezone in settings
- [ ] Add early exit for no-op cases
- [ ] Implement batch processing for large data
- [ ] Add execution logging

### Error Handling
- [ ] Create Error Trigger workflow
- [ ] Implement retry logic
- [ ] Add alert notifications
- [ ] Log errors for analysis
- [ ] Handle partial failures gracefully

### Monitoring
- [ ] Log each execution (start, end, status)
- [ ] Track metrics (duration, records, success rate)
- [ ] Set up daily/weekly summaries
- [ ] Alert on consecutive failures
- [ ] Monitor resource usage

### Testing
- [ ] Test with Manual Trigger first
- [ ] Verify timezone behavior
- [ ] Test error scenarios
- [ ] Check for overlapping executions
- [ ] Validate output quality

### Deployment
- [ ] Document workflow purpose
- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Activate workflow in n8n UI ⚠️ **Manual activation required** (API/MCP cannot activate)
- [ ] Test in production (short interval first)
- [ ] Monitor first few executions

---

## Advanced Patterns

### Dynamic Scheduling
**Change schedule based on conditions**:

```
Schedule (check every hour) → Code (check if it's time to run)
  → IF (business hours AND weekday)
    └─ Execute workflow
  → ELSE
    └─ Skip
```

### Dependent Schedules
**Chain workflows**:

```
Workflow A (daily 2 AM): Data sync
  → On completion → Trigger Workflow B

Workflow B: Generate report (depends on fresh data)
```

### Conditional Execution
**Skip based on external factors**:

```
Schedule → HTTP Request (check feature flag)
  → IF (feature enabled)
    └─ Execute
  → ELSE
    └─ Skip
```

---

## Summary

**Key Points**:
1. **Set workflow timezone** explicitly
2. **Batch processing** for large datasets
3. **Error handling** is critical (Error Trigger + retries)
4. **Prevent overlaps** with execution locks
5. **Monitor and log** all executions

**Pattern**: Schedule → Fetch → Process → Deliver → Log

**Schedule Modes**:
- **Interval**: Simple recurring (every X minutes/hours)
- **Days & Hours**: Specific days and times
- **Cron**: Advanced complex schedules

**Related**:
- [http_api_integration.md](http_api_integration.md) - Fetching data on schedule
- [database_operations.md](database_operations.md) - Scheduled database tasks
- [webhook_processing.md](webhook_processing.md) - Alternative to scheduling
