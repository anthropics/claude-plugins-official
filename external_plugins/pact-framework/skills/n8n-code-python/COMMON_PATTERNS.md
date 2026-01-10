# Common Patterns - Python Code Node

Production-tested Python patterns for n8n Code nodes.

---

## ⚠️ Important: JavaScript First

**Use JavaScript for 95% of use cases.**

Python in n8n has **NO external libraries** (no requests, pandas, numpy).

Only use Python when:
- You have complex Python-specific logic
- You need Python's standard library features
- You're more comfortable with Python than JavaScript

For most workflows, **JavaScript is the better choice**.

---

## Pattern Overview

These 10 patterns cover common n8n Code node scenarios using Python:

1. **Multi-Source Data Aggregation** - Combine data from multiple nodes
2. **Regex-Based Filtering** - Filter items using pattern matching
3. **Markdown to Structured Data** - Parse markdown into structured format
4. **JSON Object Comparison** - Compare two JSON objects for changes
5. **CRM Data Transformation** - Transform CRM data to standard format
6. **Release Notes Processing** - Parse and categorize release notes
7. **Array Transformation** - Reshape arrays and extract fields
8. **Dictionary Lookup** - Create and use lookup dictionaries
9. **Top N Filtering** - Get top items by score/value
10. **String Aggregation** - Aggregate strings with formatting

---

## Pattern 1: Multi-Source Data Aggregation

**Use case**: Combine data from multiple sources (APIs, webhooks, databases).

**Scenario**: Aggregate news articles from multiple sources.

### Implementation

```python
from datetime import datetime

all_items = _input.all()
processed_articles = []

for item in all_items:
    source_name = item["json"].get("name", "Unknown")
    source_data = item["json"]

    # Process Hacker News source
    if source_name == "Hacker News" and source_data.get("hits"):
        for hit in source_data["hits"]:
            processed_articles.append({
                "title": hit.get("title", "No title"),
                "url": hit.get("url", ""),
                "summary": hit.get("story_text") or "No summary",
                "source": "Hacker News",
                "score": hit.get("points", 0),
                "fetched_at": datetime.now().isoformat()
            })

    # Process Reddit source
    elif source_name == "Reddit" and source_data.get("data"):
        for post in source_data["data"].get("children", []):
            post_data = post.get("data", {})
            processed_articles.append({
                "title": post_data.get("title", "No title"),
                "url": post_data.get("url", ""),
                "summary": post_data.get("selftext", "")[:200],
                "source": "Reddit",
                "score": post_data.get("score", 0),
                "fetched_at": datetime.now().isoformat()
            })

# Sort by score descending
processed_articles.sort(key=lambda x: x["score"], reverse=True)

# Return as n8n items
return [{"json": article} for article in processed_articles]
```

### Key Techniques

- Process multiple data sources in one loop
- Normalize different data structures
- Use datetime for timestamps
- Sort by criteria
- Return properly formatted items

---

## Pattern 2: Regex-Based Filtering

**Use case**: Filter items based on pattern matching in text fields.

**Scenario**: Filter support tickets by priority keywords.

### Implementation

```python
import re

all_items = _input.all()
priority_tickets = []

# High priority keywords pattern
high_priority_pattern = re.compile(
    r'\b(urgent|critical|emergency|asap|down|outage|broken)\b',
    re.IGNORECASE
)

for item in all_items:
    ticket = item["json"]

    # Check subject and description
    subject = ticket.get("subject", "")
    description = ticket.get("description", "")
    combined_text = f"{subject} {description}"

    # Find matches
    matches = high_priority_pattern.findall(combined_text)

    if matches:
        priority_tickets.append({
            "json": {
                **ticket,
                "priority": "high",
                "matched_keywords": list(set(matches)),
                "keyword_count": len(matches)
            }
        })
    else:
        priority_tickets.append({
            "json": {
                **ticket,
                "priority": "normal",
                "matched_keywords": [],
                "keyword_count": 0
            }
        })

# Sort by keyword count (most urgent first)
priority_tickets.sort(key=lambda x: x["json"]["keyword_count"], reverse=True)

return priority_tickets
```

### Key Techniques

- Use re.compile() for reusable patterns
- re.IGNORECASE for case-insensitive matching
- Combine multiple text fields for searching
- Extract and deduplicate matches
- Sort by priority indicators

---

## Pattern 3: Markdown to Structured Data

**Use case**: Parse markdown text into structured data.

**Scenario**: Extract tasks from markdown checklist.

### Implementation

```python
import re

markdown_text = _input.first()["json"]["body"].get("markdown", "")

# Parse markdown checklist
tasks = []
lines = markdown_text.split("\n")

for line in lines:
    # Match: - [ ] Task or - [x] Task
    match = re.match(r'^\s*-\s*\[([ x])\]\s*(.+)$', line, re.IGNORECASE)

    if match:
        checked = match.group(1).lower() == 'x'
        task_text = match.group(2).strip()

        # Extract priority if present (e.g., [P1], [HIGH])
        priority_match = re.search(r'\[(P\d|HIGH|MEDIUM|LOW)\]', task_text, re.IGNORECASE)
        priority = priority_match.group(1).upper() if priority_match else "NORMAL"

        # Remove priority tag from text
        clean_text = re.sub(r'\[(P\d|HIGH|MEDIUM|LOW)\]', '', task_text, flags=re.IGNORECASE).strip()

        tasks.append({
            "text": clean_text,
            "completed": checked,
            "priority": priority,
            "original_line": line.strip()
        })

return [{
    "json": {
        "tasks": tasks,
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t["completed"]),
        "pending": sum(1 for t in tasks if not t["completed"])
    }
}]
```

### Key Techniques

- Line-by-line parsing
- Multiple regex patterns for extraction
- Extract metadata from text
- Calculate summary statistics
- Return structured data

---

## Pattern 4: JSON Object Comparison

**Use case**: Compare two JSON objects to find differences.

**Scenario**: Compare old and new user profile data.

### Implementation

```python
import json

all_items = _input.all()

# Assume first item is old data, second is new data
old_data = all_items[0]["json"] if len(all_items) > 0 else {}
new_data = all_items[1]["json"] if len(all_items) > 1 else {}

changes = {
    "added": {},
    "removed": {},
    "modified": {},
    "unchanged": {}
}

# Find all unique keys
all_keys = set(old_data.keys()) | set(new_data.keys())

for key in all_keys:
    old_value = old_data.get(key)
    new_value = new_data.get(key)

    if key not in old_data:
        # Added field
        changes["added"][key] = new_value
    elif key not in new_data:
        # Removed field
        changes["removed"][key] = old_value
    elif old_value != new_value:
        # Modified field
        changes["modified"][key] = {
            "old": old_value,
            "new": new_value
        }
    else:
        # Unchanged field
        changes["unchanged"][key] = old_value

return [{
    "json": {
        "changes": changes,
        "summary": {
            "added_count": len(changes["added"]),
            "removed_count": len(changes["removed"]),
            "modified_count": len(changes["modified"]),
            "unchanged_count": len(changes["unchanged"]),
            "has_changes": len(changes["added"]) > 0 or len(changes["removed"]) > 0 or len(changes["modified"]) > 0
        }
    }
}]
```

### Key Techniques

- Set operations for key comparison
- Dictionary .get() for safe access
- Categorize changes by type
- Create summary statistics
- Return detailed comparison

---

## Pattern 5: CRM Data Transformation

**Use case**: Transform CRM data to standard format.

**Scenario**: Normalize data from different CRM systems.

### Implementation

```python
from datetime import datetime
import re

all_items = _input.all()
normalized_contacts = []

for item in all_items:
    raw_contact = item["json"]
    source = raw_contact.get("source", "unknown")

    # Normalize email
    email = raw_contact.get("email", "").lower().strip()

    # Normalize phone (remove non-digits)
    phone_raw = raw_contact.get("phone", "")
    phone = re.sub(r'\D', '', phone_raw)

    # Parse name
    if "full_name" in raw_contact:
        name_parts = raw_contact["full_name"].split(" ", 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
    else:
        first_name = raw_contact.get("first_name", "")
        last_name = raw_contact.get("last_name", "")

    # Normalize status
    status_raw = raw_contact.get("status", "").lower()
    status = "active" if status_raw in ["active", "enabled", "true", "1"] else "inactive"

    # Create normalized contact
    normalized_contacts.append({
        "json": {
            "id": raw_contact.get("id", ""),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "full_name": f"{first_name} {last_name}".strip(),
            "email": email,
            "phone": phone,
            "status": status,
            "source": source,
            "normalized_at": datetime.now().isoformat(),
            "original_data": raw_contact
        }
    })

return normalized_contacts
```

### Key Techniques

- Multiple field name variations handling
- String cleaning and normalization
- Regex for phone number cleaning
- Name parsing logic
- Status normalization
- Preserve original data

---

## Pattern 6: Release Notes Processing

**Use case**: Parse release notes and categorize changes.

**Scenario**: Extract features, fixes, and breaking changes from release notes.

### Implementation

```python
import re

release_notes = _input.first()["json"]["body"].get("notes", "")

categories = {
    "features": [],
    "fixes": [],
    "breaking": [],
    "other": []
}

# Split into lines
lines = release_notes.split("\n")

for line in lines:
    line = line.strip()

    # Skip empty lines and headers
    if not line or line.startswith("#"):
        continue

    # Remove bullet points
    clean_line = re.sub(r'^[\*\-\+]\s*', '', line)

    # Categorize
    if re.search(r'\b(feature|add|new)\b', clean_line, re.IGNORECASE):
        categories["features"].append(clean_line)
    elif re.search(r'\b(fix|bug|patch|resolve)\b', clean_line, re.IGNORECASE):
        categories["fixes"].append(clean_line)
    elif re.search(r'\b(breaking|deprecated|remove)\b', clean_line, re.IGNORECASE):
        categories["breaking"].append(clean_line)
    else:
        categories["other"].append(clean_line)

return [{
    "json": {
        "categories": categories,
        "summary": {
            "features": len(categories["features"]),
            "fixes": len(categories["fixes"]),
            "breaking": len(categories["breaking"]),
            "other": len(categories["other"]),
            "total": sum(len(v) for v in categories.values())
        }
    }
}]
```

### Key Techniques

- Line-by-line parsing
- Pattern-based categorization
- Bullet point removal
- Skip headers and empty lines
- Summary statistics

---

## Pattern 7: Array Transformation

**Use case**: Reshape arrays and extract specific fields.

**Scenario**: Transform user data array to extract specific fields.

### Implementation

```python
all_items = _input.all()

# Extract and transform
transformed = []

for item in all_items:
    user = item["json"]

    # Extract nested fields
    profile = user.get("profile", {})
    settings = user.get("settings", {})

    transformed.append({
        "json": {
            "user_id": user.get("id"),
            "email": user.get("email"),
            "name": profile.get("name", "Unknown"),
            "avatar": profile.get("avatar_url"),
            "bio": profile.get("bio", "")[:100],  # Truncate to 100 chars
            "notifications_enabled": settings.get("notifications", True),
            "theme": settings.get("theme", "light"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login_at")
        }
    })

return transformed
```

### Key Techniques

- Field extraction from nested objects
- Default values with .get()
- String truncation
- Flattening nested structures

---

## Pattern 8: Dictionary Lookup

**Use case**: Create lookup dictionary for fast data access.

**Scenario**: Look up user details by ID.

### Implementation

```python
all_items = _input.all()

# Build lookup dictionary
users_by_id = {}

for item in all_items:
    user = item["json"]
    user_id = user.get("id")

    if user_id:
        users_by_id[user_id] = {
            "name": user.get("name"),
            "email": user.get("email"),
            "status": user.get("status")
        }

# Example: Look up specific users
lookup_ids = [1, 3, 5]
looked_up = []

for user_id in lookup_ids:
    if user_id in users_by_id:
        looked_up.append({
            "json": {
                "id": user_id,
                **users_by_id[user_id],
                "found": True
            }
        })
    else:
        looked_up.append({
            "json": {
                "id": user_id,
                "found": False
            }
        })

return looked_up
```

### Key Techniques

- Dictionary comprehension alternative
- O(1) lookup time
- Handle missing keys gracefully
- Preserve lookup order

---

## Pattern 9: Top N Filtering

**Use case**: Get top items by score or value.

**Scenario**: Get top 10 products by sales.

### Implementation

```python
all_items = _input.all()

# Extract products with sales
products = []

for item in all_items:
    product = item["json"]
    products.append({
        "id": product.get("id"),
        "name": product.get("name"),
        "sales": product.get("sales", 0),
        "revenue": product.get("revenue", 0.0),
        "category": product.get("category")
    })

# Sort by sales descending
products.sort(key=lambda p: p["sales"], reverse=True)

# Get top 10
top_10 = products[:10]

return [
    {
        "json": {
            **product,
            "rank": index + 1
        }
    }
    for index, product in enumerate(top_10)
]
```

### Key Techniques

- List sorting with custom key
- Slicing for top N
- Add ranking information
- Enumerate for index

---

## Pattern 10: String Aggregation

**Use case**: Aggregate strings with formatting.

**Scenario**: Create summary text from multiple items.

### Implementation

```python
all_items = _input.all()

# Collect messages
messages = []

for item in all_items:
    data = item["json"]

    user = data.get("user", "Unknown")
    message = data.get("message", "")
    timestamp = data.get("timestamp", "")

    # Format each message
    formatted = f"[{timestamp}] {user}: {message}"
    messages.append(formatted)

# Join with newlines
summary = "\n".join(messages)

# Create statistics
total_length = sum(len(msg) for msg in messages)
average_length = total_length / len(messages) if messages else 0

return [{
    "json": {
        "summary": summary,
        "message_count": len(messages),
        "total_characters": total_length,
        "average_length": round(average_length, 2)
    }
}]
```

### Key Techniques

- String formatting with f-strings
- Join lists with separator
- Calculate string statistics
- Handle empty lists

---

## Pattern Comparison: Python vs JavaScript

### Data Access

```python
# Python
all_items = _input.all()
first_item = _input.first()
current = _input.item
webhook_data = _json["body"]

# JavaScript
const allItems = $input.all();
const firstItem = $input.first();
const current = $input.item;
const webhookData = $json.body;
```

### Dictionary/Object Access

```python
# Python - Dictionary key access
name = user["name"]           # May raise KeyError
name = user.get("name", "?")  # Safe with default

# JavaScript - Object property access
const name = user.name;              // May be undefined
const name = user.name || "?";       // Safe with default
```

### Array Operations

```python
# Python - List comprehension
filtered = [item for item in items if item["active"]]

# JavaScript - Array methods
const filtered = items.filter(item => item.active);
```

### Sorting

```python
# Python
items.sort(key=lambda x: x["score"], reverse=True)

# JavaScript
items.sort((a, b) => b.score - a.score);
```

---

## Best Practices

### 1. Use .get() for Safe Access

```python
# ✅ SAFE: Use .get() with defaults
name = user.get("name", "Unknown")
email = user.get("email", "no-email@example.com")

# ❌ RISKY: Direct key access
name = user["name"]  # KeyError if missing!
```

### 2. Handle Empty Lists

```python
# ✅ SAFE: Check before processing
items = _input.all()
if items:
    first = items[0]
else:
    return [{"json": {"error": "No items"}}]

# ❌ RISKY: Assume items exist
first = items[0]  # IndexError if empty!
```

### 3. Use List Comprehensions

```python
# ✅ PYTHONIC: List comprehension
active = [item for item in items if item["json"].get("active")]

# ❌ VERBOSE: Traditional loop
active = []
for item in items:
    if item["json"].get("active"):
        active.append(item)
```

### 4. Return Proper Format

```python
# ✅ CORRECT: Array of objects with "json" key
return [{"json": {"field": "value"}}]

# ❌ WRONG: Just the data
return {"field": "value"}

# ❌ WRONG: Array without "json" wrapper
return [{"field": "value"}]
```

### 5. Use Standard Library

```python
# ✅ GOOD: Use standard library
import statistics
average = statistics.mean(numbers)

# ✅ ALSO GOOD: Built-in functions
average = sum(numbers) / len(numbers) if numbers else 0

# ❌ CAN'T DO: External libraries
import numpy as np  # ModuleNotFoundError!
```

---

## When to Use Each Pattern

| Pattern | When to Use |
|---------|-------------|
| Multi-Source Aggregation | Combining data from different nodes/sources |
| Regex Filtering | Text pattern matching, validation, extraction |
| Markdown Parsing | Processing formatted text into structured data |
| JSON Comparison | Detecting changes between objects |
| CRM Transformation | Normalizing data from different systems |
| Release Notes | Categorizing text by keywords |
| Array Transformation | Reshaping data, extracting fields |
| Dictionary Lookup | Fast ID-based lookups |
| Top N Filtering | Getting best/worst items by criteria |
| String Aggregation | Creating formatted text summaries |

---

## Summary

**Key Takeaways**:
- Use `.get()` for safe dictionary access
- List comprehensions are pythonic and efficient
- Handle empty lists/None values
- Use standard library (json, datetime, re)
- Return proper n8n format: `[{"json": {...}}]`

**Remember**:
- JavaScript is recommended for 95% of use cases
- Python has NO external libraries
- Use n8n nodes for complex operations
- Code node is for data transformation, not API calls

**See Also**:
- [SKILL.md](SKILL.md) - Python Code overview
- [DATA_ACCESS.md](DATA_ACCESS.md) - Data access patterns
- [STANDARD_LIBRARY.md](STANDARD_LIBRARY.md) - Available modules
- [ERROR_PATTERNS.md](ERROR_PATTERNS.md) - Avoid common mistakes
