# Error Patterns - Python Code Node

Common Python Code node errors and how to fix them.

---

## Error Overview

**Top 5 Python Code Node Errors**:

1. **ModuleNotFoundError** - Trying to import external libraries (Python-specific)
2. **Empty Code / Missing Return** - No code or return statement
3. **KeyError** - Dictionary access without .get()
4. **IndexError** - List access without bounds checking
5. **Incorrect Return Format** - Wrong data structure returned

These 5 errors cover the majority of Python Code node failures.

---

## Error #1: ModuleNotFoundError (MOST CRITICAL)

**Frequency**: Very common in Python Code nodes

**What it is**: Attempting to import external libraries that aren't available.

### The Problem

```python
# ❌ WRONG: External libraries not available
import requests  # ModuleNotFoundError: No module named 'requests'
import pandas    # ModuleNotFoundError: No module named 'pandas'
import numpy     # ModuleNotFoundError: No module named 'numpy'
import bs4       # ModuleNotFoundError: No module named 'bs4'
import pymongo   # ModuleNotFoundError: No module named 'pymongo'
import psycopg2  # ModuleNotFoundError: No module named 'psycopg2'

# This code will FAIL - these libraries are not installed!
response = requests.get("https://api.example.com/data")
```

### The Solution

**Option 1: Use JavaScript Instead** (Recommended for 95% of cases)

```javascript
// ✅ JavaScript Code node with $helpers.httpRequest()
const response = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/data'
});

return [{json: response}];
```

**Option 2: Use n8n HTTP Request Node**

```python
# ✅ Add HTTP Request node BEFORE Python Code node
# Access the response in Python Code node

response = _input.first()["json"]

return [{
    "json": {
        "status": response.get("status"),
        "data": response.get("body"),
        "processed": True
    }
}]
```

**Option 3: Use Standard Library Only**

```python
# ✅ Use urllib from standard library (limited functionality)
from urllib.request import urlopen
from urllib.parse import urlencode
import json

# Simple GET request (no headers, no auth)
url = "https://api.example.com/data"
with urlopen(url) as response:
    data = json.loads(response.read())

return [{"json": data}]
```

### Common Library Replacements

| Need | ❌ External Library | ✅ Alternative |
|------|-------------------|----------------|
| HTTP requests | `requests` | Use HTTP Request node or JavaScript |
| Data analysis | `pandas` | Use Python list comprehensions |
| Database | `psycopg2`, `pymongo` | Use n8n database nodes |
| Web scraping | `beautifulsoup4` | Use HTML Extract node |
| Excel | `openpyxl` | Use Spreadsheet File node |
| Image processing | `pillow` | Use external API or node |

### Available Standard Library Modules

```python
# ✅ THESE WORK - Standard library only
import json          # JSON parsing
import datetime      # Date/time operations
import re            # Regular expressions
import base64        # Base64 encoding
import hashlib       # Hashing (MD5, SHA256)
import urllib.parse  # URL parsing and encoding
import math          # Math functions
import random        # Random numbers
import statistics    # Statistical functions
import collections   # defaultdict, Counter, etc.
```

---

## Error #2: Empty Code / Missing Return

**Frequency**: Common across all Code nodes

**What it is**: Code node has no code or no return statement.

### The Problem

```python
# ❌ WRONG: Empty code
# (nothing here)

# ❌ WRONG: Code but no return
items = _input.all()
processed = [item for item in items if item["json"].get("active")]
# Forgot to return!

# ❌ WRONG: Return in wrong scope
if _input.all():
    return [{"json": {"result": "success"}}]
# Return is inside if block - may not execute!
```

### The Solution

```python
# ✅ CORRECT: Always return
all_items = _input.all()

if not all_items:
    # Return empty array or error
    return [{"json": {"error": "No items"}}]

# Process items
processed = [item for item in all_items if item["json"].get("active")]

# Always return at the end
return processed if processed else [{"json": {"message": "No active items"}}]
```

### Best Practice

```python
# ✅ GOOD: Return at end of function (unconditional)
def process_items():
    items = _input.all()

    if not items:
        return [{"json": {"error": "Empty input"}}]

    # Process
    result = []
    for item in items:
        result.append({"json": item["json"]})

    return result

# Call function and return result
return process_items()
```

---

## Error #3: KeyError

**Frequency**: Very common in Python Code nodes

**What it is**: Accessing dictionary key that doesn't exist.

### The Problem

```python
# ❌ WRONG: Direct key access
item = _input.first()["json"]

name = item["name"]        # KeyError if "name" doesn't exist!
email = item["email"]      # KeyError if "email" doesn't exist!
age = item["age"]          # KeyError if "age" doesn't exist!

return [{
    "json": {
        "name": name,
        "email": email,
        "age": age
    }
}]
```

### Error Message

```
KeyError: 'name'
```

### The Solution

```python
# ✅ CORRECT: Use .get() with defaults
item = _input.first()["json"]

name = item.get("name", "Unknown")
email = item.get("email", "no-email@example.com")
age = item.get("age", 0)

return [{
    "json": {
        "name": name,
        "email": email,
        "age": age
    }
}]
```

### Nested Dictionary Access

```python
# ❌ WRONG: Nested key access
webhook = _input.first()["json"]
name = webhook["body"]["user"]["name"]  # Multiple KeyErrors possible!

# ✅ CORRECT: Safe nested access
webhook = _input.first()["json"]
body = webhook.get("body", {})
user = body.get("user", {})
name = user.get("name", "Unknown")

# ✅ ALSO CORRECT: Chained .get()
name = (
    webhook
    .get("body", {})
    .get("user", {})
    .get("name", "Unknown")
)

return [{"json": {"name": name}}]
```

### Webhook Body Access (Critical!)

```python
# ❌ WRONG: Forgetting webhook data is under "body"
webhook = _input.first()["json"]
name = webhook["name"]        # KeyError!
email = webhook["email"]      # KeyError!

# ✅ CORRECT: Access via ["body"]
webhook = _input.first()["json"]
body = webhook.get("body", {})
name = body.get("name", "Unknown")
email = body.get("email", "no-email")

return [{
    "json": {
        "name": name,
        "email": email
    }
}]
```

---

## Error #4: IndexError

**Frequency**: Common when processing arrays/lists

**What it is**: Accessing list index that doesn't exist.

### The Problem

```python
# ❌ WRONG: Assuming items exist
all_items = _input.all()
first_item = all_items[0]        # IndexError if list is empty!
second_item = all_items[1]       # IndexError if only 1 item!

return [{
    "json": {
        "first": first_item["json"],
        "second": second_item["json"]
    }
}]
```

### Error Message

```
IndexError: list index out of range
```

### The Solution

```python
# ✅ CORRECT: Check length first
all_items = _input.all()

if len(all_items) >= 2:
    first_item = all_items[0]["json"]
    second_item = all_items[1]["json"]

    return [{
        "json": {
            "first": first_item,
            "second": second_item
        }
    }]
else:
    return [{
        "json": {
            "error": f"Expected 2+ items, got {len(all_items)}"
        }
    }]
```

### Safe First Item Access

```python
# ✅ CORRECT: Use _input.first() instead of [0]
# This is safer than manual indexing
first_item = _input.first()["json"]

return [{"json": first_item}]

# ✅ ALSO CORRECT: Check before accessing
all_items = _input.all()
if all_items:
    first_item = all_items[0]["json"]
else:
    first_item = {}

return [{"json": first_item}]
```

### Slice Instead of Index

```python
# ✅ CORRECT: Use slicing (never raises IndexError)
all_items = _input.all()

# Get first 5 items (won't fail if fewer than 5)
first_five = all_items[:5]

# Get items after first (won't fail if empty)
rest = all_items[1:]

return [{"json": item["json"]} for item in first_five]
```

---

## Error #5: Incorrect Return Format

**Frequency**: Common for new users

**What it is**: Returning data in wrong format (n8n expects array of objects with "json" key).

### The Problem

```python
# ❌ WRONG: Returning plain dictionary
return {"name": "Alice", "age": 30}

# ❌ WRONG: Returning array without "json" wrapper
return [{"name": "Alice"}, {"name": "Bob"}]

# ❌ WRONG: Returning None
return None

# ❌ WRONG: Returning string
return "success"

# ❌ WRONG: Returning single item (not array)
return {"json": {"name": "Alice"}}
```

### The Solution

```python
# ✅ CORRECT: Array of objects with "json" key
return [{"json": {"name": "Alice", "age": 30}}]

# ✅ CORRECT: Multiple items
return [
    {"json": {"name": "Alice"}},
    {"json": {"name": "Bob"}}
]

# ✅ CORRECT: Transform items
all_items = _input.all()
return [
    {"json": item["json"]}
    for item in all_items
]

# ✅ CORRECT: Empty array (valid)
return []

# ✅ CORRECT: Single item still needs array wrapper
return [{"json": {"result": "success"}}]
```

### Common Scenarios

**Scenario 1: Aggregation (Return Single Result)**

```python
# Calculate total
all_items = _input.all()
total = sum(item["json"].get("amount", 0) for item in all_items)

# ✅ CORRECT: Wrap in array with "json"
return [{
    "json": {
        "total": total,
        "count": len(all_items)
    }
}]
```

**Scenario 2: Filtering (Return Multiple Results)**

```python
# Filter active items
all_items = _input.all()
active = [item for item in all_items if item["json"].get("active")]

# ✅ CORRECT: Already in correct format
return active

# ✅ ALSO CORRECT: If transforming
return [
    {"json": {**item["json"], "filtered": True}}
    for item in active
]
```

**Scenario 3: No Results**

```python
# ✅ CORRECT: Return empty array
return []

# ✅ ALSO CORRECT: Return error message
return [{"json": {"error": "No results found"}}]
```

---

## Bonus Error: AttributeError

**What it is**: Using _input.item in wrong mode.

### The Problem

```python
# ❌ WRONG: Using _input.item in "All Items" mode
current = _input.item        # None in "All Items" mode
data = current["json"]       # AttributeError: 'NoneType' object has no attribute '__getitem__'
```

### The Solution

```python
# ✅ CORRECT: Check mode or use appropriate method
# In "All Items" mode, use:
all_items = _input.all()

# In "Each Item" mode, use:
current_item = _input.item

# ✅ SAFE: Check if item exists
current = _input.item
if current:
    data = current["json"]
    return [{"json": data}]
else:
    # Running in "All Items" mode
    return _input.all()
```

---

## Error Prevention Checklist

Before running your Python Code node, verify:

- [ ] **No external imports**: Only standard library (json, datetime, re, etc.)
- [ ] **Code returns data**: Every code path ends with `return`
- [ ] **Correct format**: Returns `[{"json": {...}}]` (array with "json" key)
- [ ] **Safe dictionary access**: Uses `.get()` instead of `[]` for dictionaries
- [ ] **Safe list access**: Checks length before indexing or uses slicing
- [ ] **Webhook body access**: Accesses webhook data via `_json["body"]`
- [ ] **No None returns**: Returns empty array `[]` instead of `None`
- [ ] **Mode awareness**: Uses `_input.all()`, `_input.first()`, or `_input.item` appropriately

---

## Quick Fix Reference

| Error | Quick Fix |
|-------|-----------|
| `ModuleNotFoundError` | Use JavaScript or HTTP Request node instead |
| `KeyError: 'field'` | Change `data["field"]` to `data.get("field", default)` |
| `IndexError: list index out of range` | Check `if len(items) > 0:` before `items[0]` |
| Empty output | Add `return [{"json": {...}}]` at end |
| `AttributeError: 'NoneType'` | Check mode setting or verify `_input.item` exists |
| Wrong format error | Wrap result: `return [{"json": result}]` |
| Webhook KeyError | Access via `_json.get("body", {})` |

---

## Testing Your Code

### Test Pattern 1: Handle Empty Input

```python
# ✅ Always test with empty input
all_items = _input.all()

if not all_items:
    return [{"json": {"message": "No items to process"}}]

# Continue with processing
# ...
```

### Test Pattern 2: Test with Missing Fields

```python
# ✅ Use .get() with defaults
item = _input.first()["json"]

# These won't fail even if fields missing
name = item.get("name", "Unknown")
email = item.get("email", "no-email")
age = item.get("age", 0)

return [{"json": {"name": name, "email": email, "age": age}}]
```

### Test Pattern 3: Test Both Modes

```python
# ✅ Code that works in both modes
try:
    # Try "Each Item" mode first
    current = _input.item
    if current:
        return [{"json": current["json"]}]
except:
    pass

# Fall back to "All Items" mode
all_items = _input.all()
return all_items if all_items else [{"json": {"message": "No data"}}]
```

---

## Summary

**Top 5 Errors to Avoid**:
1. **ModuleNotFoundError** - Use JavaScript or n8n nodes instead
2. **Missing return** - Always end with `return [{"json": {...}}]`
3. **KeyError** - Use `.get()` for dictionary access
4. **IndexError** - Check length before indexing
5. **Wrong format** - Return `[{"json": {...}}]`, not plain objects

**Golden Rules**:
- NO external libraries (use JavaScript instead)
- ALWAYS use `.get()` for dictionaries
- ALWAYS return `[{"json": {...}}]` format
- CHECK lengths before list access
- ACCESS webhook data via `["body"]`

**Remember**:
- JavaScript is recommended for 95% of use cases
- Python has limitations (no requests, pandas, numpy)
- Use n8n nodes for complex operations

**See Also**:
- [SKILL.md](SKILL.md) - Python Code overview
- [DATA_ACCESS.md](DATA_ACCESS.md) - Data access patterns
- [STANDARD_LIBRARY.md](STANDARD_LIBRARY.md) - Available modules
- [COMMON_PATTERNS.md](COMMON_PATTERNS.md) - Production patterns
