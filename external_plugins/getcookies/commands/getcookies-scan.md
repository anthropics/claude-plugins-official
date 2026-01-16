# GetCookies Domain Scanner

Scan a website domain for cookies and tracking technologies.

## Usage

```
/getcookies-scan [domain]
```

## Arguments

- `domain` (optional): The domain to scan (e.g., `example.com`). If not provided, will prompt for input.

## What This Does

1. Initiates a cookie scan on the specified domain using GetCookies API
2. Crawls the website using headless browser automation
3. Detects all cookies set by first-party and third-party scripts
4. Classifies cookies into categories:
   - **Necessary**: Essential for website functionality
   - **Functional**: Enhance user experience
   - **Analytics**: Track user behavior and site performance
   - **Marketing**: Used for advertising and retargeting
5. Returns a summary with detected cookies and their purposes

## Example Output

```
Domain: example.com
Scan Status: Completed
Pages Crawled: 15

Cookies Found: 23
├── Necessary: 5
├── Functional: 3
├── Analytics: 8
├── Marketing: 6
└── Unknown: 1

Top Cookies:
- _ga (Analytics) - Google Analytics tracking
- _fbp (Marketing) - Facebook Pixel
- session_id (Necessary) - Session management
```

## Requirements

- `GETCOOKIES_API_KEY` environment variable must be set
- Domain must be registered in your GetCookies account

## API Endpoint

`POST /api/v1/domains/{id}/scans`

---

When the user runs this command:

1. If no domain is provided, ask: "Which domain would you like to scan?"
2. Look up the domain ID in GetCookies using the API
3. Initiate a scan using `POST /api/v1/domains/{id}/scans`
4. Poll for scan completion using `GET /api/v1/scans/{id}`
5. Once complete, fetch cookies using `GET /api/v1/scans/{id}/cookies`
6. Display a formatted summary of the results
7. Offer to generate a cookie declaration or check compliance
