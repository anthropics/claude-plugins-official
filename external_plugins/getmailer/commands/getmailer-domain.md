# GetMailer Domain Manager

Verify and manage sending domains with DKIM, SPF, and DMARC.

## Usage

```
/getmailer-domain [action] [domain]
```

## Actions

- `list` - List all configured domains
- `add [domain]` - Add a new sending domain
- `verify [domain]` - Check domain verification status
- `dns [domain]` - Show required DNS records
- `status [domain]` - Full domain health check

## What This Does

1. Manages sending domains in GetMailer
2. Generates DKIM keys and DNS records
3. Validates SPF, DKIM, and DMARC configuration
4. Provides copy-paste DNS records

## Examples

### List domains
```
/getmailer-domain list
```

### Add a new domain
```
/getmailer-domain add newdomain.com
```

### Get DNS records to add
```
/getmailer-domain dns example.com
```

### Verify domain setup
```
/getmailer-domain verify example.com
```

## DNS Records Required

### DKIM Record
```
Type: TXT
Host: getmailer._domainkey
Value: v=DKIM1; k=rsa; p=MIGfMA0GCS...
```

### SPF Record
```
Type: TXT
Host: @
Value: v=spf1 include:spf.getmailer.co ~all
```

### DMARC Record
```
Type: TXT
Host: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

### Return-Path (CNAME)
```
Type: CNAME
Host: bounce
Value: bounce.getmailer.co
```

## Example Output

```
Domain: example.com
Status: Verified ✅

Authentication:
├── DKIM: ✅ Configured and passing
├── SPF: ✅ Configured and passing
├── DMARC: ⚠️ No DMARC record found
└── Return-Path: ✅ Configured

Recommendation:
Add DMARC record to improve deliverability:

_dmarc.example.com TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
```

## API Endpoints

- `GET /api/domains` - List domains
- `POST /api/domains` - Add domain
- `GET /api/domains/{id}` - Get domain details
- `POST /api/domains/{id}/verify` - Trigger verification
- `GET /api/domains/{id}/dns` - Get DNS records

---

When the user runs this command:

1. Parse the action and domain
2. For add: Create domain and show DNS records to add
3. For verify: Check DNS propagation and validation
4. For dns: Display all required DNS records with copy buttons
5. For status: Full health check with recommendations
