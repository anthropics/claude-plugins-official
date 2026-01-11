---
description: List all scheduled scraping jobs
argument-hint: [status] [page]
allowed-tools: []
---

# List Jobs Command

Retrieve a paginated list of all scheduled jobs for your account.

## Usage

```
/list-jobs [status] [page]
```

## Arguments

- **status** (optional): Filter by status (queued, processing, completed, failed)
- **page** (optional): Page number (default: 1)

## Examples

```
/list-jobs
/list-jobs completed
/list-jobs processing 2
```

## Response

Returns paginated list with:
- Job ID, name, and service type
- Cron expression and status
- Last run and next run timestamps
- Job configuration
- Webhook URL (if set)

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Default page size: 20 jobs
- Use status filter to find specific job states
- No credits consumed for this operation

