# GetMailer Send Email

Send a test email or quick transactional email via GetMailer.

## Usage

```
/getmailer-send [--to email] [--subject "Subject"] [--template name]
```

## Arguments

- `--to`: Recipient email address (defaults to GETMAILER_TEST_EMAIL)
- `--subject`: Email subject line
- `--template`: Template name to use (optional)
- `--test`: Enable test mode (no actual delivery)

## What This Does

1. Sends an email via GetMailer's transactional API
2. Supports plain text, HTML, or template-based emails
3. Returns delivery status and message ID
4. Can simulate delivery in test mode

## Examples

### Quick test email
```
/getmailer-send --to test@example.com --subject "Test"
```

### Send using a template
```
/getmailer-send --to user@example.com --template welcome --vars '{"name": "John"}'
```

### Test mode (no delivery)
```
/getmailer-send --to test@example.com --test
```

## Interactive Mode

When run without arguments:

1. Ask for recipient email
2. Ask for subject line
3. Ask for content (plain text or offer to generate HTML)
4. Confirm and send
5. Display delivery confirmation

## API Endpoint

`POST /api/emails/send`

## Request Body

```json
{
  "to": "recipient@example.com",
  "from": "sender@yourdomain.com",
  "subject": "Your Subject",
  "html": "<p>Email content</p>",
  "text": "Plain text fallback",
  "templateId": "optional-template-id",
  "variables": { "name": "John" },
  "testMode": false
}
```

---

When the user runs this command:

1. Gather required information (to, subject, content)
2. Use GETMAILER_DEFAULT_FROM if from address not specified
3. Call GetMailer API to send the email
4. Display confirmation with message ID
5. Offer to check delivery status
