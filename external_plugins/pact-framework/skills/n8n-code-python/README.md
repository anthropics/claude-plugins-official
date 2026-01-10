# n8n Code Python Skill

Expert guidance for writing Python code in n8n Code nodes.

---

## ⚠️ Important: JavaScript First

**Use JavaScript for 95% of use cases.**

Python in n8n has **NO external libraries** (no requests, pandas, numpy).

**When to use Python**:
- You have complex Python-specific logic
- You need Python's standard library features
- You're more comfortable with Python than JavaScript

**When to use JavaScript** (recommended):
- HTTP requests ($helpers.httpRequest available)
- Date/time operations (Luxon library included)
- Most data transformations
- When in doubt

---

## What This Skill Teaches

### Core Concepts

1. **Critical Limitation**: No external libraries
2. **Data Access**: `_input.all()`, `_input.first()`, `_input.item`
3. **Webhook Gotcha**: Data is under `_json["body"]`
4. **Return Format**: Must return `[{"json": {...}}]`
5. **Standard Library**: json, datetime, re, base64, hashlib, etc.

### Top 5 Error Prevention

This skill emphasizes **error prevention**:

1. **ModuleNotFoundError** (trying to import external libraries)
2. **Empty code / missing return**
3. **KeyError** (dictionary access without .get())
4. **IndexError** (list access without bounds checking)
5. **Incorrect return format**

These 5 errors are the most common in Python Code nodes.

---

## Skill Activation

This skill activates when you:
- Write Python in Code nodes
- Ask about Python limitations
- Need to know available standard library
- Troubleshoot Python Code node errors
- Work with Python data structures

**Example queries**:
- "Can I use pandas in Python Code node?"
- "How do I access webhook data in Python?"
- "What Python libraries are available?"
- "Write Python code to process JSON"
- "Why is requests module not found?"

---

## File Structure

### SKILL.md (719 lines)
**Quick start** and overview
- When to use Python vs JavaScript
- Critical limitation (no external libraries)
- Mode selection (All Items vs Each Item)
- Data access overview
- Return format requirements
- Standard library overview

### DATA_ACCESS.md (703 lines)
**Complete data access patterns**
- `_input.all()` - Process all items
- `_input.first()` - Get first item
- `_input.item` - Current item (Each Item mode)
- `_node["Name"]` - Reference other nodes
- Webhook body structure (critical gotcha!)
- Pattern selection guide

### STANDARD_LIBRARY.md (850 lines)
**Available Python modules**
- json - JSON parsing
- datetime - Date/time operations
- re - Regular expressions
- base64 - Encoding/decoding
- hashlib - Hashing
- urllib.parse - URL operations
- math, random, statistics
- What's NOT available (requests, pandas, numpy)
- Workarounds for missing libraries

### COMMON_PATTERNS.md (895 lines)
**10 production-tested patterns**
1. Multi-source data aggregation
2. Regex-based filtering
3. Markdown to structured data
4. JSON object comparison
5. CRM data transformation
6. Release notes processing
7. Array transformation
8. Dictionary lookup
9. Top N filtering
10. String aggregation

### ERROR_PATTERNS.md (730 lines)
**Top 5 errors with solutions**
1. ModuleNotFoundError (external libraries)
2. Empty code / missing return
3. KeyError (dictionary access)
4. IndexError (list access)
5. Incorrect return format
- Error prevention checklist
- Quick fix reference
- Testing patterns

---

## Integration with Other Skills

This skill works with:

### n8n Expression Syntax
- Python uses code syntax, not {{}} expressions
- Data access patterns differ ($ vs _)

### n8n MCP Tools Expert
- Use MCP tools to validate Code node configurations
- Check node setup with `get_node_essentials`

### n8n Workflow Patterns
- Code nodes fit into larger workflow patterns
- Often used after HTTP Request or Webhook nodes

### n8n Code JavaScript
- Compare Python vs JavaScript approaches
- Understand when to use which language
- JavaScript recommended for 95% of cases

### n8n Node Configuration
- Configure Code node mode (All Items vs Each Item)
- Set up proper connections

---

## Success Metrics

After using this skill, you should be able to:

- [ ] **Know the limitation**: Python has NO external libraries
- [ ] **Choose language**: JavaScript for 95% of cases, Python when needed
- [ ] **Access data**: Use `_input.all()`, `_input.first()`, `_input.item`
- [ ] **Handle webhooks**: Access data via `_json["body"]`
- [ ] **Return properly**: Always return `[{"json": {...}}]`
- [ ] **Avoid KeyError**: Use `.get()` for dictionary access
- [ ] **Use standard library**: Know what's available (json, datetime, re, etc.)
- [ ] **Prevent errors**: Avoid top 5 common errors
- [ ] **Choose alternatives**: Use n8n nodes when libraries needed
- [ ] **Write production code**: Use proven patterns

---

## Quick Reference

### Data Access
```python
all_items = _input.all()
first_item = _input.first()
current_item = _input.item  # Each Item mode only
other_node = _node["NodeName"]
```

### Webhook Data
```python
webhook = _input.first()["json"]
body = webhook.get("body", {})
name = body.get("name")
```

### Safe Dictionary Access
```python
# ✅ Use .get() with defaults
value = data.get("field", "default")

# ❌ Risky - may raise KeyError
value = data["field"]
```

### Return Format
```python
# ✅ Correct format
return [{"json": {"result": "success"}}]

# ❌ Wrong - plain dict
return {"result": "success"}
```

### Standard Library
```python
# ✅ Available
import json
import datetime
import re
import base64
import hashlib

# ❌ NOT available
import requests  # ModuleNotFoundError!
import pandas    # ModuleNotFoundError!
import numpy     # ModuleNotFoundError!
```

---

## Common Use Cases

### Use Case 1: Process Webhook Data
```python
webhook = _input.first()["json"]
body = webhook.get("body", {})

return [{
    "json": {
        "name": body.get("name"),
        "email": body.get("email"),
        "processed": True
    }
}]
```

### Use Case 2: Filter and Transform
```python
all_items = _input.all()

active = [
    {"json": {**item["json"], "filtered": True}}
    for item in all_items
    if item["json"].get("status") == "active"
]

return active
```

### Use Case 3: Aggregate Statistics
```python
import statistics

all_items = _input.all()
amounts = [item["json"].get("amount", 0) for item in all_items]

return [{
    "json": {
        "total": sum(amounts),
        "average": statistics.mean(amounts) if amounts else 0,
        "count": len(amounts)
    }
}]
```

### Use Case 4: Parse JSON String
```python
import json

data = _input.first()["json"]["body"]
json_string = data.get("payload", "{}")

try:
    parsed = json.loads(json_string)
    return [{"json": parsed}]
except json.JSONDecodeError:
    return [{"json": {"error": "Invalid JSON"}}]
```

---

## Limitations and Workarounds

### Limitation 1: No HTTP Requests Library
**Problem**: No `requests` library
**Workaround**: Use HTTP Request node or JavaScript

### Limitation 2: No Data Analysis Library
**Problem**: No `pandas` or `numpy`
**Workaround**: Use list comprehensions and standard library

### Limitation 3: No Database Drivers
**Problem**: No `psycopg2`, `pymongo`, etc.
**Workaround**: Use n8n database nodes (Postgres, MySQL, MongoDB)

### Limitation 4: No Web Scraping
**Problem**: No `beautifulsoup4` or `selenium`
**Workaround**: Use HTML Extract node

---

## Best Practices

1. **Use JavaScript for most cases** (95% recommendation)
2. **Use .get() for dictionaries** (avoid KeyError)
3. **Check lengths before indexing** (avoid IndexError)
4. **Always return proper format**: `[{"json": {...}}]`
5. **Access webhook data via ["body"]**
6. **Use standard library only** (no external imports)
7. **Handle empty input** (check `if items:`)
8. **Test both modes** (All Items and Each Item)

---

## When Python is the Right Choice

Use Python when:
- Complex text processing (re module)
- Mathematical calculations (math, statistics)
- Date/time manipulation (datetime)
- Cryptographic operations (hashlib)
- You have existing Python logic to reuse
- Team is more comfortable with Python

Use JavaScript instead when:
- Making HTTP requests
- Working with dates (Luxon included)
- Most data transformations
- When in doubt

---

## Learning Path

**Beginner**:
1. Read SKILL.md - Understand the limitation
2. Try DATA_ACCESS.md examples - Learn `_input` patterns
3. Practice safe dictionary access with `.get()`

**Intermediate**:
4. Study STANDARD_LIBRARY.md - Know what's available
5. Try COMMON_PATTERNS.md examples - Use proven patterns
6. Learn ERROR_PATTERNS.md - Avoid common mistakes

**Advanced**:
7. Combine multiple patterns
8. Use standard library effectively
9. Know when to switch to JavaScript
10. Write production-ready code

---

## Support

**Questions?**
- Check ERROR_PATTERNS.md for common issues
- Review COMMON_PATTERNS.md for examples
- Consider using JavaScript instead

**Related Skills**:
- n8n Code JavaScript - Alternative (recommended for 95% of cases)
- n8n Expression Syntax - For {{}} expressions in other nodes
- n8n Workflow Patterns - Bigger picture workflow design

---

## Version

**Version**: 1.0.0
**Status**: Production Ready
**Compatibility**: n8n Code node (Python mode)

---

## Credits

Part of the n8n-skills project.

**Conceived by Romuald Członkowski**
- Website: [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)
- Part of [n8n-mcp project](https://github.com/czlonkowski/n8n-mcp)

---

**Remember**: JavaScript is recommended for 95% of use cases. Use Python only when you specifically need Python's standard library features.
