---
description: Resume a paused scheduled scraping job
argument-hint: <job-id>
allowed-tools: []
---

# Resume Job Command

Resume a paused scheduled job. The job will continue running according to its cron schedule.

## Usage

```
/resume-job <job-id>
```

## Arguments

- **job-id** (required): The UUID of the scheduled job to resume

## Examples

```
/resume-job 123e4567-e89b-12d3-a456-426614174000
```

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- No credits consumed for this operation
- Job will resume its normal schedule
- Use /pause-job to temporarily stop

