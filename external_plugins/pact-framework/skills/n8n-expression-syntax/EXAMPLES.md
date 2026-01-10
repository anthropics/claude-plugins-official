# n8n Expression Examples

Real working examples from n8n workflows.

---

## Example 1: Webhook Form Submission

**Scenario**: Form submission webhook posts to Slack

**Workflow**: Webhook → Slack

**Webhook Input** (POST):
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Corp",
  "message": "Interested in your product"
}
```

**Webhook Node Output**:
```json
{
  "headers": {"content-type": "application/json"},
  "params": {},
  "query": {},
  "body": {
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp",
    "message": "Interested in your product"
  }
}
```

**In Slack Node** (text field):
```
New form submission! 📝

Name: {{$json.body.name}}
Email: {{$json.body.email}}
Company: {{$json.body.company}}
Message: {{$json.body.message}}
```

**Output**:
```
New form submission! 📝

Name: John Doe
Email: john@example.com
Company: Acme Corp
Message: Interested in your product
```

---

## Example 2: HTTP API to Database

**Scenario**: Fetch user data from API and insert into database

**Workflow**: Schedule → HTTP Request → Postgres

**HTTP Request Returns**:
```json
{
  "data": {
    "users": [
      {
        "id": 123,
        "name": "Alice Smith",
        "email": "alice@example.com",
        "role": "admin"
      }
    ]
  }
}
```

**In Postgres Node** (INSERT statement):
```sql
INSERT INTO users (user_id, name, email, role, synced_at)
VALUES (
  {{$json.data.users[0].id}},
  '{{$json.data.users[0].name}}',
  '{{$json.data.users[0].email}}',
  '{{$json.data.users[0].role}}',
  '{{$now.toFormat('yyyy-MM-dd HH:mm:ss')}}'
)
```

**Result**: User inserted with current timestamp

---

## Example 3: Multi-Node Data Flow

**Scenario**: Webhook → HTTP Request → Email

**Workflow Structure**:
1. Webhook receives order ID
2. HTTP Request fetches order details
3. Email sends confirmation

### Node 1: Webhook

**Receives**:
```json
{
  "body": {
    "order_id": "ORD-12345"
  }
}
```

### Node 2: HTTP Request

**URL field**:
```
https://api.example.com/orders/{{$json.body.order_id}}
```

**Returns**:
```json
{
  "order": {
    "id": "ORD-12345",
    "customer": "Bob Jones",
    "total": 99.99,
    "items": ["Widget", "Gadget"]
  }
}
```

### Node 3: Email

**Subject**:
```
Order {{$node["Webhook"].json.body.order_id}} Confirmed
```

**Body**:
```
Dear {{$node["HTTP Request"].json.order.customer}},

Your order {{$node["Webhook"].json.body.order_id}} has been confirmed!

Total: ${{$node["HTTP Request"].json.order.total}}
Items: {{$node["HTTP Request"].json.order.items.join(', ')}}

Thank you for your purchase!
```

**Email Result**:
```
Subject: Order ORD-12345 Confirmed

Dear Bob Jones,

Your order ORD-12345 has been confirmed!

Total: $99.99
Items: Widget, Gadget

Thank you for your purchase!
```

---

## Example 4: Date Formatting

**Scenario**: Various date format outputs

**Current Time**: 2025-10-20 14:30:45

### ISO Format
```javascript
{{$now.toISO()}}
```
**Output**: `2025-10-20T14:30:45.000Z`

### Custom Date Format
```javascript
{{$now.toFormat('yyyy-MM-dd')}}
```
**Output**: `2025-10-20`

### Time Only
```javascript
{{$now.toFormat('HH:mm:ss')}}
```
**Output**: `14:30:45`

### Full Readable Format
```javascript
{{$now.toFormat('MMMM dd, yyyy')}}
```
**Output**: `October 20, 2025`

### Date Math - Future
```javascript
{{$now.plus({days: 7}).toFormat('yyyy-MM-dd')}}
```
**Output**: `2025-10-27`

### Date Math - Past
```javascript
{{$now.minus({hours: 24}).toFormat('yyyy-MM-dd HH:mm')}}
```
**Output**: `2025-10-19 14:30`

---

## Example 5: Array Operations

**Data**:
```json
{
  "users": [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"}
  ]
}
```

### First User
```javascript
{{$json.users[0].name}}
```
**Output**: `Alice`

### Last User
```javascript
{{$json.users[$json.users.length - 1].name}}
```
**Output**: `Charlie`

### All Emails (Join)
```javascript
{{$json.users.map(u => u.email).join(', ')}}
```
**Output**: `alice@example.com, bob@example.com, charlie@example.com`

### Array Length
```javascript
{{$json.users.length}}
```
**Output**: `3`

---

## Example 6: Conditional Logic

**Data**:
```json
{
  "order": {
    "status": "completed",
    "total": 150
  }
}
```

### Ternary Operator
```javascript
{{$json.order.status === 'completed' ? 'Order Complete ✓' : 'Pending...'}}
```
**Output**: `Order Complete ✓`

### Default Values
```javascript
{{$json.order.notes || 'No notes provided'}}
```
**Output**: `No notes provided` (if notes field doesn't exist)

### Multiple Conditions
```javascript
{{$json.order.total > 100 ? 'Premium Customer' : 'Standard Customer'}}
```
**Output**: `Premium Customer`

---

## Example 7: String Manipulation

**Data**:
```json
{
  "user": {
    "email": "JOHN@EXAMPLE.COM",
    "message": "  Hello World  "
  }
}
```

### Lowercase
```javascript
{{$json.user.email.toLowerCase()}}
```
**Output**: `john@example.com`

### Uppercase
```javascript
{{$json.user.message.toUpperCase()}}
```
**Output**: `  HELLO WORLD  `

### Trim
```javascript
{{$json.user.message.trim()}}
```
**Output**: `Hello World`

### Substring
```javascript
{{$json.user.email.substring(0, 4)}}
```
**Output**: `JOHN`

### Replace
```javascript
{{$json.user.message.replace('World', 'n8n')}}
```
**Output**: `  Hello n8n  `

---

## Example 8: Fields with Spaces

**Data**:
```json
{
  "user data": {
    "first name": "Jane",
    "last name": "Doe",
    "phone number": "+1234567890"
  }
}
```

### Bracket Notation
```javascript
{{$json['user data']['first name']}}
```
**Output**: `Jane`

### Combined
```javascript
{{$json['user data']['first name']}} {{$json['user data']['last name']}}
```
**Output**: `Jane Doe`

### Nested Spaces
```javascript
Contact: {{$json['user data']['phone number']}}
```
**Output**: `Contact: +1234567890`

---

## Example 9: Code Node (Direct Access)

**Code Node**: Transform webhook data

**Input** (from Webhook node):
```json
{
  "body": {
    "items": ["apple", "banana", "cherry"]
  }
}
```

**Code** (JavaScript):
```javascript
// ✅ Direct access (no {{ }})
const items = $json.body.items;

// Transform to uppercase
const uppercased = items.map(item => item.toUpperCase());

// Return in n8n format
return [{
  json: {
    original: items,
    transformed: uppercased,
    count: items.length
  }
}];
```

**Output**:
```json
{
  "original": ["apple", "banana", "cherry"],
  "transformed": ["APPLE", "BANANA", "CHERRY"],
  "count": 3
}
```

---

## Example 10: Environment Variables

**Setup**: Environment variable `API_KEY=secret123`

### In HTTP Request (Headers)
```javascript
Authorization: Bearer {{$env.API_KEY}}
```
**Result**: `Authorization: Bearer secret123`

### In URL
```javascript
https://api.example.com/data?key={{$env.API_KEY}}
```
**Result**: `https://api.example.com/data?key=secret123`

---

## Template from Real Workflow

**Based on n8n template #2947** (Weather to Slack)

### Workflow Structure
Webhook → OpenStreetMap API → Weather API → Slack

### Webhook Slash Command
**Input**: `/weather London`

**Webhook receives**:
```json
{
  "body": {
    "text": "London"
  }
}
```

### OpenStreetMap API
**URL**:
```
https://nominatim.openstreetmap.org/search?q={{$json.body.text}}&format=json
```

### Weather API (NWS)
**URL**:
```
https://api.weather.gov/points/{{$node["OpenStreetMap"].json[0].lat}},{{$node["OpenStreetMap"].json[0].lon}}
```

### Slack Message
```
Weather for {{$json.body.text}}:

Temperature: {{$node["Weather API"].json.properties.temperature.value}}°C
Conditions: {{$node["Weather API"].json.properties.shortForecast}}
```

---

## Summary

**Key Patterns**:
1. Webhook data is under `.body`
2. Use `{{}}` for expressions (except Code nodes)
3. Reference other nodes with `$node["Node Name"].json`
4. Use brackets for field names with spaces
5. Node names are case-sensitive

**Most Common Uses**:
- `{{$json.body.field}}` - Webhook data
- `{{$node["Name"].json.field}}` - Other node data
- `{{$now.toFormat('yyyy-MM-dd')}}` - Timestamps
- `{{$json.array[0].field}}` - Array access
- `{{$json.field || 'default'}}` - Default values

---

**Related**: See [COMMON_MISTAKES.md](COMMON_MISTAKES.md) for error examples and fixes.
