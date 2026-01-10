# Property Dependencies Guide

Deep dive into n8n property dependencies and displayOptions mechanism.

---

## What Are Property Dependencies?

**Definition**: Rules that control when fields are visible or required based on other field values.

**Mechanism**: `displayOptions` in node schema

**Purpose**:
- Show relevant fields only
- Hide irrelevant fields
- Simplify configuration UX
- Prevent invalid configurations

---

## displayOptions Structure

### Basic Format

```javascript
{
  "name": "fieldName",
  "type": "string",
  "displayOptions": {
    "show": {
      "otherField": ["value1", "value2"]
    }
  }
}
```

**Translation**: Show `fieldName` when `otherField` equals "value1" OR "value2"

### Show vs Hide

#### show (Most Common)

**Show field when condition matches**:
```javascript
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true]
    }
  }
}
```

**Meaning**: Show `body` when `sendBody = true`

#### hide (Less Common)

**Hide field when condition matches**:
```javascript
{
  "name": "advanced",
  "displayOptions": {
    "hide": {
      "simpleMode": [true]
    }
  }
}
```

**Meaning**: Hide `advanced` when `simpleMode = true`

### Multiple Conditions (AND Logic)

```javascript
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true],
      "method": ["POST", "PUT", "PATCH"]
    }
  }
}
```

**Meaning**: Show `body` when:
- `sendBody = true` AND
- `method IN (POST, PUT, PATCH)`

**All conditions must match** (AND logic)

### Multiple Values (OR Logic)

```javascript
{
  "name": "someField",
  "displayOptions": {
    "show": {
      "method": ["POST", "PUT", "PATCH"]
    }
  }
}
```

**Meaning**: Show `someField` when:
- `method = POST` OR
- `method = PUT` OR
- `method = PATCH`

**Any value matches** (OR logic)

---

## Common Dependency Patterns

### Pattern 1: Boolean Toggle

**Use case**: Optional feature flag

**Example**: HTTP Request sendBody
```javascript
// Field: sendBody (boolean)
{
  "name": "sendBody",
  "type": "boolean",
  "default": false
}

// Field: body (depends on sendBody)
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true]
    }
  }
}
```

**Flow**:
1. User sees sendBody checkbox
2. When checked → body field appears
3. When unchecked → body field hides

### Pattern 2: Resource/Operation Cascade

**Use case**: Different operations show different fields

**Example**: Slack message operations
```javascript
// Operation: post
{
  "name": "channel",
  "displayOptions": {
    "show": {
      "resource": ["message"],
      "operation": ["post"]
    }
  }
}

// Operation: update
{
  "name": "messageId",
  "displayOptions": {
    "show": {
      "resource": ["message"],
      "operation": ["update"]
    }
  }
}
```

**Flow**:
1. User selects resource="message"
2. User selects operation="post" → sees channel
3. User changes to operation="update" → channel hides, messageId shows

### Pattern 3: Type-Specific Configuration

**Use case**: Different types need different fields

**Example**: IF node conditions
```javascript
// String operations
{
  "name": "value2",
  "displayOptions": {
    "show": {
      "conditions.string.0.operation": ["equals", "notEquals", "contains"]
    }
  }
}

// Unary operations (isEmpty) don't show value2
{
  "displayOptions": {
    "hide": {
      "conditions.string.0.operation": ["isEmpty", "isNotEmpty"]
    }
  }
}
```

### Pattern 4: Method-Specific Fields

**Use case**: HTTP methods have different options

**Example**: HTTP Request
```javascript
// Query parameters (all methods can have)
{
  "name": "queryParameters",
  "displayOptions": {
    "show": {
      "sendQuery": [true]
    }
  }
}

// Body (only certain methods)
{
  "name": "body",
  "displayOptions": {
    "show": {
      "sendBody": [true],
      "method": ["POST", "PUT", "PATCH", "DELETE"]
    }
  }
}
```

---

## Finding Property Dependencies

### Using get_node with search_properties Mode

```javascript
// Find properties related to "body"
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "body"
});
```

### Using get_node with Full Detail

```javascript
// Get complete schema with displayOptions
get_node({
  nodeType: "nodes-base.httpRequest",
  detail: "full"
});
```

### When to Use

**✅ Use when**:
- Validation fails with "missing field" but you don't see that field
- A field appears/disappears unexpectedly
- You need to understand what controls field visibility
- Building dynamic configuration tools

**❌ Don't use when**:
- Simple configuration (use `get_node` with standard detail)
- Just starting configuration
- Field requirements are obvious

---

## Complex Dependency Examples

### Example 1: HTTP Request Complete Flow

**Scenario**: Configuring POST with JSON body

**Step 1**: Set method
```javascript
{
  "method": "POST"
  // → sendBody becomes visible
}
```

**Step 2**: Enable body
```javascript
{
  "method": "POST",
  "sendBody": true
  // → body field becomes visible AND required
}
```

**Step 3**: Configure body
```javascript
{
  "method": "POST",
  "sendBody": true,
  "body": {
    "contentType": "json"
    // → content field becomes visible AND required
  }
}
```

**Step 4**: Add content
```javascript
{
  "method": "POST",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {
      "name": "John",
      "email": "john@example.com"
    }
  }
}
// ✅ Valid!
```

**Dependency chain**:
```
method=POST
  → sendBody visible
    → sendBody=true
      → body visible + required
        → body.contentType=json
          → body.content visible + required
```

### Example 2: IF Node Operator Dependencies

**Scenario**: String comparison with different operators

**Binary operator** (equals):
```javascript
{
  "conditions": {
    "string": [
      {
        "operation": "equals"
        // → value1 required
        // → value2 required
        // → singleValue should NOT be set
      }
    ]
  }
}
```

**Unary operator** (isEmpty):
```javascript
{
  "conditions": {
    "string": [
      {
        "operation": "isEmpty"
        // → value1 required
        // → value2 should NOT be set
        // → singleValue should be true (auto-added)
      }
    ]
  }
}
```

**Dependency table**:

| Operator | value1 | value2 | singleValue |
|---|---|---|---|
| equals | Required | Required | false |
| notEquals | Required | Required | false |
| contains | Required | Required | false |
| isEmpty | Required | Hidden | true |
| isNotEmpty | Required | Hidden | true |

### Example 3: Slack Operation Matrix

**Scenario**: Different Slack operations show different fields

```javascript
// post message
{
  "resource": "message",
  "operation": "post"
  // Shows: channel (required), text (required), attachments, blocks
}

// update message
{
  "resource": "message",
  "operation": "update"
  // Shows: messageId (required), text (required), channel (optional)
}

// delete message
{
  "resource": "message",
  "operation": "delete"
  // Shows: messageId (required), channel (required)
  // Hides: text, attachments, blocks
}

// get message
{
  "resource": "message",
  "operation": "get"
  // Shows: messageId (required), channel (required)
  // Hides: text, attachments, blocks
}
```

**Field visibility matrix**:

| Field | post | update | delete | get |
|---|---|---|---|---|
| channel | Required | Optional | Required | Required |
| text | Required | Required | Hidden | Hidden |
| messageId | Hidden | Required | Required | Required |
| attachments | Optional | Optional | Hidden | Hidden |
| blocks | Optional | Optional | Hidden | Hidden |

---

## Nested Dependencies

### What Are They?

**Definition**: Dependencies within object properties

**Example**: HTTP Request body.contentType controls body.content structure

```javascript
{
  "body": {
    "contentType": "json",
    // → content expects JSON object
    "content": {
      "key": "value"
    }
  }
}

{
  "body": {
    "contentType": "form-data",
    // → content expects form fields array
    "content": [
      {
        "name": "field1",
        "value": "value1"
      }
    ]
  }
}
```

### How to Handle

**Strategy**: Configure parent first, then children

```javascript
// Step 1: Parent
{
  "body": {
    "contentType": "json"  // Set parent first
  }
}

// Step 2: Children (structure determined by parent)
{
  "body": {
    "contentType": "json",
    "content": {           // JSON object format
      "key": "value"
    }
  }
}
```

---

## Auto-Sanitization and Dependencies

### What Auto-Sanitization Fixes

**Operator structure issues** (IF/Switch nodes):

**Example**: singleValue property
```javascript
// You configure (missing singleValue)
{
  "type": "boolean",
  "operation": "isEmpty"
  // Missing singleValue
}

// Auto-sanitization adds it
{
  "type": "boolean",
  "operation": "isEmpty",
  "singleValue": true  // ✅ Added automatically
}
```

### What It Doesn't Fix

**Missing required fields**:
```javascript
// You configure (missing channel)
{
  "resource": "message",
  "operation": "post",
  "text": "Hello"
  // Missing required field: channel
}

// Auto-sanitization does NOT add
// You must add it yourself
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",  // ← You must add
  "text": "Hello"
}
```

---

## Troubleshooting Dependencies

### Problem 1: "Field X is required but not visible"

**Error**:
```json
{
  "type": "missing_required",
  "property": "body",
  "message": "body is required"
}
```

**But you don't see body field in configuration!**

**Solution**:
```javascript
// Check field dependencies using search_properties
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "body"
});

// Find that body shows when sendBody=true
// Add sendBody
{
  "method": "POST",
  "sendBody": true,  // ← Now body appears!
  "body": {...}
}
```

### Problem 2: "Field disappears when I change operation"

**Scenario**:
```javascript
// Working configuration
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "Hello"
}

// Change operation
{
  "resource": "message",
  "operation": "update",  // Changed
  "channel": "#general",  // Still here
  "text": "Updated"       // Still here
  // Missing: messageId (required for update!)
}
```

**Validation error**: "messageId is required"

**Why**: Different operation = different required fields

**Solution**:
```javascript
// Check requirements for new operation
get_node({
  nodeType: "nodes-base.slack"
});

// Configure for update operation
{
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890",  // Required for update
  "text": "Updated",
  "channel": "#general"       // Optional for update
}
```

### Problem 3: "Validation passes but field doesn't save"

**Scenario**: Field hidden by dependencies after validation

**Example**:
```javascript
// Configure
{
  "method": "GET",
  "sendBody": true,  // ❌ GET doesn't support body
  "body": {...}      // This will be stripped
}

// After save
{
  "method": "GET"
  // body removed because method=GET hides it
}
```

**Solution**: Respect dependencies from the start

```javascript
// Correct approach - check property dependencies
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "body"
});

// See that body only shows for POST/PUT/PATCH/DELETE
// Use correct method
{
  "method": "POST",
  "sendBody": true,
  "body": {...}
}
```

---

## Advanced Patterns

### Pattern 1: Conditional Required with Fallback

**Example**: Channel can be string OR expression

```javascript
// Option 1: String
{
  "channel": "#general"
}

// Option 2: Expression
{
  "channel": "={{$json.channelName}}"
}

// Validation accepts both
```

### Pattern 2: Mutually Exclusive Fields

**Example**: Use either ID or name, not both

```javascript
// Use messageId
{
  "messageId": "1234567890"
  // name not needed
}

// OR use messageName
{
  "messageName": "thread-name"
  // messageId not needed
}

// Dependencies ensure only one is required
```

### Pattern 3: Progressive Complexity

**Example**: Simple mode vs advanced mode

```javascript
// Simple mode
{
  "mode": "simple",
  "text": "{{$json.message}}"
  // Advanced fields hidden
}

// Advanced mode
{
  "mode": "advanced",
  "attachments": [...],
  "blocks": [...],
  "metadata": {...}
  // Simple field hidden, advanced fields shown
}
```

---

## Best Practices

### ✅ Do

1. **Check dependencies when stuck**
   ```javascript
   get_node({nodeType: "...", mode: "search_properties", propertyQuery: "..."});
   ```

2. **Configure parent properties first**
   ```javascript
   // First: method, resource, operation
   // Then: dependent fields
   ```

3. **Validate after changing operation**
   ```javascript
   // Operation changed → requirements changed
   validate_node({nodeType: "...", config: {...}, profile: "runtime"});
   ```

4. **Read validation errors for dependency hints**
   ```
   Error: "body required when sendBody=true"
   → Hint: Set sendBody=true to enable body
   ```

### ❌ Don't

1. **Don't ignore dependency errors**
   ```javascript
   // Error: "body not visible" → Check displayOptions
   ```

2. **Don't hardcode all possible fields**
   ```javascript
   // Bad: Adding fields that will be hidden
   ```

3. **Don't assume operations are identical**
   ```javascript
   // Each operation has unique requirements
   ```

---

## Summary

**Key Concepts**:
- `displayOptions` control field visibility
- `show` = field appears when conditions match
- `hide` = field disappears when conditions match
- Multiple conditions = AND logic
- Multiple values = OR logic

**Common Patterns**:
1. Boolean toggle (sendBody → body)
2. Resource/operation cascade (different operations → different fields)
3. Type-specific config (string vs boolean conditions)
4. Method-specific fields (GET vs POST)

**Troubleshooting**:
- Field required but not visible → Check dependencies
- Field disappears after change → Operation changed requirements
- Field doesn't save → Hidden by dependencies

**Tools**:
- `get_node({mode: "search_properties"})` - Find property dependencies
- `get_node({detail: "full"})` - See complete schema with displayOptions
- `get_node` - See operation requirements (standard detail)
- Validation errors - Hints about dependencies

**Related Files**:
- **[SKILL.md](SKILL.md)** - Main configuration guide
- **[OPERATION_PATTERNS.md](OPERATION_PATTERNS.md)** - Common patterns by node type
