# GetMailer Template Manager

Create, list, and preview email templates.

## Usage

```
/getmailer-template [action] [name]
```

## Actions

- `list` - List all templates
- `create [name]` - Create a new template
- `preview [name]` - Preview a template with sample data
- `generate [name]` - Generate a template from a description
- `edit [name]` - Edit an existing template

## What This Does

1. Manages email templates stored in GetMailer
2. Supports React Email component-based templates
3. Provides variable substitution preview
4. Generates templates from natural language descriptions

## Examples

### List all templates
```
/getmailer-template list
```

### Create a welcome email template
```
/getmailer-template create welcome
```

### Generate a template from description
```
/getmailer-template generate "A password reset email with a reset link button"
```

### Preview with sample data
```
/getmailer-template preview welcome --vars '{"name": "John", "company": "Acme"}'
```

## Template Variables

Templates support Handlebars-style variables:
- `{{firstName}}` - First name
- `{{email}}` - Recipient email
- `{{unsubscribeUrl}}` - Unsubscribe link
- Custom variables defined in template

## Template Structure

```typescript
// React Email template example
import { Html, Head, Body, Container, Text, Button } from '@react-email/components';

export default function WelcomeEmail({ firstName, loginUrl }) {
  return (
    <Html>
      <Head />
      <Body>
        <Container>
          <Text>Welcome, {firstName}!</Text>
          <Button href={loginUrl}>Log In</Button>
        </Container>
      </Body>
    </Html>
  );
}
```

## API Endpoints

- `GET /api/templates` - List templates
- `POST /api/templates` - Create template
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `POST /api/templates/{id}/preview` - Preview with variables

---

When the user runs this command:

1. Parse the action (list/create/preview/generate/edit)
2. For create/generate: Guide through template creation
3. For preview: Render template with sample or provided variables
4. For list: Display templates with names, subjects, last updated
5. Show helpful next steps (edit, send test, etc.)
