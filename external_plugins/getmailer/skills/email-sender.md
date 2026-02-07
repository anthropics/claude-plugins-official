# Email Sender Skill

Use this skill when the user needs to:
- Send transactional emails
- Send test emails during development
- Trigger email notifications
- Test email templates

## Capabilities

This skill can:
1. Send single emails via GetMailer API
2. Send batch emails
3. Use templates with variable substitution
4. Schedule emails for later delivery
5. Track delivery status

## API Integration

### Required Environment
- `GETMAILER_API_KEY`: API key for authentication
- `GETMAILER_DEFAULT_FROM`: Default sender address (optional)

### Endpoints Used
- `POST /api/emails/send` - Send single email
- `POST /api/emails/batch` - Send batch emails
- `GET /api/emails/{id}` - Get email status
- `GET /api/emails/{id}/events` - Get delivery events

## Usage Examples

### Send a quick test email
```
User: "Send a test email to john@example.com"
Assistant: [Uses email-sender skill to send and confirm delivery]
```

### Send using a template
```
User: "Send the welcome email to our new user"
Assistant: [Sends template-based email with user variables]
```

### Check delivery status
```
User: "Did my last email get delivered?"
Assistant: [Checks email status and delivery events]
```

## Email Options

- `to`: Recipient(s)
- `from`: Sender address
- `subject`: Subject line
- `html`: HTML content
- `text`: Plain text fallback
- `templateId`: Template to use
- `variables`: Template variables
- `scheduledFor`: Schedule for later
- `testMode`: Simulate without sending

## Response Format

When reporting send results:
- Confirmation of send
- Message ID for tracking
- Delivery status updates
- Any errors or warnings
