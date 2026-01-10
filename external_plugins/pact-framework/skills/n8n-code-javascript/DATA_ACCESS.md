# Data Access Patterns - JavaScript Code Node

Comprehensive guide to accessing data in n8n Code nodes using JavaScript.

---

## Overview

In n8n Code nodes, you access data from previous nodes using built-in variables and methods. Understanding which method to use is critical for correct workflow execution.

**Data Access Priority** (by common usage):
1. **`$input.all()`** - Most common - Batch operations, aggregations
2. **`$input.first()`** - Very common - Single item operations
3. **`$input.item`** - Common - Each Item mode only
4. **`$node["NodeName"].json`** - Specific node references
5. **`$json`** - Direct current item (legacy, use `$input` instead)

---

## Pattern 1: $input.all() - Process All Items

**Usage**: Most common pattern for batch processing

**When to use:**
- Processing multiple records
- Aggregating data (sum, count, average)
- Filtering arrays
- Transforming datasets
- Comparing items
- Sorting or ranking

### Basic Usage

```javascript
// Get all items from previous node
const allItems = $input.all();

// allItems is an array of objects like:
// [
//   {json: {id: 1, name: "Alice"}},
//   {json: {id: 2, name: "Bob"}}
// ]

console.log(`Received ${allItems.length} items`);

return allItems;
```

### Example 1: Filter Active Items

```javascript
const allItems = $input.all();

// Filter only active items
const activeItems = allItems.filter(item => item.json.status === 'active');

return activeItems;
```

### Example 2: Transform All Items

```javascript
const allItems = $input.all();

// Map to new structure
const transformed = allItems.map(item => ({
  json: {
    id: item.json.id,
    fullName: `${item.json.firstName} ${item.json.lastName}`,
    email: item.json.email,
    processedAt: new Date().toISOString()
  }
}));

return transformed;
```

### Example 3: Aggregate Data

```javascript
const allItems = $input.all();

// Calculate total
const total = allItems.reduce((sum, item) => {
  return sum + (item.json.amount || 0);
}, 0);

return [{
  json: {
    total,
    count: allItems.length,
    average: total / allItems.length
  }
}];
```

### Example 4: Sort and Limit

```javascript
const allItems = $input.all();

// Get top 5 by score
const topFive = allItems
  .sort((a, b) => (b.json.score || 0) - (a.json.score || 0))
  .slice(0, 5);

return topFive.map(item => ({json: item.json}));
```

### Example 5: Group By Category

```javascript
const allItems = $input.all();

// Group items by category
const grouped = {};

for (const item of allItems) {
  const category = item.json.category || 'Uncategorized';

  if (!grouped[category]) {
    grouped[category] = [];
  }

  grouped[category].push(item.json);
}

// Convert to array format
return Object.entries(grouped).map(([category, items]) => ({
  json: {
    category,
    items,
    count: items.length
  }
}));
```

### Example 6: Deduplicate by ID

```javascript
const allItems = $input.all();

// Remove duplicates by ID
const seen = new Set();
const unique = [];

for (const item of allItems) {
  const id = item.json.id;

  if (!seen.has(id)) {
    seen.add(id);
    unique.push(item);
  }
}

return unique;
```

---

## Pattern 2: $input.first() - Get First Item

**Usage**: Very common for single-item operations

**When to use:**
- Previous node returns single object
- Working with API responses
- Getting initial/first data point
- Configuration or metadata access

### Basic Usage

```javascript
// Get first item from previous node
const firstItem = $input.first();

// Access the JSON data
const data = firstItem.json;

console.log('First item:', data);

return [{json: data}];
```

### Example 1: Process Single API Response

```javascript
// Get API response (typically single object)
const response = $input.first().json;

// Extract what you need
return [{
  json: {
    userId: response.data.user.id,
    userName: response.data.user.name,
    status: response.status,
    fetchedAt: new Date().toISOString()
  }
}];
```

### Example 2: Transform Single Object

```javascript
const data = $input.first().json;

// Transform structure
return [{
  json: {
    id: data.id,
    contact: {
      email: data.email,
      phone: data.phone
    },
    address: {
      street: data.street,
      city: data.city,
      zip: data.zip
    }
  }
}];
```

### Example 3: Validate Single Item

```javascript
const item = $input.first().json;

// Validation logic
const isValid = item.email && item.email.includes('@');

return [{
  json: {
    ...item,
    valid: isValid,
    validatedAt: new Date().toISOString()
  }
}];
```

### Example 4: Extract Nested Data

```javascript
const response = $input.first().json;

// Navigate nested structure
const users = response.data?.users || [];

return users.map(user => ({
  json: {
    id: user.id,
    name: user.profile?.name || 'Unknown',
    email: user.contact?.email || 'no-email'
  }
}));
```

### Example 5: Combine with Other Methods

```javascript
// Get first item's data
const firstData = $input.first().json;

// Use it to filter all items
const allItems = $input.all();
const matching = allItems.filter(item =>
  item.json.category === firstData.targetCategory
);

return matching;
```

---

## Pattern 3: $input.item - Current Item (Each Item Mode)

**Usage**: Common in "Run Once for Each Item" mode

**When to use:**
- Mode is set to "Run Once for Each Item"
- Need to process items independently
- Per-item API calls or validations
- Item-specific error handling

**IMPORTANT**: Only use in "Each Item" mode. Will be undefined in "All Items" mode.

### Basic Usage

```javascript
// In "Run Once for Each Item" mode
const currentItem = $input.item;
const data = currentItem.json;

console.log('Processing item:', data.id);

return [{
  json: {
    ...data,
    processed: true
  }
}];
```

### Example 1: Add Processing Metadata

```javascript
const item = $input.item;

return [{
  json: {
    ...item.json,
    processed: true,
    processedAt: new Date().toISOString(),
    processingDuration: Math.random() * 1000  // Simulated duration
  }
}];
```

### Example 2: Per-Item Validation

```javascript
const item = $input.item;
const data = item.json;

// Validate this specific item
const errors = [];

if (!data.email) errors.push('Email required');
if (!data.name) errors.push('Name required');
if (data.age && data.age < 18) errors.push('Must be 18+');

return [{
  json: {
    ...data,
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined
  }
}];
```

### Example 3: Item-Specific API Call

```javascript
const item = $input.item;
const userId = item.json.userId;

// Make API call specific to this item
const response = await $helpers.httpRequest({
  method: 'GET',
  url: `https://api.example.com/users/${userId}/details`
});

return [{
  json: {
    ...item.json,
    details: response
  }
}];
```

### Example 4: Conditional Processing

```javascript
const item = $input.item;
const data = item.json;

// Process based on item type
if (data.type === 'premium') {
  return [{
    json: {
      ...data,
      discount: 0.20,
      tier: 'premium'
    }
  }];
} else {
  return [{
    json: {
      ...data,
      discount: 0.05,
      tier: 'standard'
    }
  }];
}
```

---

## Pattern 4: $node - Reference Other Nodes

**Usage**: Less common, but powerful for specific scenarios

**When to use:**
- Need data from specific named node
- Combining data from multiple nodes
- Accessing metadata about workflow execution

### Basic Usage

```javascript
// Get output from specific node
const webhookData = $node["Webhook"].json;
const apiData = $node["HTTP Request"].json;

return [{
  json: {
    fromWebhook: webhookData,
    fromAPI: apiData
  }
}];
```

### Example 1: Combine Multiple Sources

```javascript
// Reference multiple nodes
const webhook = $node["Webhook"].json;
const database = $node["Postgres"].json;
const api = $node["HTTP Request"].json;

return [{
  json: {
    combined: {
      webhook: webhook.body,
      dbRecords: database.length,
      apiResponse: api.status
    },
    processedAt: new Date().toISOString()
  }
}];
```

### Example 2: Compare Across Nodes

```javascript
const oldData = $node["Get Old Data"].json;
const newData = $node["Get New Data"].json;

// Compare
const changes = {
  added: newData.filter(n => !oldData.find(o => o.id === n.id)),
  removed: oldData.filter(o => !newData.find(n => n.id === o.id)),
  modified: newData.filter(n => {
    const old = oldData.find(o => o.id === n.id);
    return old && JSON.stringify(old) !== JSON.stringify(n);
  })
};

return [{
  json: {
    changes,
    summary: {
      added: changes.added.length,
      removed: changes.removed.length,
      modified: changes.modified.length
    }
  }
}];
```

### Example 3: Access Node Metadata

```javascript
// Get data from specific execution path
const ifTrueBranch = $node["IF True"].json;
const ifFalseBranch = $node["IF False"].json;

// Use whichever branch executed
const result = ifTrueBranch || ifFalseBranch || {};

return [{json: result}];
```

---

## Critical: Webhook Data Structure

**MOST COMMON MISTAKE**: Forgetting webhook data is nested under `.body`

### The Problem

Webhook node wraps all incoming data under a `body` property. This catches many developers by surprise.

### Structure

```javascript
// Webhook node output structure:
{
  "headers": {
    "content-type": "application/json",
    "user-agent": "...",
    // ... other headers
  },
  "params": {},
  "query": {},
  "body": {
    // ← YOUR DATA IS HERE
    "name": "Alice",
    "email": "alice@example.com",
    "message": "Hello!"
  }
}
```

### Wrong vs Right

```javascript
// ❌ WRONG: Trying to access directly
const name = $json.name;  // undefined
const email = $json.email;  // undefined

// ✅ CORRECT: Access via .body
const name = $json.body.name;  // "Alice"
const email = $json.body.email;  // "alice@example.com"

// ✅ CORRECT: Extract body first
const webhookData = $json.body;
const name = webhookData.name;  // "Alice"
const email = webhookData.email;  // "alice@example.com"
```

### Example: Full Webhook Processing

```javascript
// Get webhook data from previous node
const webhookOutput = $input.first().json;

// Access the actual payload
const payload = webhookOutput.body;

// Access headers if needed
const contentType = webhookOutput.headers['content-type'];

// Access query parameters if needed
const apiKey = webhookOutput.query.api_key;

// Process the actual data
return [{
  json: {
    // Data from webhook body
    userName: payload.name,
    userEmail: payload.email,
    message: payload.message,

    // Metadata
    receivedAt: new Date().toISOString(),
    contentType: contentType,
    authenticated: !!apiKey
  }
}];
```

### POST Data, Query Params, and Headers

```javascript
const webhook = $input.first().json;

return [{
  json: {
    // POST body data
    formData: webhook.body,

    // Query parameters (?key=value)
    queryParams: webhook.query,

    // HTTP headers
    userAgent: webhook.headers['user-agent'],
    contentType: webhook.headers['content-type'],

    // Request metadata
    method: webhook.method,  // POST, GET, etc.
    url: webhook.url
  }
}];
```

### Common Webhook Scenarios

```javascript
// Scenario 1: Form submission
const formData = $json.body;
const name = formData.name;
const email = formData.email;

// Scenario 2: JSON API webhook
const apiPayload = $json.body;
const eventType = apiPayload.event;
const data = apiPayload.data;

// Scenario 3: Query parameters
const apiKey = $json.query.api_key;
const userId = $json.query.user_id;

// Scenario 4: Headers
const authorization = $json.headers['authorization'];
const signature = $json.headers['x-signature'];
```

---

## Choosing the Right Pattern

### Decision Tree

```
Do you need ALL items from previous node?
├─ YES → Use $input.all()
│
└─ NO → Do you need just the FIRST item?
    ├─ YES → Use $input.first()
    │
    └─ NO → Are you in "Each Item" mode?
        ├─ YES → Use $input.item
        │
        └─ NO → Do you need specific node data?
            ├─ YES → Use $node["NodeName"]
            └─ NO → Use $input.first() (default)
```

### Quick Reference Table

| Scenario | Use This | Example |
|----------|----------|---------|
| Sum all amounts | `$input.all()` | `allItems.reduce((sum, i) => sum + i.json.amount, 0)` |
| Get API response | `$input.first()` | `$input.first().json.data` |
| Process each independently | `$input.item` | `$input.item.json` (Each Item mode) |
| Combine two nodes | `$node["Name"]` | `$node["API"].json` |
| Filter array | `$input.all()` | `allItems.filter(i => i.json.active)` |
| Transform single object | `$input.first()` | `{...input.first().json, new: true}` |
| Webhook data | `$input.first()` | `$input.first().json.body` |

---

## Common Mistakes

### Mistake 1: Using $json Without Context

```javascript
// ❌ WRONG: $json is ambiguous
const value = $json.field;

// ✅ CORRECT: Be explicit
const value = $input.first().json.field;
```

### Mistake 2: Forgetting .json Property

```javascript
// ❌ WRONG: Trying to access fields on item object
const items = $input.all();
const names = items.map(item => item.name);  // undefined

// ✅ CORRECT: Access via .json
const names = items.map(item => item.json.name);
```

### Mistake 3: Using $input.item in All Items Mode

```javascript
// ❌ WRONG: $input.item is undefined in "All Items" mode
const data = $input.item.json;  // Error!

// ✅ CORRECT: Use appropriate method
const data = $input.first().json;  // Or $input.all()
```

### Mistake 4: Not Handling Empty Arrays

```javascript
// ❌ WRONG: Crashes if no items
const first = $input.all()[0].json;

// ✅ CORRECT: Check length first
const items = $input.all();
if (items.length === 0) {
  return [];
}
const first = items[0].json;

// ✅ ALSO CORRECT: Use $input.first()
const first = $input.first().json;  // Built-in safety
```

### Mistake 5: Modifying Original Data

```javascript
// ❌ RISKY: Mutating original
const items = $input.all();
items[0].json.modified = true;  // Modifies original
return items;

// ✅ SAFE: Create new objects
const items = $input.all();
return items.map(item => ({
  json: {
    ...item.json,
    modified: true
  }
}));
```

---

## Advanced Patterns

### Pattern: Pagination Handling

```javascript
const currentPage = $input.all();
const pageNumber = $node["Set Page"].json.page || 1;

// Combine with previous pages
const allPreviousPages = $node["Accumulator"]?.json.accumulated || [];

return [{
  json: {
    accumulated: [...allPreviousPages, ...currentPage],
    currentPage: pageNumber,
    totalItems: allPreviousPages.length + currentPage.length
  }
}];
```

### Pattern: Conditional Node Reference

```javascript
// Access different nodes based on condition
const condition = $input.first().json.type;

let data;
if (condition === 'api') {
  data = $node["API Response"].json;
} else if (condition === 'database') {
  data = $node["Database"].json;
} else {
  data = $node["Default"].json;
}

return [{json: data}];
```

### Pattern: Multi-Node Aggregation

```javascript
// Collect data from multiple named nodes
const sources = ['Source1', 'Source2', 'Source3'];
const allData = [];

for (const source of sources) {
  const nodeData = $node[source]?.json;
  if (nodeData) {
    allData.push({
      source,
      data: nodeData
    });
  }
}

return allData.map(item => ({json: item}));
```

---

## Summary

**Most Common Patterns**:
1. `$input.all()` - Process multiple items, batch operations
2. `$input.first()` - Single item, API responses
3. `$input.item` - Each Item mode processing

**Critical Rule**:
- Webhook data is under `.body` property

**Best Practice**:
- Be explicit: Use `$input.first().json.field` instead of `$json.field`
- Always check for null/undefined
- Use appropriate method for your mode (All Items vs Each Item)

**See Also**:
- [SKILL.md](SKILL.md) - Overview and quick start
- [COMMON_PATTERNS.md](COMMON_PATTERNS.md) - Production patterns
- [ERROR_PATTERNS.md](ERROR_PATTERNS.md) - Avoid common mistakes
