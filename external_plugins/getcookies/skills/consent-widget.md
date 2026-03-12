# Consent Widget Skill

Use this skill when the user needs to:
- Configure a cookie consent banner
- Generate widget embed code
- Customize consent banner appearance
- Deploy consent management to their website

## Capabilities

This skill can:
1. Configure widget settings (position, theme, colors)
2. Set compliance mode (GDPR, CCPA, TCF)
3. Generate embed code snippets
4. Preview widget configurations
5. Deploy configurations to GetCookies

## API Integration

### Required Environment
- `GETCOOKIES_API_KEY`: API key for authentication

### Endpoints Used
- `GET /api/v1/domains` - List user's domains
- `GET /api/v1/domains/{id}/widget` - Get current widget config
- `POST /api/v1/domains/{id}/widget` - Save widget config
- `GET /api/v1/widget/config/{id}` - Get public widget config

## Configuration Options

### Position
- `bottom` - Full-width banner at page bottom
- `bottom-left` - Corner popup, bottom left
- `bottom-right` - Corner popup, bottom right
- `top` - Full-width banner at page top
- `center` - Centered modal overlay

### Theme
- `light` - Light background with dark text
- `dark` - Dark background with light text
- `custom` - Custom colors

### Compliance Modes
- `gdpr` - GDPR compliant (EU)
- `ccpa` - CCPA compliant (California)
- `tcf` - IAB TCF v2.2 compliant
- `all` - All regulations

### Features
- Google Consent Mode v2
- Geo-targeting
- Auto script blocking
- Custom branding

## Usage Examples

### Configure a widget
```
User: "Set up a cookie consent banner for my site"
Assistant: [Guides through configuration and generates embed code]
```

### Get embed code
```
User: "Give me the cookie banner code for example.com"
Assistant: [Retrieves widget config and provides embed snippet]
```

## Output Format

Always provide:
1. Configuration summary
2. Ready-to-use embed code
3. Installation instructions
4. Link to preview/test
