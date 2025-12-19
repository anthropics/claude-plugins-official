---
description: Get execution history for a scheduled job
argument-hint: <job-id> [page]
allowed-tools: []
---

# Job Executions Command

Retrieve execution history for a specific scheduled job, showing all past runs and their results.

## Usage

```
/job-executions <job-id> [page]
```

## Arguments

- **job-id** (required): The UUID of the scheduled job
- **page** (optional): Page number (default: 1)

## Examples

```
/job-executions 123e4567-e89b-12d3-a456-426614174000
/job-executions 123e4567-e89b-12d3-a456-426614174000 2
```

## Response

Returns paginated list with:
- Execution ID and status
- Start and finish timestamps
- Result data (if completed)
- Error messages (if failed)

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Default page size: 20 executions
- No credits consumed for this operation
- Use to monitor job performance and debug failures

