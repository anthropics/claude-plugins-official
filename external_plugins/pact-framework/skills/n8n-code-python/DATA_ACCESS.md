# Data Access Patterns - Python Code Node

Complete guide to accessing data in n8n Code nodes using Python.

---

## Overview

In n8n Python Code nodes, you access data using **underscore-prefixed** variables: `_input`, `_json`, `_node`.

**Data Access Priority** (by common usage):
1. **`_input.all()`** - Most common - Batch operations, aggregations
2. **`_input.first()`** - Very common - Single item operations
3. **`_input.item`** - Common - Each Item mode only
4. **`_node["NodeName"]["json"]`** - Specific node references
5. **`_json`** - Direct current item (use `_input` instead)

**Python vs JavaScript**:
| JavaScript | Python (Beta) | Python (Native) |
|------------|---------------|-----------------|
| `$input.all()` | `_input.all()` | `_items` |
| `$input.first()` | `_input.first()` | `_items[0]` |
| `$input.item` | `_input.item` | `_item` |
| `$json` | `_json` | `_item["json"]` |
| `$node["Name"]` | `_node["Name"]` | Not available |

---

## Pattern 1: _input.all() - Process All Items

**Usage**: Most common pattern for batch processing

**When to use:**
- Processing multiple records
- Aggregating data (sum, count, average)
- Filtering lists
- Transforming datasets

### Basic Usage

```python
# Get all items from previous node
all_items = _input.all()

# all_items is a list of dictionaries like:
# [
#   {"json": {"id": 1, "name": "Alice"}},
#   {"json": {"id": 2, "name": "Bob"}}
# ]

print(f"Received {len(all_items)} items")

return all_items
```

### Example 1: Filter Active Items

```python
all_items = _input.all()

# Filter only active items
active_items = [
    item for item in all_items
    if item["json"].get("status") == "active"
]

return active_items
```

### Example 2: Transform All Items

```python
all_items = _input.all()

# Transform to new structure
transformed = []
for item in all_items:
    transformed.append({
        "json": {
            "id": item["json"].get("id"),
            "full_name": f"{item['json'].get('first_name', '')} {item['json'].get('last_name', '')}",
            "email": item["json"].get("email"),
            "processed_at": datetime.now().isoformat()
        }
    })

return transformed
```

### Example 3: Aggregate Data

```python
all_items = _input.all()

# Calculate total
total = sum(item["json"].get("amount", 0) for item in all_items)

return [{
    "json": {
        "total": total,
        "count": len(all_items),
        "average": total / len(all_items) if all_items else 0
    }
}]
```

### Example 4: Sort and Limit

```python
all_items = _input.all()

# Get top 5 by score
sorted_items = sorted(
    all_items,
    key=lambda item: item["json"].get("score", 0),
    reverse=True
)
top_five = sorted_items[:5]

return [{"json": item["json"]} for item in top_five]
```

### Example 5: Group By Category

```python
all_items = _input.all()

# Group items by category
grouped = {}
for item in all_items:
    category = item["json"].get("category", "Uncategorized")

    if category not in grouped:
        grouped[category] = []

    grouped[category].append(item["json"])

# Convert to list format
return [
    {
        "json": {
            "category": category,
            "items": items,
            "count": len(items)
        }
    }
    for category, items in grouped.items()
]
```

### Example 6: Deduplicate by ID

```python
all_items = _input.all()

# Remove duplicates by ID
seen = set()
unique = []

for item in all_items:
    item_id = item["json"].get("id")

    if item_id and item_id not in seen:
        seen.add(item_id)
        unique.append(item)

return unique
```

---

## Pattern 2: _input.first() - Get First Item

**Usage**: Very common for single-item operations

**When to use:**
- Previous node returns single object
- Working with API responses
- Getting initial/first data point

### Basic Usage

```python
# Get first item from previous node
first_item = _input.first()

# Access the JSON data
data = first_item["json"]

print(f"First item: {data}")

return [{"json": data}]
```

### Example 1: Process Single API Response

```python
# Get API response (typically single object)
response = _input.first()["json"]

# Extract what you need
return [{
    "json": {
        "user_id": response.get("data", {}).get("user", {}).get("id"),
        "user_name": response.get("data", {}).get("user", {}).get("name"),
        "status": response.get("status"),
        "fetched_at": datetime.now().isoformat()
    }
}]
```

### Example 2: Transform Single Object

```python
data = _input.first()["json"]

# Transform structure
return [{
    "json": {
        "id": data.get("id"),
        "contact": {
            "email": data.get("email"),
            "phone": data.get("phone")
        },
        "address": {
            "street": data.get("street"),
            "city": data.get("city"),
            "zip": data.get("zip")
        }
    }
}]
```

### Example 3: Validate Single Item

```python
item = _input.first()["json"]

# Validation logic
is_valid = bool(item.get("email") and "@" in item.get("email", ""))

return [{
    "json": {
        **item,
        "valid": is_valid,
        "validated_at": datetime.now().isoformat()
    }
}]
```

### Example 4: Extract Nested Data

```python
response = _input.first()["json"]

# Navigate nested structure
users = response.get("data", {}).get("users", [])

return [
    {
        "json": {
            "id": user.get("id"),
            "name": user.get("profile", {}).get("name", "Unknown"),
            "email": user.get("contact", {}).get("email", "no-email")
        }
    }
    for user in users
]
```

---

## Pattern 3: _input.item - Current Item (Each Item Mode)

**Usage**: Common in "Run Once for Each Item" mode

**When to use:**
- Mode is set to "Run Once for Each Item"
- Need to process items independently
- Per-item API calls or validations

**IMPORTANT**: Only use in "Each Item" mode. Will be undefined in "All Items" mode.

### Basic Usage

```python
# In "Run Once for Each Item" mode
current_item = _input.item
data = current_item["json"]

print(f"Processing item: {data.get('id')}")

return [{
    "json": {
        **data,
        "processed": True
    }
}]
```

### Example 1: Add Processing Metadata

```python
item = _input.item

return [{
    "json": {
        **item["json"],
        "processed": True,
        "processed_at": datetime.now().isoformat(),
        "processing_duration": random.random() * 1000  # Simulated
    }
}]
```

### Example 2: Per-Item Validation

```python
item = _input.item
data = item["json"]

# Validate this specific item
errors = []

if not data.get("email"):
    errors.append("Email required")
if not data.get("name"):
    errors.append("Name required")
if data.get("age") and data["age"] < 18:
    errors.append("Must be 18+")

return [{
    "json": {
        **data,
        "valid": len(errors) == 0,
        "errors": errors if errors else None
    }
}]
```

### Example 3: Conditional Processing

```python
item = _input.item
data = item["json"]

# Process based on item type
if data.get("type") == "premium":
    return [{
        "json": {
            **data,
            "discount": 0.20,
            "tier": "premium"
        }
    }]
else:
    return [{
        "json": {
            **data,
            "discount": 0.05,
            "tier": "standard"
        }
    }]
```

---

## Pattern 4: _node - Reference Other Nodes

**Usage**: Less common, but powerful for specific scenarios

**When to use:**
- Need data from specific named node
- Combining data from multiple nodes

### Basic Usage

```python
# Get output from specific node
webhook_data = _node["Webhook"]["json"]
api_data = _node["HTTP Request"]["json"]

return [{
    "json": {
        "from_webhook": webhook_data,
        "from_api": api_data
    }
}]
```

### Example 1: Combine Multiple Sources

```python
# Reference multiple nodes
webhook = _node["Webhook"]["json"]
database = _node["Postgres"]["json"]
api = _node["HTTP Request"]["json"]

return [{
    "json": {
        "combined": {
            "webhook": webhook.get("body", {}),
            "db_records": len(database) if isinstance(database, list) else 1,
            "api_response": api.get("status")
        },
        "processed_at": datetime.now().isoformat()
    }
}]
```

### Example 2: Compare Across Nodes

```python
old_data = _node["Get Old Data"]["json"]
new_data = _node["Get New Data"]["json"]

# Simple comparison
changes = {
    "added": [n for n in new_data if n.get("id") not in [o.get("id") for o in old_data]],
    "removed": [o for o in old_data if o.get("id") not in [n.get("id") for n in new_data]]
}

return [{
    "json": {
        "changes": changes,
        "summary": {
            "added": len(changes["added"]),
            "removed": len(changes["removed"])
        }
    }
}]
```

---

## Critical: Webhook Data Structure

**MOST COMMON MISTAKE**: Forgetting webhook data is nested under `["body"]`

### The Problem

Webhook node wraps all incoming data under a `"body"` property.

### Structure

```python
# Webhook node output structure:
{
    "headers": {
        "content-type": "application/json",
        "user-agent": "..."
    },
    "params": {},
    "query": {},
    "body": {
        # ← YOUR DATA IS HERE
        "name": "Alice",
        "email": "alice@example.com",
        "message": "Hello!"
    }
}
```

### Wrong vs Right

```python
# ❌ WRONG: Trying to access directly
name = _json["name"]  # KeyError!
email = _json["email"]  # KeyError!

# ✅ CORRECT: Access via ["body"]
name = _json["body"]["name"]  # "Alice"
email = _json["body"]["email"]  # "alice@example.com"

# ✅ SAFER: Use .get() for safe access
webhook_data = _json.get("body", {})
name = webhook_data.get("name")  # None if missing
email = webhook_data.get("email", "no-email")  # Default value
```

### Example: Full Webhook Processing

```python
# Get webhook data from previous node
webhook_output = _input.first()["json"]

# Access the actual payload
payload = webhook_output.get("body", {})

# Access headers if needed
content_type = webhook_output.get("headers", {}).get("content-type")

# Access query parameters if needed
api_key = webhook_output.get("query", {}).get("api_key")

# Process the actual data
return [{
    "json": {
        # Data from webhook body
        "user_name": payload.get("name"),
        "user_email": payload.get("email"),
        "message": payload.get("message"),

        # Metadata
        "received_at": datetime.now().isoformat(),
        "content_type": content_type,
        "authenticated": bool(api_key)
    }
}]
```

### POST Data, Query Params, and Headers

```python
webhook = _input.first()["json"]

return [{
    "json": {
        # POST body data
        "form_data": webhook.get("body", {}),

        # Query parameters (?key=value)
        "query_params": webhook.get("query", {}),

        # HTTP headers
        "user_agent": webhook.get("headers", {}).get("user-agent"),
        "content_type": webhook.get("headers", {}).get("content-type"),

        # Request metadata
        "method": webhook.get("method"),  # POST, GET, etc.
        "url": webhook.get("url")
    }
}]
```

---

## Choosing the Right Pattern

### Decision Tree

```
Do you need ALL items from previous node?
├─ YES → Use _input.all()
│
└─ NO → Do you need just the FIRST item?
    ├─ YES → Use _input.first()
    │
    └─ NO → Are you in "Each Item" mode?
        ├─ YES → Use _input.item
        │
        └─ NO → Do you need specific node data?
            ├─ YES → Use _node["NodeName"]
            └─ NO → Use _input.first() (default)
```

### Quick Reference Table

| Scenario | Use This | Example |
|----------|----------|---------|
| Sum all amounts | `_input.all()` | `sum(i["json"].get("amount", 0) for i in items)` |
| Get API response | `_input.first()` | `_input.first()["json"].get("data")` |
| Process each independently | `_input.item` | `_input.item["json"]` (Each Item mode) |
| Combine two nodes | `_node["Name"]` | `_node["API"]["json"]` |
| Filter list | `_input.all()` | `[i for i in items if i["json"].get("active")]` |
| Transform single object | `_input.first()` | `{**_input.first()["json"], "new": True}` |
| Webhook data | `_input.first()` | `_input.first()["json"]["body"]` |

---

## Common Mistakes

### Mistake 1: Using _json Without Context

```python
# ❌ RISKY: _json is ambiguous
value = _json["field"]

# ✅ CLEAR: Be explicit
value = _input.first()["json"]["field"]
```

### Mistake 2: Forgetting ["json"] Property

```python
# ❌ WRONG: Trying to access fields on item dictionary
items = _input.all()
names = [item["name"] for item in items]  # KeyError!

# ✅ CORRECT: Access via ["json"]
names = [item["json"]["name"] for item in items]
```

### Mistake 3: Using _input.item in All Items Mode

```python
# ❌ WRONG: _input.item is None in "All Items" mode
data = _input.item["json"]  # AttributeError!

# ✅ CORRECT: Use appropriate method
data = _input.first()["json"]  # Or _input.all()
```

### Mistake 4: Not Handling Empty Lists

```python
# ❌ WRONG: Crashes if no items
first = _input.all()[0]["json"]  # IndexError!

# ✅ CORRECT: Check length first
items = _input.all()
if items:
    first = items[0]["json"]
else:
    return []

# ✅ ALSO CORRECT: Use _input.first()
first = _input.first()["json"]  # Built-in safety
```

### Mistake 5: Direct Dictionary Access (KeyError)

```python
# ❌ RISKY: Crashes if key missing
value = item["json"]["field"]  # KeyError!

# ✅ SAFE: Use .get()
value = item["json"].get("field", "default")
```

---

## Advanced Patterns

### Pattern: Safe Nested Access

```python
# Deep nested access with .get()
value = (
    _input.first()["json"]
    .get("level1", {})
    .get("level2", {})
    .get("level3", "default")
)
```

### Pattern: List Comprehension with Filtering

```python
items = _input.all()

# Filter and transform in one step
result = [
    {
        "json": {
            "id": item["json"]["id"],
            "name": item["json"]["name"].upper()
        }
    }
    for item in items
    if item["json"].get("active") and item["json"].get("verified")
]

return result
```

### Pattern: Dictionary Comprehension

```python
items = _input.all()

# Create lookup dictionary
lookup = {
    item["json"]["id"]: item["json"]
    for item in items
    if "id" in item["json"]
}

return [{"json": lookup}]
```

---

## Summary

**Most Common Patterns**:
1. `_input.all()` - Process multiple items, batch operations
2. `_input.first()` - Single item, API responses
3. `_input.item` - Each Item mode processing

**Critical Rule**:
- Webhook data is under `["body"]` property

**Best Practice**:
- Use `.get()` for dictionary access to avoid KeyError
- Always check for empty lists
- Be explicit: Use `_input.first()["json"]["field"]` instead of `_json["field"]`

**See Also**:
- [SKILL.md](SKILL.md) - Overview and quick start
- [COMMON_PATTERNS.md](COMMON_PATTERNS.md) - Python-specific patterns
- [ERROR_PATTERNS.md](ERROR_PATTERNS.md) - Avoid common mistakes
