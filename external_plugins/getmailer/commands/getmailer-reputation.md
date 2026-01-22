# GetMailer Reputation Monitor

Check your sending reputation and deliverability metrics.

## Usage

```
/getmailer-reputation [--domain domain.com] [--days 7]
```

## Arguments

- `--domain`: Specific domain to check (optional, shows all if omitted)
- `--days`: Number of days to include in metrics (default: 7)

## What This Does

1. Fetches your current reputation score (0-100)
2. Shows key deliverability metrics
3. Alerts on any issues (blacklists, high bounce rates)
4. Provides recommendations for improvement

## Metrics Shown

### Reputation Score
- **90-100**: Excellent - Full sending capacity
- **70-89**: Good - Monitor for issues
- **50-69**: Warning - Reduced sending recommended
- **0-49**: Critical - Sending paused, action required

### Key Metrics
- **Delivery Rate**: % of emails successfully delivered
- **Bounce Rate**: % of emails bounced (hard + soft)
- **Complaint Rate**: % of spam complaints
- **Open Rate**: % of emails opened
- **Click Rate**: % of emails with clicks
- **Unsubscribe Rate**: % of unsubscribes

### Health Checks
- Blacklist status (RBL checks)
- Authentication status (DKIM, SPF, DMARC)
- IP warmup status
- Sending volume trends

## Example Output

```
Reputation Report: yourdomain.com
Period: Last 7 days

Overall Score: 94/100 ✅ Excellent

Metrics:
├── Delivery Rate: 98.5%
├── Bounce Rate: 0.8%
├── Complaint Rate: 0.02%
├── Open Rate: 24.3%
├── Click Rate: 3.2%
└── Unsubscribe Rate: 0.1%

Health Status:
├── ✅ Not on any blacklists
├── ✅ DKIM: Passing
├── ✅ SPF: Passing
├── ✅ DMARC: Passing
└── ✅ IP fully warmed up

Recommendations:
- Consider segmenting inactive subscribers
- Open rate is slightly below industry average (27%)
```

## API Endpoints

- `GET /api/reputation` - Get reputation overview
- `GET /api/reputation/metrics` - Detailed metrics
- `GET /api/reputation/health` - Health check status

---

When the user runs this command:

1. Fetch reputation data from GetMailer API
2. Calculate and display overall score
3. Show key metrics with trend indicators
4. Check health status (blacklists, auth, warmup)
5. Provide actionable recommendations
