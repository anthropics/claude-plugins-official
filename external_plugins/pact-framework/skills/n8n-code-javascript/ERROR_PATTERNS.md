# Error Patterns - JavaScript Code Node

Complete guide to avoiding the most common Code node errors.

---

## Overview

This guide covers the **top 5 error patterns** encountered in n8n Code nodes. Understanding and avoiding these errors will save you significant debugging time.

**Error Frequency**:
1. Empty Code / Missing Return - **38% of failures**
2. Expression Syntax Confusion - **8% of failures**
3. Incorrect Return Wrapper - **5% of failures**
4. Unmatched Expression Brackets - **6% of failures**
5. Missing Null Checks - **Common runtime error**

---

## Error #1: Empty Code or Missing Return Statement

**Frequency**: Most common error (38% of all validation failures)

**What Happens**:
- Workflow execution fails
- Next nodes receive no data
- Error: "Code cannot be empty" or "Code must return data"

### The Problem

```javascript
// ❌ ERROR: No code at all
// (Empty code field)
```

```javascript
// ❌ ERROR: Code executes but doesn't return anything
const items = $input.all();

// Process items
for (const item of items) {
  console.log(item.json.name);
}

// Forgot to return!
```

```javascript
// ❌ ERROR: Early return path exists, but not all paths return
const items = $input.all();

if (items.length === 0) {
  return [];  // ✅ This path returns
}

// Process items
const processed = items.map(item => ({json: item.json}));

// ❌ Forgot to return processed!
```

### The Solution

```javascript
// ✅ CORRECT: Always return data
const items = $input.all();

// Process items
const processed = items.map(item => ({
  json: {
    ...item.json,
    processed: true
  }
}));

return processed;  // ✅ Return statement present
```

```javascript
// ✅ CORRECT: Return empty array if no items
const items = $input.all();

if (items.length === 0) {
  return [];  // Valid: empty array when no data
}

// Process and return
return items.map(item => ({json: item.json}));
```

```javascript
// ✅ CORRECT: All code paths return
const items = $input.all();

if (items.length === 0) {
  return [];
} else if (items.length === 1) {
  return [{json: {single: true, data: items[0].json}}];
} else {
  return items.map(item => ({json: item.json}));
}

// All paths covered
```

### Checklist

- [ ] Code field is not empty
- [ ] Return statement exists
- [ ] ALL code paths return data (if/else branches)
- [ ] Return format is correct (`[{json: {...}}]`)
- [ ] Return happens even on errors (use try-catch)

---

## Error #2: Expression Syntax Confusion

**Frequency**: 8% of validation failures

**What Happens**:
- Syntax error in code execution
- Error: "Unexpected token" or "Expression syntax is not valid in Code nodes"
- Template variables not evaluated

### The Problem

n8n has TWO distinct syntaxes:
1. **Expression syntax** `{{ }}` - Used in OTHER nodes (Set, IF, HTTP Request)
2. **JavaScript** - Used in CODE nodes (no `{{ }}`)

Many developers mistakenly use expression syntax inside Code nodes.

```javascript
// ❌ WRONG: Using n8n expression syntax in Code node
const userName = "{{ $json.name }}";
const userEmail = "{{ $json.body.email }}";

return [{
  json: {
    name: userName,
    email: userEmail
  }
}];

// Result: Literal string "{{ $json.name }}", NOT the value!
```

```javascript
// ❌ WRONG: Trying to evaluate expressions
const value = "{{ $now.toFormat('yyyy-MM-dd') }}";
```

### The Solution

```javascript
// ✅ CORRECT: Use JavaScript directly (no {{ }})
const userName = $json.name;
const userEmail = $json.body.email;

return [{
  json: {
    name: userName,
    email: userEmail
  }
}];
```

```javascript
// ✅ CORRECT: JavaScript template literals (use backticks)
const message = `Hello, ${$json.name}! Your email is ${$json.email}`;

return [{
  json: {
    greeting: message
  }
}];
```

```javascript
// ✅ CORRECT: Direct variable access
const item = $input.first().json;

return [{
  json: {
    name: item.name,
    email: item.email,
    timestamp: new Date().toISOString()  // JavaScript Date, not {{ }}
  }
}];
```

### Comparison Table

| Context | Syntax | Example |
|---------|--------|---------|
| Set node | `{{ }}` expressions | `{{ $json.name }}` |
| IF node | `{{ }}` expressions | `{{ $json.age > 18 }}` |
| HTTP Request URL | `{{ }}` expressions | `{{ $json.userId }}` |
| **Code node** | **JavaScript** | `$json.name` |
| **Code node strings** | **Template literals** | `` `Hello ${$json.name}` `` |

### Quick Fix Guide

```javascript
// WRONG → RIGHT conversions

// ❌ "{{ $json.field }}"
// ✅ $json.field

// ❌ "{{ $now }}"
// ✅ new Date().toISOString()

// ❌ "{{ $node['HTTP Request'].json.data }}"
// ✅ $node["HTTP Request"].json.data

// ❌ `{{ $json.firstName }} {{ $json.lastName }}`
// ✅ `${$json.firstName} ${$json.lastName}`
```

---

## Error #3: Incorrect Return Wrapper Format

**Frequency**: 5% of validation failures

**What Happens**:
- Error: "Return value must be an array of objects"
- Error: "Each item must have a json property"
- Next nodes receive malformed data

### The Problem

Code nodes MUST return:
- **Array** of objects
- Each object MUST have a **`json` property**

```javascript
// ❌ WRONG: Returning object instead of array
return {
  json: {
    result: 'success'
  }
};
// Missing array wrapper []
```

```javascript
// ❌ WRONG: Returning array without json wrapper
return [
  {id: 1, name: 'Alice'},
  {id: 2, name: 'Bob'}
];
// Missing json property
```

```javascript
// ❌ WRONG: Returning plain value
return "processed";
```

```javascript
// ❌ WRONG: Returning items without mapping
return $input.all();
// Works if items already have json property, but not guaranteed
```

```javascript
// ❌ WRONG: Incomplete structure
return [{data: {result: 'success'}}];
// Should be {json: {...}}, not {data: {...}}
```

### The Solution

```javascript
// ✅ CORRECT: Single result
return [{
  json: {
    result: 'success',
    timestamp: new Date().toISOString()
  }
}];
```

```javascript
// ✅ CORRECT: Multiple results
return [
  {json: {id: 1, name: 'Alice'}},
  {json: {id: 2, name: 'Bob'}},
  {json: {id: 3, name: 'Carol'}}
];
```

```javascript
// ✅ CORRECT: Transforming array
const items = $input.all();

return items.map(item => ({
  json: {
    id: item.json.id,
    name: item.json.name,
    processed: true
  }
}));
```

```javascript
// ✅ CORRECT: Empty result
return [];
// Valid when no data to return
```

```javascript
// ✅ CORRECT: Conditional returns
if (shouldProcess) {
  return [{json: {result: 'processed'}}];
} else {
  return [];
}
```

### Return Format Checklist

- [ ] Return value is an **array** `[...]`
- [ ] Each array element has **`json` property**
- [ ] Structure is `[{json: {...}}]` or `[{json: {...}}, {json: {...}}]`
- [ ] NOT `{json: {...}}` (missing array wrapper)
- [ ] NOT `[{...}]` (missing json property)

### Common Scenarios

```javascript
// Scenario 1: Single object from API
const response = $input.first().json;

// ✅ CORRECT
return [{json: response}];

// ❌ WRONG
return {json: response};


// Scenario 2: Array of objects
const users = $input.all();

// ✅ CORRECT
return users.map(user => ({json: user.json}));

// ❌ WRONG
return users;  // Risky - depends on existing structure


// Scenario 3: Computed result
const total = $input.all().reduce((sum, item) => sum + item.json.amount, 0);

// ✅ CORRECT
return [{json: {total}}];

// ❌ WRONG
return {total};


// Scenario 4: No results
// ✅ CORRECT
return [];

// ❌ WRONG
return null;
```

---

## Error #4: Unmatched Expression Brackets

**Frequency**: 6% of validation failures

**What Happens**:
- Parsing error during save
- Error: "Unmatched expression brackets"
- Code appears correct but fails validation

### The Problem

This error typically occurs when:
1. Strings contain unbalanced quotes
2. Multi-line strings with special characters
3. Template literals with nested brackets

```javascript
// ❌ WRONG: Unescaped quote in string
const message = "It's a nice day";
// Single quote breaks string
```

```javascript
// ❌ WRONG: Unbalanced brackets in regex
const pattern = /\{(\w+)\}/;  // JSON storage issue
```

```javascript
// ❌ WRONG: Multi-line string with quotes
const html = "
  <div class="container">
    <p>Hello</p>
  </div>
";
// Quote balance issues
```

### The Solution

```javascript
// ✅ CORRECT: Escape quotes
const message = "It\\'s a nice day";
// Or use different quotes
const message = "It's a nice day";  // Double quotes work
```

```javascript
// ✅ CORRECT: Escape regex properly
const pattern = /\\{(\\w+)\\}/;
```

```javascript
// ✅ CORRECT: Template literals for multi-line
const html = `
  <div class="container">
    <p>Hello</p>
  </div>
`;
// Backticks handle multi-line and quotes
```

```javascript
// ✅ CORRECT: Escape backslashes
const path = "C:\\\\Users\\\\Documents\\\\file.txt";
```

### Escaping Guide

| Character | Escape As | Example |
|-----------|-----------|---------|
| Single quote in single-quoted string | `\\'` | `'It\\'s working'` |
| Double quote in double-quoted string | `\\"` | `"She said \\"hello\\""` |
| Backslash | `\\\\` | `"C:\\\\path"` |
| Newline | `\\n` | `"Line 1\\nLine 2"` |
| Tab | `\\t` | `"Column1\\tColumn2"` |

### Best Practices

```javascript
// ✅ BEST: Use template literals for complex strings
const message = `User ${name} said: "Hello!"`;

// ✅ BEST: Use template literals for HTML
const html = `
  <div class="${className}">
    <h1>${title}</h1>
    <p>${content}</p>
  </div>
`;

// ✅ BEST: Use template literals for JSON
const jsonString = `{
  "name": "${name}",
  "email": "${email}"
}`;
```

---

## Error #5: Missing Null Checks / Undefined Access

**Frequency**: Very common runtime error

**What Happens**:
- Workflow execution stops
- Error: "Cannot read property 'X' of undefined"
- Error: "Cannot read property 'X' of null"
- Crashes on missing data

### The Problem

```javascript
// ❌ WRONG: No null check - crashes if user doesn't exist
const email = item.json.user.email;
```

```javascript
// ❌ WRONG: Assumes array has items
const firstItem = $input.all()[0].json;
```

```javascript
// ❌ WRONG: Assumes nested property exists
const city = $json.address.city;
```

```javascript
// ❌ WRONG: No validation before array operations
const names = $json.users.map(user => user.name);
```

### The Solution

```javascript
// ✅ CORRECT: Optional chaining
const email = item.json?.user?.email || 'no-email@example.com';
```

```javascript
// ✅ CORRECT: Check array length
const items = $input.all();

if (items.length === 0) {
  return [];
}

const firstItem = items[0].json;
```

```javascript
// ✅ CORRECT: Guard clauses
const data = $input.first().json;

if (!data.address) {
  return [{json: {error: 'No address provided'}}];
}

const city = data.address.city;
```

```javascript
// ✅ CORRECT: Default values
const users = $json.users || [];
const names = users.map(user => user.name || 'Unknown');
```

```javascript
// ✅ CORRECT: Try-catch for risky operations
try {
  const email = item.json.user.email.toLowerCase();
  return [{json: {email}}];
} catch (error) {
  return [{
    json: {
      error: 'Invalid user data',
      details: error.message
    }
  }];
}
```

### Safe Access Patterns

```javascript
// Pattern 1: Optional chaining (modern, recommended)
const value = data?.nested?.property?.value;

// Pattern 2: Logical OR with default
const value = data.property || 'default';

// Pattern 3: Ternary check
const value = data.property ? data.property : 'default';

// Pattern 4: Guard clause
if (!data.property) {
  return [];
}
const value = data.property;

// Pattern 5: Try-catch
try {
  const value = data.nested.property.value;
} catch (error) {
  const value = 'default';
}
```

### Webhook Data Safety

```javascript
// Webhook data requires extra safety

// ❌ RISKY: Assumes all fields exist
const name = $json.body.user.name;
const email = $json.body.user.email;

// ✅ SAFE: Check each level
const body = $json.body || {};
const user = body.user || {};
const name = user.name || 'Unknown';
const email = user.email || 'no-email';

// ✅ BETTER: Optional chaining
const name = $json.body?.user?.name || 'Unknown';
const email = $json.body?.user?.email || 'no-email';
```

### Array Safety

```javascript
// ❌ RISKY: No length check
const items = $input.all();
const firstId = items[0].json.id;

// ✅ SAFE: Check length
const items = $input.all();

if (items.length > 0) {
  const firstId = items[0].json.id;
} else {
  // Handle empty case
  return [];
}

// ✅ BETTER: Use $input.first()
const firstItem = $input.first();
const firstId = firstItem.json.id;  // Built-in safety
```

### Object Property Safety

```javascript
// ❌ RISKY: Direct access
const config = $json.settings.advanced.timeout;

// ✅ SAFE: Step by step with defaults
const settings = $json.settings || {};
const advanced = settings.advanced || {};
const timeout = advanced.timeout || 30000;

// ✅ BETTER: Optional chaining
const timeout = $json.settings?.advanced?.timeout ?? 30000;
// Note: ?? (nullish coalescing) vs || (logical OR)
```

---

## Error Prevention Checklist

Use this checklist before deploying Code nodes:

### Code Structure
- [ ] Code field is not empty
- [ ] Return statement exists
- [ ] All code paths return data

### Return Format
- [ ] Returns array: `[...]`
- [ ] Each item has `json` property: `{json: {...}}`
- [ ] Format is `[{json: {...}}]`

### Syntax
- [ ] No `{{ }}` expression syntax (use JavaScript)
- [ ] Template literals use backticks: `` `${variable}` ``
- [ ] All quotes and brackets balanced
- [ ] Strings properly escaped

### Data Safety
- [ ] Null checks for optional properties
- [ ] Array length checks before access
- [ ] Webhook data accessed via `.body`
- [ ] Try-catch for risky operations
- [ ] Default values for missing data

### Testing
- [ ] Test with empty input
- [ ] Test with missing fields
- [ ] Test with unexpected data types
- [ ] Check browser console for errors

---

## Quick Error Reference

| Error Message | Likely Cause | Fix |
|---------------|--------------|-----|
| "Code cannot be empty" | Empty code field | Add meaningful code |
| "Code must return data" | Missing return statement | Add `return [...]` |
| "Return value must be an array" | Returning object instead of array | Wrap in `[...]` |
| "Each item must have json property" | Missing `json` wrapper | Use `{json: {...}}` |
| "Unexpected token" | Expression syntax `{{ }}` in code | Remove `{{ }}`, use JavaScript |
| "Cannot read property X of undefined" | Missing null check | Use optional chaining `?.` |
| "Cannot read property X of null" | Null value access | Add guard clause or default |
| "Unmatched expression brackets" | Quote/bracket imbalance | Check string escaping |

---

## Debugging Tips

### 1. Use console.log()

```javascript
const items = $input.all();
console.log('Items count:', items.length);
console.log('First item:', items[0]);

// Check browser console (F12) for output
```

### 2. Return Intermediate Results

```javascript
// Debug by returning current state
const items = $input.all();
const processed = items.map(item => ({json: item.json}));

// Return to see what you have
return processed;
```

### 3. Try-Catch for Troubleshooting

```javascript
try {
  // Your code here
  const result = riskyOperation();
  return [{json: {result}}];
} catch (error) {
  // See what failed
  return [{
    json: {
      error: error.message,
      stack: error.stack
    }
  }];
}
```

### 4. Validate Input Structure

```javascript
const items = $input.all();

// Check what you received
console.log('Input structure:', JSON.stringify(items[0], null, 2));

// Then process
```

---

## Summary

**Top 5 Errors to Avoid**:
1. **Empty code / missing return** (38%) - Always return data
2. **Expression syntax `{{ }}`** (8%) - Use JavaScript, not expressions
3. **Wrong return format** (5%) - Always `[{json: {...}}]`
4. **Unmatched brackets** (6%) - Escape strings properly
5. **Missing null checks** - Use optional chaining `?.`

**Quick Prevention**:
- Return `[{json: {...}}]` format
- Use JavaScript, NOT `{{ }}` expressions
- Check for null/undefined before accessing
- Test with empty and invalid data
- Use browser console for debugging

**See Also**:
- [SKILL.md](SKILL.md) - Overview and best practices
- [DATA_ACCESS.md](DATA_ACCESS.md) - Safe data access patterns
- [COMMON_PATTERNS.md](COMMON_PATTERNS.md) - Working examples
