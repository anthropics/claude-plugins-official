---
description: Pause a scheduled scraping job temporarily
argument-hint: <job-id>
allowed-tools: []
---

# Pause Job Command

Pause a scheduled job temporarily. The job will not run until resumed.

## Usage

```
/pause-job <job-id>
```

## Arguments

- **job-id** (required): The UUID of the scheduled job to pause

## Examples

```
/pause-job 123e4567-e89b-12d3-a456-426614174000
```

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- No credits consumed for this operation
- Job remains in database but won't execute
- Use /resume-job to reactivate


