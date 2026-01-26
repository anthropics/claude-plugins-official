---
description: Create a new scheduled scraping job with cron expression
argument-hint: <job-name> <service-type> <cron> <config-json>
allowed-tools: []
---

# Schedule Job Command

Create a new scheduled job that will run automatically based on a cron expression. Supports all available service types.

## Usage

```
/schedule-job <job-name> <service-type> <cron-expression> <config-json>
```

## Arguments

- **job-name** (required): Human-readable name for the scheduled job
- **service-type** (required): Type of service (smartscraper, searchscraper, markdownify, smartcrawler, agenticscrapper)
- **cron-expression** (required): Standard 5-field cron expression in UTC (minute hour day month day_of_week)
- **config-json** (required): JSON configuration matching the service's request schema

## Examples

```
/schedule-job "Daily News Scrape" smartscraper "0 9 * * *" '{"user_prompt":"Extract headlines","website_url":"https://news.example.com"}'
/schedule-job "Weekly Product Check" searchscraper "0 10 * * 1" '{"user_prompt":"Find latest products","num_results":5}'
```

## Cron Expression Format

5-field format: `minute hour day month day_of_week`

- `0 9 * * *` - Daily at 9:00 AM UTC
- `0 10 * * 1` - Every Monday at 10:00 AM UTC
- `*/30 * * * *` - Every 30 minutes
- `0 0 1 * *` - First day of every month at midnight

## Features

- Automated recurring scraping
- All service types supported
- Cron-based scheduling
- Webhook notifications
- Pause/resume capability
- Manual trigger option

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Cron expression must be in UTC timezone
- Config JSON must match the service type's request schema
- Use webhook_url for result notifications
- Check job status with scheduled jobs list command


