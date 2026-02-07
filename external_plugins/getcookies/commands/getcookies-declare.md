# GetCookies Declaration Generator

Generate a cookie declaration table for your privacy policy or cookie policy page.

## Usage

```
/getcookies-declare [domain] [--format html|markdown|json]
```

## Arguments

- `domain` (optional): The domain to generate declaration for
- `--format`: Output format (default: markdown)

## What This Does

1. Fetches all detected cookies for the domain
2. Groups them by category
3. Generates a formatted declaration table
4. Includes cookie name, purpose, duration, and type

## Output Formats

### Markdown (default)
```markdown
## Cookies We Use

### Necessary Cookies
| Cookie | Purpose | Duration | Type |
|--------|---------|----------|------|
| session_id | Maintains user session | Session | First-party |

### Analytics Cookies
| Cookie | Purpose | Duration | Type |
|--------|---------|----------|------|
| _ga | Google Analytics tracking | 2 years | Third-party |
```

### HTML
```html
<div class="cookie-declaration">
  <h2>Cookies We Use</h2>
  <h3>Necessary Cookies</h3>
  <table>
    <thead>
      <tr><th>Cookie</th><th>Purpose</th><th>Duration</th><th>Type</th></tr>
    </thead>
    <tbody>
      <tr><td>session_id</td><td>Maintains user session</td><td>Session</td><td>First-party</td></tr>
    </tbody>
  </table>
</div>
```

### JSON
```json
{
  "necessary": [
    {"name": "session_id", "purpose": "Maintains user session", "duration": "Session", "type": "first-party"}
  ],
  "analytics": [...]
}
```

## Features

- Auto-updates when you re-scan your domain
- Includes all classified cookies
- Groups by category with clear headings
- Ready to paste into your privacy policy

---

When the user runs this command:

1. Fetch latest scan data for the domain
2. Group cookies by category
3. Format according to requested output type
4. Display the declaration
5. Offer to copy to clipboard or save to file
