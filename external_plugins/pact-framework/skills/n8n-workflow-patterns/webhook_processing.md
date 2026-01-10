# Webhook Processing Pattern

**Use Case**: Receive HTTP requests from external systems and process them instantly.

---

## Pattern Structure

```
Webhook → [Validate] → [Transform] → [Action] → [Response/Notify]
```

**Key Characteristic**: Instant event-driven processing

---

## Core Components

### 1. Webhook Node (Trigger)
**Purpose**: Create HTTP endpoint to receive data

**Configuration**:
```javascript
{
  path: "form-submit",        // URL path: https://n8n.example.com/webhook/form-submit
  httpMethod: "POST",         // GET, POST, PUT, DELETE
  responseMode: "onReceived", // or "lastNode" for custom response
  responseData: "allEntries"  // or "firstEntryJson"
}
```

**Critical Gotcha**: Data is nested under `$json.body`
```javascript
❌ {{$json.email}}
✅ {{$json.body.email}}
```

### 2. Validation (Optional but Recommended)
**Purpose**: Verify incoming data before processing

**Options**:
- **IF node** - Check required fields exist
- **Code node** - Custom validation logic
- **Stop and Error** - Fail gracefully with message

**Example**:
```javascript
// IF node condition
{{$json.body.email}} is not empty AND
{{$json.body.name}} is not empty
```

### 3. Transformation
**Purpose**: Map webhook data to desired format

**Typical nodes**:
- **Set** - Field mapping
- **Code** - Complex transformations

**Example** (Set node):
```javascript
{
  "user_email": "={{$json.body.email}}",
  "user_name": "={{$json.body.name}}",
  "timestamp": "={{$now}}"
}
```

### 4. Action
**Purpose**: Do something with the data

**Common actions**:
- Store in database (Postgres, MySQL, MongoDB)
- Send notification (Slack, Email, Discord)
- Call another API (HTTP Request)
- Update external system (CRM, support ticket)

### 5. Response (If responseMode: "lastNode")
**Purpose**: Send custom HTTP response

**Webhook Response Node**:
```javascript
{
  statusCode: 200,
  headers: {
    "Content-Type": "application/json"
  },
  body: {
    "status": "success",
    "message": "Form received"
  }
}
```

---

## Common Use Cases

### 1. Form Submissions
**Flow**: Form → Webhook → Validate → Database → Email Confirmation

**Example**:
```
1. Webhook (path: "contact-form", POST)
2. IF (check email & message not empty)
3. Postgres (insert into contacts table)
4. Email (send confirmation to user)
5. Slack (notify team in #leads)
6. Webhook Response ({"status": "success"})
```

**Real Data Access**:
```javascript
Name: {{$json.body.name}}
Email: {{$json.body.email}}
Message: {{$json.body.message}}
```

### 2. Payment Webhooks (Stripe, PayPal)
**Flow**: Payment Provider → Webhook → Verify → Update Database → Send Receipt

**Security**: Verify webhook signatures
```javascript
// Code node - verify Stripe signature
const crypto = require('crypto');
const signature = $input.item.headers['stripe-signature'];
const secret = $credentials.stripeWebhookSecret;

// Verify signature matches
const expectedSig = crypto
  .createHmac('sha256', secret)
  .update($input.item.body)
  .digest('hex');

if (signature !== expectedSig) {
  throw new Error('Invalid webhook signature');
}

return $input.item.body; // Return validated body
```

### 3. Chat Platform Integrations (Slack, Discord, Teams)
**Flow**: Chat Command → Webhook → Process → Respond

**Example** (Slack slash command):
```
1. Webhook (path: "slack-command", POST)
2. Code (parse Slack payload: $json.body.text, $json.body.user_id)
3. HTTP Request (fetch data from API)
4. Set (format Slack message)
5. Webhook Response (immediate Slack response)
```

**Slack Data Access**:
```javascript
Command: {{$json.body.command}}
Text: {{$json.body.text}}
User ID: {{$json.body.user_id}}
Channel ID: {{$json.body.channel_id}}
```

### 4. GitHub/GitLab Webhooks
**Flow**: Git Event → Webhook → Parse → Notify/Deploy

**Example** (new PR notification):
```
1. Webhook (path: "github", POST)
2. IF (check $json.body.action equals "opened")
3. Set (extract PR details: title, author, url)
4. Slack (notify #dev-team)
5. Webhook Response (200 OK)
```

**GitHub Data Access**:
```javascript
Event Type: {{$json.headers['x-github-event']}}
Action: {{$json.body.action}}
PR Title: {{$json.body.pull_request.title}}
Author: {{$json.body.pull_request.user.login}}
URL: {{$json.body.pull_request.html_url}}
```

### 5. IoT Device Data
**Flow**: Device → Webhook → Validate → Store → Alert (if threshold)

**Example** (temperature sensor):
```
1. Webhook (path: "sensor-data", POST)
2. Set (extract sensor readings)
3. Postgres (insert into sensor_readings)
4. IF (temperature > 80)
5. Email (alert admin)
```

---

## Webhook Data Structure

### Standard Structure
```json
{
  "headers": {
    "content-type": "application/json",
    "user-agent": "...",
    "x-custom-header": "..."
  },
  "params": {
    "id": "123"  // From URL: /webhook/form/:id
  },
  "query": {
    "token": "abc"  // From URL: /webhook/form?token=abc
  },
  "body": {
    // ⚠️ YOUR DATA IS HERE!
    "name": "John",
    "email": "john@example.com"
  }
}
```

### Accessing Different Parts
```javascript
// Headers
{{$json.headers['content-type']}}
{{$json.headers['x-api-key']}}

// URL Parameters
{{$json.params.id}}

// Query Parameters
{{$json.query.token}}
{{$json.query.page}}

// Body (MOST COMMON)
{{$json.body.email}}
{{$json.body.user.name}}
{{$json.body.items[0].price}}
```

---

## Authentication & Security

### 1. Query Parameter Token
**Simple but less secure**
```javascript
// IF node - validate token
{{$json.query.token}} equals "your-secret-token"
```

### 2. Header-Based Auth
**Better security**
```javascript
// IF node - check header
{{$json.headers['x-api-key']}} equals "your-api-key"
```

### 3. Signature Verification
**Best security** (for webhooks from services like Stripe, GitHub)
```javascript
// Code node
const crypto = require('crypto');
const signature = $input.item.headers['x-signature'];
const secret = $credentials.webhookSecret;

const calculatedSig = crypto
  .createHmac('sha256', secret)
  .update(JSON.stringify($input.item.body))
  .digest('hex');

if (signature !== `sha256=${calculatedSig}`) {
  throw new Error('Invalid signature');
}

return $input.item.body;
```

### 4. IP Whitelist
**Restrict access by IP** (n8n workflow settings)
- Configure in workflow settings
- Only allow specific IP ranges
- Use for internal systems

---

## Response Modes

### onReceived (Default)
**Behavior**: Immediate 200 OK response, workflow continues in background

**Use when**:
- Long-running workflows
- Response doesn't depend on workflow result
- Fire-and-forget processing

**Configuration**:
```javascript
{
  responseMode: "onReceived",
  responseCode: 200
}
```

### lastNode (Custom Response)
**Behavior**: Wait for workflow completion, send custom response

**Use when**:
- Need to return data to caller
- Synchronous processing required
- Form submissions with confirmation

**Configuration**:
```javascript
{
  responseMode: "lastNode"
}
```

**Then add Webhook Response node**:
```javascript
{
  statusCode: 200,
  headers: {
    "Content-Type": "application/json"
  },
  body: {
    "id": "={{$json.record_id}}",
    "status": "success"
  }
}
```

---

## Error Handling

### Pattern 1: Try-Catch with Error Trigger
```
Main Flow:
  Webhook → [nodes...] → Success Response

Error Flow:
  Error Trigger → Log Error → Slack Alert → Error Response
```

**Error Trigger Configuration**:
```javascript
{
  workflowId: "current-workflow-id"
}
```

**Error Response** (if responseMode: "lastNode"):
```javascript
{
  statusCode: 500,
  body: {
    "status": "error",
    "message": "Processing failed"
  }
}
```

### Pattern 2: Validation Early Exit
```
Webhook → IF (validate) → [True: Process]
                       └→ [False: Error Response]
```

**False Branch Response**:
```javascript
{
  statusCode: 400,
  body: {
    "status": "error",
    "message": "Invalid data: missing email"
  }
}
```

### Pattern 3: Continue On Fail
**Per-node setting**: Continue even if node fails

**Use case**: Non-critical notifications
```
Webhook → Database (critical) → Slack (continueOnFail: true)
```

---

## Testing Webhooks

### 1. Use Manual Trigger
Replace Webhook with Manual Trigger for testing:
```
Manual Trigger → [set test data] → rest of workflow
```

### 2. Use curl
```bash
curl -X POST https://n8n.example.com/webhook/form-submit \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

### 3. Use Postman/Insomnia
- Create request collection
- Test different payloads
- Verify responses

### 4. Webhook.site
- Use webhook.site for testing
- Copy webhook.site URL to your service
- View requests and debug

---

## Performance Considerations

### Large Payloads
- Webhook timeout: 120 seconds (default)
- For large data, consider async processing:
  ```
  Webhook → Queue (Redis/DB) → Response (immediate)

  Separate Workflow:
  Schedule → Check Queue → Process
  ```

### High Volume
- Use "Execute Once" mode if processing all items together
- Consider rate limiting
- Monitor execution times
- Scale n8n instance if needed

### Retries
- Webhook calls typically don't retry automatically
- Implement retry logic on caller side
- Or use queue pattern for guaranteed processing

---

## Common Gotchas

### 1. ❌ Wrong: Accessing webhook data
```javascript
{{$json.email}}  // Empty or undefined
```

### ✅ Correct
```javascript
{{$json.body.email}}  // Data is under .body
```

### 2. ❌ Wrong: Response mode confusion
Using Webhook Response node with responseMode: "onReceived" (ignored)

### ✅ Correct
Set responseMode: "lastNode" to use Webhook Response node

### 3. ❌ Wrong: No validation
Assuming data is always present and valid

### ✅ Correct
Validate data early with IF node or Code node

### 4. ❌ Wrong: Hardcoded paths
Using same path for dev/prod

### ✅ Correct
Use environment variables: `{{$env.WEBHOOK_PATH_PREFIX}}/form-submit`

---

## Real Template Examples

From n8n template library (1,085 webhook templates):

**Simple Form to Slack**:
```
Webhook → Set → Slack
```

**Payment Processing**:
```
Webhook → Verify Signature → Update Database → Send Receipt → Notify Admin
```

**Chat Bot**:
```
Webhook → Parse Command → AI Agent → Format Response → Webhook Response
```

Use `search_templates({query: "webhook"})` to find more!

---

## Checklist for Webhook Workflows

### Setup
- [ ] Choose descriptive webhook path
- [ ] Configure HTTP method (POST most common)
- [ ] Choose response mode (onReceived vs lastNode)
- [ ] Test webhook URL before connecting services

### Security
- [ ] Add authentication (token, signature, IP whitelist)
- [ ] Validate incoming data
- [ ] Sanitize user input (if storing/displaying)
- [ ] Use HTTPS (always)

### Data Handling
- [ ] Remember data is under $json.body
- [ ] Handle missing fields gracefully
- [ ] Transform data to desired format
- [ ] Log important data (for debugging)

### Error Handling
- [ ] Add Error Trigger workflow
- [ ] Validate required fields
- [ ] Return appropriate error responses
- [ ] Alert team on failures

### Testing
- [ ] Test with curl/Postman
- [ ] Test error scenarios
- [ ] Verify response format
- [ ] Monitor first executions

---

## Summary

**Key Points**:
1. **Data under $json.body** (most common mistake!)
2. **Validate early** to catch bad data
3. **Choose response mode** based on use case
4. **Secure webhooks** with auth
5. **Handle errors** gracefully

**Pattern**: Webhook → Validate → Transform → Action → Response

**Related**:
- [n8n Expression Syntax](../../n8n-expression-syntax/SKILL.md) - Accessing webhook data correctly
- [http_api_integration.md](http_api_integration.md) - Making HTTP requests in response
