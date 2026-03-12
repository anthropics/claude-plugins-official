# Deliverability Skill

Use this skill when the user needs to:
- Check sending reputation
- Diagnose delivery issues
- Monitor email metrics
- Improve deliverability

## Capabilities

This skill can:
1. Check reputation score and metrics
2. Monitor blacklist status
3. Validate domain authentication (DKIM, SPF, DMARC)
4. Analyze bounce and complaint rates
5. Provide improvement recommendations

## API Integration

### Required Environment
- `GETMAILER_API_KEY`: API key for authentication

### Endpoints Used
- `GET /api/reputation` - Reputation overview
- `GET /api/reputation/metrics` - Detailed metrics
- `GET /api/reputation/health` - Health checks
- `GET /api/domains/{id}/verify` - Domain verification
- `GET /api/analytics/deliverability` - Deliverability stats

## Usage Examples

### Check reputation
```
User: "How is my email reputation?"
Assistant: [Fetches and displays reputation score with details]
```

### Diagnose issues
```
User: "My emails are going to spam"
Assistant: [Checks authentication, blacklists, content issues]
```

### Monitor metrics
```
User: "Show me my deliverability metrics for the past week"
Assistant: [Displays delivery, bounce, complaint, open rates]
```

## Reputation Factors

### Authentication
- DKIM signature validity
- SPF record alignment
- DMARC policy and reporting

### Engagement
- Open rates
- Click rates
- Reply rates
- Unsubscribe rates

### Quality
- Bounce rates (hard/soft)
- Complaint rates
- Spam trap hits
- List hygiene

### Infrastructure
- IP reputation
- Domain age
- Sending patterns
- Warmup status

## Health Indicators

- **Green (90-100)**: Excellent reputation, full capacity
- **Yellow (70-89)**: Good, monitor for issues
- **Orange (50-69)**: Warning, reduce volume
- **Red (0-49)**: Critical, sending paused

## Response Format

When reporting deliverability:
- Overall score with trend
- Key metrics with benchmarks
- Any active issues/alerts
- Specific recommendations
- Links to detailed reports
