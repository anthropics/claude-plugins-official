# Cookie Scanner Skill

Use this skill when the user needs to:
- Scan a website for cookies
- Detect tracking technologies on a domain
- Audit cookie usage for compliance
- Identify third-party cookies

## Capabilities

This skill can:
1. Initiate cookie scans via GetCookies API
2. Retrieve and display scan results
3. Classify cookies by category (necessary, functional, analytics, marketing)
4. Identify cookie providers and purposes
5. Check for unclassified or unknown cookies

## API Integration

### Required Environment
- `GETCOOKIES_API_KEY`: API key for authentication

### Endpoints Used
- `GET /api/v1/domains` - List user's domains
- `POST /api/v1/domains/{id}/scans` - Start a scan
- `GET /api/v1/scans/{id}` - Check scan status
- `GET /api/v1/scans/{id}/cookies` - Get scan results

## Usage Examples

### Scan a domain
```
User: "Scan example.com for cookies"
Assistant: [Uses cookie-scanner skill to initiate scan and display results]
```

### Check scan status
```
User: "What's the status of my cookie scan?"
Assistant: [Checks pending scans and reports status]
```

### List detected cookies
```
User: "What cookies does my site use?"
Assistant: [Retrieves and displays categorized cookie list]
```

## Response Format

When reporting scan results, format as:
- Total cookies found
- Breakdown by category
- List of top/notable cookies with purposes
- Any compliance concerns (unknown cookies, long durations)
- Recommendations for improvement
