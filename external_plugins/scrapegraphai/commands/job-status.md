---
description: Get details of a specific scheduled job
argument-hint: <job-id>
allowed-tools: []
---

# Job Status Command

Retrieve details of a specific scheduled job including configuration, status, and execution history.

## Usage

```
/job-status <job-id>
```

## Arguments

- **job-id** (required): The UUID of the scheduled job

## Examples

```
/job-status 123e4567-e89b-12d3-a456-426614174000
```

## Response

Returns:
- Job ID, name, and service type
- Cron expression and status
- Job configuration
- Last run and next run timestamps
- Webhook URL (if set)
- Created and updated timestamps

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- No credits consumed for this operation
- Use to check job configuration and schedule

