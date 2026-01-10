# Error Catalog

Comprehensive catalog of n8n validation errors with real examples and fixes.

---

## Error Types Overview

Common validation errors by priority:

| Error Type | Priority | Severity | Auto-Fix |
|---|---|---|---|
| missing_required | Highest | Error | ❌ |
| invalid_value | High | Error | ❌ |
| type_mismatch | Medium | Error | ❌ |
| invalid_expression | Medium | Error | ❌ |
| invalid_reference | Low | Error | ❌ |
| operator_structure | Lowest | Warning | ✅ |

---

## Errors (Must Fix)

### 1. missing_required

**What it means**: Required field is not provided in node configuration

**When it occurs**:
- Creating new nodes without all required fields
- Copying configurations between different operations
- Switching operations that have different requirements

**Most common validation error**

#### Example 1: Slack Channel Missing

**Error**:
```json
{
  "type": "missing_required",
  "property": "channel",
  "message": "Channel name is required",
  "node": "Slack",
  "path": "parameters.channel"
}
```

**Broken Configuration**:
```javascript
{
  "resource": "message",
  "operation": "post"
  // Missing: channel
}
```

**Fix**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general"  // ✅ Added required field
}
```

**How to identify required fields**:
```javascript
// Use get_node to see what's required
const info = get_node({
  nodeType: "nodes-base.slack"
});
// Check properties marked as "required": true
```

#### Example 2: HTTP Request Missing URL

**Error**:
```json
{
  "type": "missing_required",
  "property": "url",
  "message": "URL is required for HTTP Request",
  "node": "HTTP Request",
  "path": "parameters.url"
}
```

**Broken Configuration**:
```javascript
{
  "method": "GET",
  "authentication": "none"
  // Missing: url
}
```

**Fix**:
```javascript
{
  "method": "GET",
  "authentication": "none",
  "url": "https://api.example.com/data"  // ✅ Added
}
```

#### Example 3: Database Query Missing Connection

**Error**:
```json
{
  "type": "missing_required",
  "property": "query",
  "message": "SQL query is required",
  "node": "Postgres",
  "path": "parameters.query"
}
```

**Broken Configuration**:
```javascript
{
  "operation": "executeQuery"
  // Missing: query
}
```

**Fix**:
```javascript
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users WHERE active = true"  // ✅ Added
}
```

#### Example 4: Conditional Fields

**Error**:
```json
{
  "type": "missing_required",
  "property": "body",
  "message": "Request body is required when sendBody is true",
  "node": "HTTP Request",
  "path": "parameters.body"
}
```

**Broken Configuration**:
```javascript
{
  "method": "POST",
  "url": "https://api.example.com/create",
  "sendBody": true
  // Missing: body (required when sendBody=true)
}
```

**Fix**:
```javascript
{
  "method": "POST",
  "url": "https://api.example.com/create",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {
      "name": "John",
      "email": "john@example.com"
    }
  }  // ✅ Added conditional required field
}
```

---

### 2. invalid_value

**What it means**: Provided value doesn't match allowed options or format

**When it occurs**:
- Using wrong enum value
- Typos in operation names
- Invalid format for specialized fields (emails, URLs, channels)

**Second most common error**

#### Example 1: Invalid Operation

**Error**:
```json
{
  "type": "invalid_value",
  "property": "operation",
  "message": "Operation must be one of: post, update, delete, get",
  "current": "send",
  "allowed": ["post", "update", "delete", "get"]
}
```

**Broken Configuration**:
```javascript
{
  "resource": "message",
  "operation": "send"  // ❌ Invalid - should be "post"
}
```

**Fix**:
```javascript
{
  "resource": "message",
  "operation": "post"  // ✅ Use valid operation
}
```

#### Example 2: Invalid HTTP Method

**Error**:
```json
{
  "type": "invalid_value",
  "property": "method",
  "message": "Method must be one of: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
  "current": "FETCH",
  "allowed": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
}
```

**Broken Configuration**:
```javascript
{
  "method": "FETCH",  // ❌ Invalid
  "url": "https://api.example.com"
}
```

**Fix**:
```javascript
{
  "method": "GET",  // ✅ Use valid HTTP method
  "url": "https://api.example.com"
}
```

#### Example 3: Invalid Channel Format

**Error**:
```json
{
  "type": "invalid_value",
  "property": "channel",
  "message": "Channel name must start with # and be lowercase (e.g., #general)",
  "current": "General"
}
```

**Broken Configuration**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "General"  // ❌ Wrong format
}
```

**Fix**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general"  // ✅ Correct format
}
```

#### Example 4: Invalid Enum with Case Sensitivity

**Error**:
```json
{
  "type": "invalid_value",
  "property": "resource",
  "message": "Resource must be one of: channel, message, user, file",
  "current": "Message",
  "allowed": ["channel", "message", "user", "file"]
}
```

**Note**: Enums are case-sensitive!

**Broken Configuration**:
```javascript
{
  "resource": "Message",  // ❌ Capital M
  "operation": "post"
}
```

**Fix**:
```javascript
{
  "resource": "message",  // ✅ Lowercase
  "operation": "post"
}
```

---

### 3. type_mismatch

**What it means**: Value is wrong data type (string instead of number, etc.)

**When it occurs**:
- Hardcoding values that should be numbers
- Using expressions where literals are expected
- JSON serialization issues

**Common error**

#### Example 1: String Instead of Number

**Error**:
```json
{
  "type": "type_mismatch",
  "property": "limit",
  "message": "Expected number, got string",
  "expected": "number",
  "current": "100"
}
```

**Broken Configuration**:
```javascript
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users",
  "limit": "100"  // ❌ String
}
```

**Fix**:
```javascript
{
  "operation": "executeQuery",
  "query": "SELECT * FROM users",
  "limit": 100  // ✅ Number
}
```

#### Example 2: Number Instead of String

**Error**:
```json
{
  "type": "type_mismatch",
  "property": "channel",
  "message": "Expected string, got number",
  "expected": "string",
  "current": 12345
}
```

**Broken Configuration**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": 12345  // ❌ Number (even if channel ID)
}
```

**Fix**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general"  // ✅ String (channel name, not ID)
}
```

#### Example 3: Boolean as String

**Error**:
```json
{
  "type": "type_mismatch",
  "property": "sendHeaders",
  "message": "Expected boolean, got string",
  "expected": "boolean",
  "current": "true"
}
```

**Broken Configuration**:
```javascript
{
  "method": "GET",
  "url": "https://api.example.com",
  "sendHeaders": "true"  // ❌ String "true"
}
```

**Fix**:
```javascript
{
  "method": "GET",
  "url": "https://api.example.com",
  "sendHeaders": true  // ✅ Boolean true
}
```

#### Example 4: Object Instead of Array

**Error**:
```json
{
  "type": "type_mismatch",
  "property": "tags",
  "message": "Expected array, got object",
  "expected": "array",
  "current": {"tag": "important"}
}
```

**Broken Configuration**:
```javascript
{
  "name": "New Channel",
  "tags": {"tag": "important"}  // ❌ Object
}
```

**Fix**:
```javascript
{
  "name": "New Channel",
  "tags": ["important", "alerts"]  // ✅ Array
}
```

---

### 4. invalid_expression

**What it means**: n8n expression has syntax errors or invalid references

**When it occurs**:
- Missing `{{}}` around expressions
- Typos in variable names
- Referencing non-existent nodes or fields
- Invalid JavaScript syntax in expressions

**Moderately common**

**Related**: See **n8n Expression Syntax** skill for comprehensive expression guidance

#### Example 1: Missing Curly Braces

**Error**:
```json
{
  "type": "invalid_expression",
  "property": "text",
  "message": "Expressions must be wrapped in {{}}",
  "current": "$json.name"
}
```

**Broken Configuration**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "$json.name"  // ❌ Missing {{}}
}
```

**Fix**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "={{$json.name}}"  // ✅ Wrapped in {{}}
}
```

#### Example 2: Invalid Node Reference

**Error**:
```json
{
  "type": "invalid_expression",
  "property": "value",
  "message": "Referenced node 'HTTP Requets' does not exist",
  "current": "={{$node['HTTP Requets'].json.data}}"
}
```

**Broken Configuration**:
```javascript
{
  "field": "data",
  "value": "={{$node['HTTP Requets'].json.data}}"  // ❌ Typo in node name
}
```

**Fix**:
```javascript
{
  "field": "data",
  "value": "={{$node['HTTP Request'].json.data}}"  // ✅ Correct node name
}
```

#### Example 3: Invalid Property Access

**Error**:
```json
{
  "type": "invalid_expression",
  "property": "text",
  "message": "Cannot access property 'user' of undefined",
  "current": "={{$json.data.user.name}}"
}
```

**Broken Configuration**:
```javascript
{
  "text": "={{$json.data.user.name}}"  // ❌ Structure doesn't exist
}
```

**Fix** (with safe navigation):
```javascript
{
  "text": "={{$json.data?.user?.name || 'Unknown'}}"  // ✅ Safe navigation + fallback
}
```

#### Example 4: Webhook Data Access Error

**Error**:
```json
{
  "type": "invalid_expression",
  "property": "value",
  "message": "Property 'email' not found in $json",
  "current": "={{$json.email}}"
}
```

**Common Gotcha**: Webhook data is under `.body`!

**Broken Configuration**:
```javascript
{
  "field": "email",
  "value": "={{$json.email}}"  // ❌ Missing .body
}
```

**Fix**:
```javascript
{
  "field": "email",
  "value": "={{$json.body.email}}"  // ✅ Webhook data under .body
}
```

---

### 5. invalid_reference

**What it means**: Configuration references a node that doesn't exist in the workflow

**When it occurs**:
- Node was renamed or deleted
- Typo in node name
- Copy-pasting from another workflow

**Less common error**

#### Example 1: Deleted Node Reference

**Error**:
```json
{
  "type": "invalid_reference",
  "property": "expression",
  "message": "Node 'Transform Data' does not exist in workflow",
  "referenced_node": "Transform Data"
}
```

**Broken Configuration**:
```javascript
{
  "value": "={{$node['Transform Data'].json.result}}"  // ❌ Node deleted
}
```

**Fix**:
```javascript
// Option 1: Update to existing node
{
  "value": "={{$node['Set'].json.result}}"
}

// Option 2: Remove expression if not needed
{
  "value": "default_value"
}
```

#### Example 2: Connection to Non-Existent Node

**Error**:
```json
{
  "type": "invalid_reference",
  "message": "Connection references node 'Slack1' which does not exist",
  "source": "HTTP Request",
  "target": "Slack1"
}
```

**Fix**: Use `cleanStaleConnections` operation:
```javascript
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{
    type: "cleanStaleConnections"
  }]
})
```

#### Example 3: Renamed Node Not Updated

**Error**:
```json
{
  "type": "invalid_reference",
  "property": "expression",
  "message": "Node 'Get Weather' does not exist (did you mean 'Weather API'?)",
  "referenced_node": "Get Weather",
  "suggestions": ["Weather API"]
}
```

**Broken Configuration**:
```javascript
{
  "value": "={{$node['Get Weather'].json.temperature}}"  // ❌ Old name
}
```

**Fix**:
```javascript
{
  "value": "={{$node['Weather API'].json.temperature}}"  // ✅ Current name
}
```

---

## Warnings (Should Fix)

### 6. best_practice

**What it means**: Configuration works but doesn't follow best practices

**Severity**: Warning (doesn't block execution)

**When acceptable**: Development, testing, simple workflows

**When to fix**: Production workflows, critical operations

#### Example 1: Missing Error Handling

**Warning**:
```json
{
  "type": "best_practice",
  "property": "onError",
  "message": "Slack API can have rate limits and connection issues",
  "suggestion": "Add error handling: onError: 'continueRegularOutput'"
}
```

**Current Configuration**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#alerts"
  // No error handling ⚠️
}
```

**Recommended Fix**:
```javascript
{
  "resource": "message",
  "operation": "post",
  "channel": "#alerts",
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 3
}
```

#### Example 2: No Retry Logic

**Warning**:
```json
{
  "type": "best_practice",
  "property": "retryOnFail",
  "message": "External API calls should retry on failure",
  "suggestion": "Add retryOnFail: true, maxTries: 3, waitBetweenTries: 1000"
}
```

**When to ignore**: Idempotent operations, APIs with their own retry logic

**When to fix**: Flaky external services, production automation

---

### 7. deprecated

**What it means**: Using old API version or deprecated feature

**Severity**: Warning (still works but may stop working in future)

**When to fix**: Always (eventually)

#### Example 1: Old typeVersion

**Warning**:
```json
{
  "type": "deprecated",
  "property": "typeVersion",
  "message": "typeVersion 1 is deprecated for Slack node, use version 2",
  "current": 1,
  "recommended": 2
}
```

**Fix**:
```javascript
{
  "type": "n8n-nodes-base.slack",
  "typeVersion": 2,  // ✅ Updated
  // May need to update configuration for new version
}
```

---

### 8. performance

**What it means**: Configuration may cause performance issues

**Severity**: Warning

**When to fix**: High-volume workflows, large datasets

#### Example 1: Unbounded Query

**Warning**:
```json
{
  "type": "performance",
  "property": "query",
  "message": "SELECT without LIMIT can return massive datasets",
  "suggestion": "Add LIMIT clause or use pagination"
}
```

**Current**:
```sql
SELECT * FROM users WHERE active = true
```

**Fix**:
```sql
SELECT * FROM users WHERE active = true LIMIT 1000
```

---

## Auto-Sanitization Fixes

### 9. operator_structure

**What it means**: IF/Switch operator structure issues

**Severity**: Warning

**Auto-Fix**: ✅ YES - Fixed automatically on workflow save

**Rare** (mostly auto-fixed)

#### Fixed Automatically: Binary Operators

**Before** (you create this):
```javascript
{
  "type": "boolean",
  "operation": "equals",
  "singleValue": true  // ❌ Wrong for binary operator
}
```

**After** (auto-sanitization fixes it):
```javascript
{
  "type": "boolean",
  "operation": "equals"
  // singleValue removed ✅
}
```

**You don't need to do anything** - this is fixed on save!

#### Fixed Automatically: Unary Operators

**Before**:
```javascript
{
  "type": "boolean",
  "operation": "isEmpty"
  // Missing singleValue ❌
}
```

**After**:
```javascript
{
  "type": "boolean",
  "operation": "isEmpty",
  "singleValue": true  // ✅ Added automatically
}
```

**What you should do**: Trust auto-sanitization, don't manually fix these!

---

## Recovery Patterns

### Pattern 1: Progressive Validation

**Problem**: Too many errors at once

**Solution**:
```javascript
// Step 1: Minimal valid config
let config = {
  resource: "message",
  operation: "post",
  channel: "#general",
  text: "Hello"
};

validate_node({nodeType: "nodes-base.slack", config, profile: "runtime"});
// ✅ Valid

// Step 2: Add features one by one
config.attachments = [...];
validate_node({nodeType: "nodes-base.slack", config, profile: "runtime"});

config.blocks = [...];
validate_node({nodeType: "nodes-base.slack", config, profile: "runtime"});
```

### Pattern 2: Error Triage

**Problem**: Multiple errors

**Solution**:
```javascript
const result = validate_node_operation({...});

// 1. Fix errors (must fix)
result.errors.forEach(error => {
  console.log(`MUST FIX: ${error.property} - ${error.message}`);
});

// 2. Review warnings (should fix)
result.warnings.forEach(warning => {
  console.log(`SHOULD FIX: ${warning.property} - ${warning.message}`);
});

// 3. Consider suggestions (optional)
result.suggestions.forEach(sug => {
  console.log(`OPTIONAL: ${sug.message}`);
});
```

### Pattern 3: Use get_node

**Problem**: Don't know what's required

**Solution**:
```javascript
// Before configuring, check requirements
const info = get_node({
  nodeType: "nodes-base.slack"
});

// Look for required fields
info.properties.forEach(prop => {
  if (prop.required) {
    console.log(`Required: ${prop.name} (${prop.type})`);
  }
});
```

---

## Summary

**Most Common Errors**:
1. `missing_required` (45%) - Always check get_node
2. `invalid_value` (28%) - Check allowed values
3. `type_mismatch` (12%) - Use correct data types
4. `invalid_expression` (8%) - Use Expression Syntax skill
5. `invalid_reference` (5%) - Clean stale connections

**Auto-Fixed**:
- `operator_structure` - Trust auto-sanitization!

**Related Skills**:
- **[SKILL.md](SKILL.md)** - Main validation guide
- **[FALSE_POSITIVES.md](FALSE_POSITIVES.md)** - When to ignore warnings
- **n8n Expression Syntax** - Fix expression errors
- **n8n MCP Tools Expert** - Use validation tools correctly
