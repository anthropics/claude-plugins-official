# Built-in Functions - JavaScript Code Node

Complete reference for n8n's built-in JavaScript functions and helpers.

---

## Overview

n8n Code nodes provide powerful built-in functions beyond standard JavaScript. This guide covers:

1. **$helpers.httpRequest()** - Make HTTP requests
2. **DateTime (Luxon)** - Advanced date/time operations
3. **$jmespath()** - Query JSON structures
4. **$getWorkflowStaticData()** - Persistent storage
5. **Standard JavaScript Globals** - Math, JSON, console, etc.
6. **Available Node.js Modules** - crypto, Buffer, URL

---

## 1. $helpers.httpRequest() - HTTP Requests

Make HTTP requests directly from Code nodes without using HTTP Request node.

### Basic Usage

```javascript
const response = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/users'
});

return [{json: {data: response}}];
```

### Complete Options

```javascript
const response = await $helpers.httpRequest({
  method: 'POST',  // GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
  url: 'https://api.example.com/users',
  headers: {
    'Authorization': 'Bearer token123',
    'Content-Type': 'application/json',
    'User-Agent': 'n8n-workflow'
  },
  body: {
    name: 'John Doe',
    email: 'john@example.com'
  },
  qs: {  // Query string parameters
    page: 1,
    limit: 10
  },
  timeout: 10000,  // Milliseconds (default: no timeout)
  json: true,  // Auto-parse JSON response (default: true)
  simple: false,  // Don't throw on HTTP errors (default: true)
  resolveWithFullResponse: false  // Return only body (default: false)
});
```

### GET Request

```javascript
// Simple GET
const users = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/users'
});

return [{json: {users}}];
```

```javascript
// GET with query parameters
const results = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/search',
  qs: {
    q: 'javascript',
    page: 1,
    per_page: 50
  }
});

return [{json: results}];
```

### POST Request

```javascript
// POST with JSON body
const newUser = await $helpers.httpRequest({
  method: 'POST',
  url: 'https://api.example.com/users',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + $env.API_KEY
  },
  body: {
    name: $json.body.name,
    email: $json.body.email,
    role: 'user'
  }
});

return [{json: newUser}];
```

### PUT/PATCH Request

```javascript
// Update resource
const updated = await $helpers.httpRequest({
  method: 'PATCH',
  url: `https://api.example.com/users/${userId}`,
  body: {
    name: 'Updated Name',
    status: 'active'
  }
});

return [{json: updated}];
```

### DELETE Request

```javascript
// Delete resource
await $helpers.httpRequest({
  method: 'DELETE',
  url: `https://api.example.com/users/${userId}`,
  headers: {
    'Authorization': 'Bearer ' + $env.API_KEY
  }
});

return [{json: {deleted: true, userId}}];
```

### Authentication Patterns

```javascript
// Bearer Token
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: {
    'Authorization': `Bearer ${$env.API_TOKEN}`
  }
});
```

```javascript
// API Key in Header
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: {
    'X-API-Key': $env.API_KEY
  }
});
```

```javascript
// Basic Auth (manual)
const credentials = Buffer.from(`${username}:${password}`).toString('base64');

const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  headers: {
    'Authorization': `Basic ${credentials}`
  }
});
```

### Error Handling

```javascript
// Handle HTTP errors gracefully
try {
  const response = await $helpers.httpRequest({
    method: 'GET',
    url: 'https://api.example.com/users',
    simple: false  // Don't throw on 4xx/5xx
  });

  if (response.statusCode >= 200 && response.statusCode < 300) {
    return [{json: {success: true, data: response.body}}];
  } else {
    return [{
      json: {
        success: false,
        status: response.statusCode,
        error: response.body
      }
    }];
  }
} catch (error) {
  return [{
    json: {
      success: false,
      error: error.message
    }
  }];
}
```

### Full Response Access

```javascript
// Get full response including headers and status
const response = await $helpers.httpRequest({
  url: 'https://api.example.com/data',
  resolveWithFullResponse: true
});

return [{
  json: {
    statusCode: response.statusCode,
    headers: response.headers,
    body: response.body,
    rateLimit: response.headers['x-ratelimit-remaining']
  }
}];
```

---

## 2. DateTime (Luxon) - Date & Time Operations

n8n includes Luxon for powerful date/time handling. Access via `DateTime` global.

### Current Date/Time

```javascript
// Current time
const now = DateTime.now();

// Current time in specific timezone
const nowTokyo = DateTime.now().setZone('Asia/Tokyo');

// Today at midnight
const today = DateTime.now().startOf('day');

return [{
  json: {
    iso: now.toISO(),  // "2025-01-20T15:30:00.000Z"
    formatted: now.toFormat('yyyy-MM-dd HH:mm:ss'),  // "2025-01-20 15:30:00"
    unix: now.toSeconds(),  // Unix timestamp
    millis: now.toMillis()  // Milliseconds since epoch
  }
}];
```

### Formatting Dates

```javascript
const now = DateTime.now();

return [{
  json: {
    isoFormat: now.toISO(),  // ISO 8601: "2025-01-20T15:30:00.000Z"
    sqlFormat: now.toSQL(),  // SQL: "2025-01-20 15:30:00.000"
    httpFormat: now.toHTTP(),  // HTTP: "Mon, 20 Jan 2025 15:30:00 GMT"

    // Custom formats
    dateOnly: now.toFormat('yyyy-MM-dd'),  // "2025-01-20"
    timeOnly: now.toFormat('HH:mm:ss'),  // "15:30:00"
    readable: now.toFormat('MMMM dd, yyyy'),  // "January 20, 2025"
    compact: now.toFormat('yyyyMMdd'),  // "20250120"
    withDay: now.toFormat('EEEE, MMMM dd, yyyy'),  // "Monday, January 20, 2025"
    custom: now.toFormat('dd/MM/yy HH:mm')  // "20/01/25 15:30"
  }
}];
```

### Parsing Dates

```javascript
// From ISO string
const dt1 = DateTime.fromISO('2025-01-20T15:30:00');

// From specific format
const dt2 = DateTime.fromFormat('01/20/2025', 'MM/dd/yyyy');

// From SQL
const dt3 = DateTime.fromSQL('2025-01-20 15:30:00');

// From Unix timestamp
const dt4 = DateTime.fromSeconds(1737384600);

// From milliseconds
const dt5 = DateTime.fromMillis(1737384600000);

return [{json: {parsed: dt1.toISO()}}];
```

### Date Arithmetic

```javascript
const now = DateTime.now();

return [{
  json: {
    // Adding time
    tomorrow: now.plus({days: 1}).toISO(),
    nextWeek: now.plus({weeks: 1}).toISO(),
    nextMonth: now.plus({months: 1}).toISO(),
    inTwoHours: now.plus({hours: 2}).toISO(),

    // Subtracting time
    yesterday: now.minus({days: 1}).toISO(),
    lastWeek: now.minus({weeks: 1}).toISO(),
    lastMonth: now.minus({months: 1}).toISO(),
    twoHoursAgo: now.minus({hours: 2}).toISO(),

    // Complex operations
    in90Days: now.plus({days: 90}).toFormat('yyyy-MM-dd'),
    in6Months: now.plus({months: 6}).toFormat('yyyy-MM-dd')
  }
}];
```

### Time Comparisons

```javascript
const now = DateTime.now();
const targetDate = DateTime.fromISO('2025-12-31');

return [{
  json: {
    // Comparisons
    isFuture: targetDate > now,
    isPast: targetDate < now,
    isEqual: targetDate.equals(now),

    // Differences
    daysUntil: targetDate.diff(now, 'days').days,
    hoursUntil: targetDate.diff(now, 'hours').hours,
    monthsUntil: targetDate.diff(now, 'months').months,

    // Detailed difference
    detailedDiff: targetDate.diff(now, ['months', 'days', 'hours']).toObject()
  }
}];
```

### Timezone Operations

```javascript
const now = DateTime.now();

return [{
  json: {
    // Current timezone
    local: now.toISO(),

    // Convert to different timezone
    tokyo: now.setZone('Asia/Tokyo').toISO(),
    newYork: now.setZone('America/New_York').toISO(),
    london: now.setZone('Europe/London').toISO(),
    utc: now.toUTC().toISO(),

    // Get timezone info
    timezone: now.zoneName,  // "America/Los_Angeles"
    offset: now.offset,  // Offset in minutes
    offsetFormatted: now.toFormat('ZZ')  // "+08:00"
  }
}];
```

### Start/End of Period

```javascript
const now = DateTime.now();

return [{
  json: {
    startOfDay: now.startOf('day').toISO(),
    endOfDay: now.endOf('day').toISO(),
    startOfWeek: now.startOf('week').toISO(),
    endOfWeek: now.endOf('week').toISO(),
    startOfMonth: now.startOf('month').toISO(),
    endOfMonth: now.endOf('month').toISO(),
    startOfYear: now.startOf('year').toISO(),
    endOfYear: now.endOf('year').toISO()
  }
}];
```

### Weekday & Month Info

```javascript
const now = DateTime.now();

return [{
  json: {
    // Day info
    weekday: now.weekday,  // 1 = Monday, 7 = Sunday
    weekdayShort: now.weekdayShort,  // "Mon"
    weekdayLong: now.weekdayLong,  // "Monday"
    isWeekend: now.weekday > 5,  // Saturday or Sunday

    // Month info
    month: now.month,  // 1-12
    monthShort: now.monthShort,  // "Jan"
    monthLong: now.monthLong,  // "January"

    // Year info
    year: now.year,  // 2025
    quarter: now.quarter,  // 1-4
    daysInMonth: now.daysInMonth  // 28-31
  }
}];
```

---

## 3. $jmespath() - JSON Querying

Query and transform JSON structures using JMESPath syntax.

### Basic Queries

```javascript
const data = $input.first().json;

// Extract specific field
const names = $jmespath(data, 'users[*].name');

// Filter array
const adults = $jmespath(data, 'users[?age >= `18`]');

// Get specific index
const firstUser = $jmespath(data, 'users[0]');

return [{json: {names, adults, firstUser}}];
```

### Advanced Queries

```javascript
const data = $input.first().json;

// Sort and slice
const top5 = $jmespath(data, 'users | sort_by(@, &score) | reverse(@) | [0:5]');

// Extract nested fields
const emails = $jmespath(data, 'users[*].contact.email');

// Multi-field extraction
const simplified = $jmespath(data, 'users[*].{name: name, email: contact.email}');

// Conditional filtering
const premium = $jmespath(data, 'users[?subscription.tier == `premium`]');

return [{json: {top5, emails, simplified, premium}}];
```

### Common Patterns

```javascript
// Pattern 1: Filter and project
const query1 = $jmespath(data, 'products[?price > `100`].{name: name, price: price}');

// Pattern 2: Aggregate functions
const query2 = $jmespath(data, 'sum(products[*].price)');
const query3 = $jmespath(data, 'max(products[*].price)');
const query4 = $jmespath(data, 'length(products)');

// Pattern 3: Nested filtering
const query5 = $jmespath(data, 'categories[*].products[?inStock == `true`]');

return [{json: {query1, query2, query3, query4, query5}}];
```

---

## 4. $getWorkflowStaticData() - Persistent Storage

Store data that persists across workflow executions.

### Basic Usage

```javascript
// Get static data storage
const staticData = $getWorkflowStaticData();

// Initialize counter if doesn't exist
if (!staticData.counter) {
  staticData.counter = 0;
}

// Increment counter
staticData.counter++;

return [{
  json: {
    executionCount: staticData.counter
  }
}];
```

### Use Cases

```javascript
// Use Case 1: Rate limiting
const staticData = $getWorkflowStaticData();
const now = Date.now();

if (!staticData.lastRun) {
  staticData.lastRun = now;
  staticData.runCount = 1;
} else {
  const timeSinceLastRun = now - staticData.lastRun;

  if (timeSinceLastRun < 60000) {  // Less than 1 minute
    return [{json: {error: 'Rate limit: wait 1 minute between runs'}}];
  }

  staticData.lastRun = now;
  staticData.runCount++;
}

return [{json: {allowed: true, totalRuns: staticData.runCount}}];
```

```javascript
// Use Case 2: Tracking last processed ID
const staticData = $getWorkflowStaticData();
const currentItems = $input.all();

// Get last processed ID
const lastId = staticData.lastProcessedId || 0;

// Filter only new items
const newItems = currentItems.filter(item => item.json.id > lastId);

// Update last processed ID
if (newItems.length > 0) {
  staticData.lastProcessedId = Math.max(...newItems.map(item => item.json.id));
}

return newItems;
```

```javascript
// Use Case 3: Accumulating results
const staticData = $getWorkflowStaticData();

if (!staticData.accumulated) {
  staticData.accumulated = [];
}

// Add current items to accumulated list
const currentData = $input.all().map(item => item.json);
staticData.accumulated.push(...currentData);

return [{
  json: {
    currentBatch: currentData.length,
    totalAccumulated: staticData.accumulated.length,
    allData: staticData.accumulated
  }
}];
```

---

## 5. Standard JavaScript Globals

### Math Object

```javascript
return [{
  json: {
    // Rounding
    rounded: Math.round(3.7),  // 4
    floor: Math.floor(3.7),  // 3
    ceil: Math.ceil(3.2),  // 4

    // Min/Max
    max: Math.max(1, 5, 3, 9, 2),  // 9
    min: Math.min(1, 5, 3, 9, 2),  // 1

    // Random
    random: Math.random(),  // 0-1
    randomInt: Math.floor(Math.random() * 100),  // 0-99

    // Other
    abs: Math.abs(-5),  // 5
    sqrt: Math.sqrt(16),  // 4
    pow: Math.pow(2, 3)  // 8
  }
}];
```

### JSON Object

```javascript
// Parse JSON string
const jsonString = '{"name": "John", "age": 30}';
const parsed = JSON.parse(jsonString);

// Stringify object
const obj = {name: "John", age: 30};
const stringified = JSON.stringify(obj);

// Pretty print
const pretty = JSON.stringify(obj, null, 2);

return [{json: {parsed, stringified, pretty}}];
```

### console Object

```javascript
// Debug logging (appears in browser console, press F12)
console.log('Processing items:', $input.all().length);
console.log('First item:', $input.first().json);

// Other console methods
console.error('Error message');
console.warn('Warning message');
console.info('Info message');

// Continues to return data
return [{json: {processed: true}}];
```

### Object Methods

```javascript
const obj = {name: "John", age: 30, city: "NYC"};

return [{
  json: {
    keys: Object.keys(obj),  // ["name", "age", "city"]
    values: Object.values(obj),  // ["John", 30, "NYC"]
    entries: Object.entries(obj),  // [["name", "John"], ...]

    // Check property
    hasName: 'name' in obj,  // true

    // Merge objects
    merged: Object.assign({}, obj, {country: "USA"})
  }
}];
```

### Array Methods

```javascript
const arr = [1, 2, 3, 4, 5];

return [{
  json: {
    mapped: arr.map(x => x * 2),  // [2, 4, 6, 8, 10]
    filtered: arr.filter(x => x > 2),  // [3, 4, 5]
    reduced: arr.reduce((sum, x) => sum + x, 0),  // 15
    some: arr.some(x => x > 3),  // true
    every: arr.every(x => x > 0),  // true
    find: arr.find(x => x > 3),  // 4
    includes: arr.includes(3),  // true
    joined: arr.join(', ')  // "1, 2, 3, 4, 5"
  }
}];
```

---

## 6. Available Node.js Modules

### crypto Module

```javascript
const crypto = require('crypto');

// Hash functions
const hash = crypto.createHash('sha256')
  .update('my secret text')
  .digest('hex');

// MD5 hash
const md5 = crypto.createHash('md5')
  .update('my text')
  .digest('hex');

// Random values
const randomBytes = crypto.randomBytes(16).toString('hex');

return [{json: {hash, md5, randomBytes}}];
```

### Buffer (built-in)

```javascript
// Base64 encoding
const encoded = Buffer.from('Hello World').toString('base64');

// Base64 decoding
const decoded = Buffer.from(encoded, 'base64').toString();

// Hex encoding
const hex = Buffer.from('Hello').toString('hex');

return [{json: {encoded, decoded, hex}}];
```

### URL / URLSearchParams

```javascript
// Parse URL
const url = new URL('https://example.com/path?param1=value1&param2=value2');

// Build query string
const params = new URLSearchParams({
  search: 'query',
  page: 1,
  limit: 10
});

return [{
  json: {
    host: url.host,
    pathname: url.pathname,
    search: url.search,
    queryString: params.toString()  // "search=query&page=1&limit=10"
  }
}];
```

---

## What's NOT Available

**External npm packages are NOT available:**
- ❌ axios
- ❌ lodash
- ❌ moment (use DateTime/Luxon instead)
- ❌ request
- ❌ Any other npm package

**Workaround**: Use $helpers.httpRequest() for HTTP, or add data to workflow via HTTP Request node.

---

## Summary

**Most Useful Built-ins**:
1. **$helpers.httpRequest()** - API calls without HTTP Request node
2. **DateTime** - Professional date/time handling
3. **$jmespath()** - Complex JSON queries
4. **Math, JSON, Object, Array** - Standard JavaScript utilities

**Common Patterns**:
- API calls: Use $helpers.httpRequest()
- Date operations: Use DateTime (Luxon)
- Data filtering: Use $jmespath() or JavaScript .filter()
- Persistent data: Use $getWorkflowStaticData()
- Hashing: Use crypto module

**See Also**:
- [SKILL.md](SKILL.md) - Overview
- [COMMON_PATTERNS.md](COMMON_PATTERNS.md) - Real usage examples
- [ERROR_PATTERNS.md](ERROR_PATTERNS.md) - Error prevention
