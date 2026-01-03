# GetCookies Widget Configurator

Configure and generate a consent banner widget for your website.

## Usage

```
/getcookies-widget [domain]
```

## Arguments

- `domain` (optional): The domain to configure the widget for

## What This Does

1. Guides you through widget configuration options
2. Generates the widget configuration JSON
3. Provides the embed code for your website
4. Optionally deploys the configuration to GetCookies

## Configuration Options

### Position
- `bottom` (default) - Full-width banner at bottom
- `bottom-left` / `bottom-right` - Corner popup
- `top` - Full-width banner at top
- `center` - Modal in center of screen

### Theme
- `light` - Light background, dark text
- `dark` - Dark background, light text
- `custom` - Custom colors

### Compliance Mode
- `gdpr` - GDPR (EU) compliant
- `ccpa` - CCPA (California) compliant
- `both` - Both GDPR and CCPA
- `tcf` - IAB TCF v2.2 compliant

### Features
- Google Consent Mode integration
- Geo-targeting (show only in specific regions)
- Auto-blocking of scripts before consent
- Custom branding and colors

## Example Output

```html
<!-- GetCookies Consent Widget -->
<script
  src="https://getcookies.co/widget.js"
  data-domain-id="abc123"
  data-position="bottom"
  data-theme="light"
  async>
</script>
```

## Interactive Mode

When run without arguments, enters interactive mode:

1. Select domain from your account
2. Choose position and theme
3. Configure compliance mode
4. Set custom colors (optional)
5. Enable/disable features
6. Preview the widget
7. Generate and copy embed code

---

When the user runs this command:

1. List available domains from GetCookies API
2. Let user select or enter a domain
3. Present configuration options interactively
4. Generate widget configuration
5. Show embed code ready to copy
6. Offer to save configuration to GetCookies
