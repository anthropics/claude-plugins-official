# Email Templates Skill

Use this skill when the user needs to:
- Create email templates
- Edit existing templates
- Preview templates with data
- Generate templates from descriptions

## Capabilities

This skill can:
1. List and search email templates
2. Create new templates (HTML or React Email)
3. Edit template content and settings
4. Preview templates with sample data
5. Generate templates from natural language

## API Integration

### Required Environment
- `GETMAILER_API_KEY`: API key for authentication

### Endpoints Used
- `GET /api/templates` - List templates
- `POST /api/templates` - Create template
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `POST /api/templates/{id}/preview` - Preview with data
- `DELETE /api/templates/{id}` - Delete template

## Usage Examples

### Create a template
```
User: "Create an email template for password reset"
Assistant: [Creates template with reset link, styling, and variables]
```

### Preview a template
```
User: "Show me the welcome email with John's data"
Assistant: [Renders template with provided variables]
```

### Generate from description
```
User: "I need a shipping confirmation email with tracking number"
Assistant: [Generates complete template based on description]
```

## Template Types

### HTML Templates
Standard HTML with variable placeholders:
```html
<h1>Welcome, {{firstName}}!</h1>
<p>Click <a href="{{loginUrl}}">here</a> to log in.</p>
```

### React Email Templates
Component-based templates:
```tsx
export default function Welcome({ firstName, loginUrl }) {
  return (
    <Html>
      <Body>
        <Heading>Welcome, {firstName}!</Heading>
        <Button href={loginUrl}>Log In</Button>
      </Body>
    </Html>
  );
}
```

## Template Variables

Standard variables available:
- `{{firstName}}`, `{{lastName}}` - Contact name
- `{{email}}` - Recipient email
- `{{unsubscribeUrl}}` - Unsubscribe link
- `{{preferencesUrl}}` - Email preferences link
- Custom variables as defined

## Response Format

When working with templates:
- Template name and ID
- Subject line
- Variable list
- Preview link
- Last updated timestamp
