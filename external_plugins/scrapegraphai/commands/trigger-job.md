---
description: Manually trigger a scheduled job to run immediately
argument-hint: <job-id>
allowed-tools: []
---

# Trigger Job Command

Execute a scheduled job immediately, outside of its normal cron schedule.

## Usage

```
/trigger-job <job-id>
```

## Arguments

- **job-id** (required): The UUID of the scheduled job to trigger

## Examples

```
/trigger-job 123e4567-e89b-12d3-a456-426614174000
```

## Response

Returns:
- Execution ID for the triggered run
- Status confirmation

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Job will execute immediately
- Normal credits apply for the execution
- Use to test jobs or run them on-demand
- Check execution status with job execution history


