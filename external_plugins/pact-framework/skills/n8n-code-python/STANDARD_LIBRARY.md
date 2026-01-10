# Standard Library Reference - Python Code Node

Complete guide to available Python standard library modules in n8n Code nodes.

---

## ⚠️ Critical Limitation

**NO EXTERNAL LIBRARIES AVAILABLE**

Python Code nodes in n8n have **ONLY** the Python standard library. No pip packages.

```python
# ❌ NOT AVAILABLE - Will cause ModuleNotFoundError
import requests      # No HTTP library!
import pandas        # No data analysis!
import numpy         # No numerical computing!
import bs4          # No web scraping!
import selenium     # No browser automation!
import psycopg2     # No database drivers!
import pymongo      # No MongoDB!
import sqlalchemy   # No ORMs!

# ✅ AVAILABLE - Standard library only
import json
import datetime
import re
import base64
import hashlib
import urllib.parse
import urllib.request
import math
import random
import statistics
```

**Recommendation**: Use **JavaScript** for 95% of use cases. JavaScript has more capabilities in n8n.

---

## Available Modules

### Priority 1: Most Useful (Use These)

1. **json** - JSON parsing and generation
2. **datetime** - Date and time operations
3. **re** - Regular expressions
4. **base64** - Base64 encoding/decoding
5. **hashlib** - Hashing (MD5, SHA256, etc.)
6. **urllib.parse** - URL parsing and encoding

### Priority 2: Moderately Useful

7. **math** - Mathematical functions
8. **random** - Random number generation
9. **statistics** - Statistical functions
10. **collections** - Specialized data structures

### Priority 3: Occasionally Useful

11. **itertools** - Iterator tools
12. **functools** - Higher-order functions
13. **operator** - Standard operators as functions
14. **string** - String constants and templates
15. **textwrap** - Text wrapping utilities

---

## Module 1: json - JSON Operations

**Most common module** - Parse and generate JSON data.

### Parse JSON String

```python
import json

# Parse JSON string to Python dict
json_string = '{"name": "Alice", "age": 30}'
data = json.loads(json_string)

return [{
    "json": {
        "name": data["name"],
        "age": data["age"],
        "parsed": True
    }
}]
```

### Generate JSON String

```python
import json

# Convert Python dict to JSON string
data = {
    "users": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ],
    "total": 2
}

json_string = json.dumps(data, indent=2)

return [{
    "json": {
        "json_output": json_string,
        "length": len(json_string)
    }
}]
```

### Handle JSON Errors

```python
import json

webhook_data = _input.first()["json"]["body"]
json_string = webhook_data.get("data", "")

try:
    parsed = json.loads(json_string)
    status = "valid"
    error = None
except json.JSONDecodeError as e:
    parsed = None
    status = "invalid"
    error = str(e)

return [{
    "json": {
        "status": status,
        "data": parsed,
        "error": error
    }
}]
```

### Pretty Print JSON

```python
import json

# Format JSON with indentation
data = _input.first()["json"]

pretty_json = json.dumps(data, indent=2, sort_keys=True)

return [{
    "json": {
        "formatted": pretty_json
    }
}]
```

---

## Module 2: datetime - Date and Time

**Very common** - Date parsing, formatting, calculations.

### Current Date and Time

```python
from datetime import datetime

now = datetime.now()

return [{
    "json": {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "formatted": now.strftime("%B %d, %Y at %I:%M %p")
    }
}]
```

### Parse Date String

```python
from datetime import datetime

date_string = "2025-01-15T14:30:00"
dt = datetime.fromisoformat(date_string)

return [{
    "json": {
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "weekday": dt.strftime("%A")
    }
}]
```

### Date Calculations

```python
from datetime import datetime, timedelta

now = datetime.now()

# Calculate future/past dates
tomorrow = now + timedelta(days=1)
yesterday = now - timedelta(days=1)
next_week = now + timedelta(weeks=1)
one_hour_ago = now - timedelta(hours=1)

return [{
    "json": {
        "now": now.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "yesterday": yesterday.isoformat(),
        "next_week": next_week.isoformat(),
        "one_hour_ago": one_hour_ago.isoformat()
    }
}]
```

### Compare Dates

```python
from datetime import datetime

date1 = datetime(2025, 1, 15)
date2 = datetime(2025, 1, 20)

# Calculate difference
diff = date2 - date1

return [{
    "json": {
        "days_difference": diff.days,
        "seconds_difference": diff.total_seconds(),
        "date1_is_earlier": date1 < date2,
        "date2_is_later": date2 > date1
    }
}]
```

### Format Dates

```python
from datetime import datetime

dt = datetime.now()

return [{
    "json": {
        "iso": dt.isoformat(),
        "us_format": dt.strftime("%m/%d/%Y"),
        "eu_format": dt.strftime("%d/%m/%Y"),
        "long_format": dt.strftime("%A, %B %d, %Y"),
        "time_12h": dt.strftime("%I:%M %p"),
        "time_24h": dt.strftime("%H:%M:%S")
    }
}]
```

---

## Module 3: re - Regular Expressions

**Common** - Pattern matching, text extraction, validation.

### Pattern Matching

```python
import re

text = "Email: alice@example.com, Phone: 555-1234"

# Find email
email_match = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
email = email_match.group(0) if email_match else None

# Find phone
phone_match = re.search(r'\d{3}-\d{4}', text)
phone = phone_match.group(0) if phone_match else None

return [{
    "json": {
        "email": email,
        "phone": phone
    }
}]
```

### Extract All Matches

```python
import re

text = "Tags: #python #automation #workflow #n8n"

# Find all hashtags
hashtags = re.findall(r'#(\w+)', text)

return [{
    "json": {
        "tags": hashtags,
        "count": len(hashtags)
    }
}]
```

### Replace Patterns

```python
import re

text = "Price: $99.99, Discount: $10.00"

# Remove dollar signs
cleaned = re.sub(r'\$', '', text)

# Replace multiple spaces with single space
normalized = re.sub(r'\s+', ' ', cleaned)

return [{
    "json": {
        "original": text,
        "cleaned": cleaned,
        "normalized": normalized
    }
}]
```

### Validate Format

```python
import re

email = _input.first()["json"]["body"].get("email", "")

# Email validation pattern
email_pattern = r'^[\w.-]+@[\w.-]+\.\w+$'
is_valid = bool(re.match(email_pattern, email))

return [{
    "json": {
        "email": email,
        "valid": is_valid
    }
}]
```

### Split on Pattern

```python
import re

text = "apple,banana;orange|grape"

# Split on multiple delimiters
items = re.split(r'[,;|]', text)

# Clean up whitespace
items = [item.strip() for item in items]

return [{
    "json": {
        "items": items,
        "count": len(items)
    }
}]
```

---

## Module 4: base64 - Encoding/Decoding

**Common** - Encode binary data, API authentication.

### Encode String to Base64

```python
import base64

text = "Hello, World!"

# Encode to base64
encoded_bytes = base64.b64encode(text.encode('utf-8'))
encoded_string = encoded_bytes.decode('utf-8')

return [{
    "json": {
        "original": text,
        "encoded": encoded_string
    }
}]
```

### Decode Base64 to String

```python
import base64

encoded = "SGVsbG8sIFdvcmxkIQ=="

# Decode from base64
decoded_bytes = base64.b64decode(encoded)
decoded_string = decoded_bytes.decode('utf-8')

return [{
    "json": {
        "encoded": encoded,
        "decoded": decoded_string
    }
}]
```

### Basic Auth Header

```python
import base64

username = "admin"
password = "secret123"

# Create Basic Auth header
credentials = f"{username}:{password}"
encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
auth_header = f"Basic {encoded}"

return [{
    "json": {
        "authorization": auth_header
    }
}]
```

---

## Module 5: hashlib - Hashing

**Common** - Generate checksums, hash passwords, create IDs.

### MD5 Hash

```python
import hashlib

text = "Hello, World!"

# Generate MD5 hash
md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

return [{
    "json": {
        "original": text,
        "md5": md5_hash
    }
}]
```

### SHA256 Hash

```python
import hashlib

data = _input.first()["json"]["body"]
text = data.get("password", "")

# Generate SHA256 hash (more secure than MD5)
sha256_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

return [{
    "json": {
        "hashed": sha256_hash
    }
}]
```

### Generate Unique ID

```python
import hashlib
from datetime import datetime

# Create unique ID from multiple values
unique_string = f"{datetime.now().isoformat()}-{_json.get('user_id', 'unknown')}"
unique_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:16]

return [{
    "json": {
        "id": unique_id,
        "generated_at": datetime.now().isoformat()
    }
}]
```

---

## Module 6: urllib.parse - URL Operations

**Common** - Parse URLs, encode parameters.

### Parse URL

```python
from urllib.parse import urlparse

url = "https://example.com/path?key=value&foo=bar#section"

parsed = urlparse(url)

return [{
    "json": {
        "scheme": parsed.scheme,      # "https"
        "netloc": parsed.netloc,      # "example.com"
        "path": parsed.path,          # "/path"
        "query": parsed.query,        # "key=value&foo=bar"
        "fragment": parsed.fragment    # "section"
    }
}]
```

### URL Encode Parameters

```python
from urllib.parse import urlencode

params = {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "message": "Hello, World!"
}

# Encode parameters for URL
encoded = urlencode(params)

return [{
    "json": {
        "query_string": encoded,
        "full_url": f"https://api.example.com/submit?{encoded}"
    }
}]
```

### Parse Query String

```python
from urllib.parse import parse_qs

query_string = "name=Alice&age=30&tags=python&tags=n8n"

# Parse query string
params = parse_qs(query_string)

return [{
    "json": {
        "name": params.get("name", [""])[0],
        "age": int(params.get("age", ["0"])[0]),
        "tags": params.get("tags", [])
    }
}]
```

### URL Encode/Decode Strings

```python
from urllib.parse import quote, unquote

text = "Hello, World! 你好"

# URL encode
encoded = quote(text)

# URL decode
decoded = unquote(encoded)

return [{
    "json": {
        "original": text,
        "encoded": encoded,
        "decoded": decoded
    }
}]
```

---

## Module 7: math - Mathematical Operations

**Moderately useful** - Advanced math functions.

### Basic Math Functions

```python
import math

number = 16.7

return [{
    "json": {
        "ceiling": math.ceil(number),      # 17
        "floor": math.floor(number),       # 16
        "rounded": round(number),          # 17
        "square_root": math.sqrt(16),      # 4.0
        "power": math.pow(2, 3),          # 8.0
        "absolute": math.fabs(-5.5)       # 5.5
    }
}]
```

### Trigonometry

```python
import math

angle_degrees = 45
angle_radians = math.radians(angle_degrees)

return [{
    "json": {
        "sine": math.sin(angle_radians),
        "cosine": math.cos(angle_radians),
        "tangent": math.tan(angle_radians),
        "pi": math.pi,
        "e": math.e
    }
}]
```

### Logarithms

```python
import math

number = 100

return [{
    "json": {
        "log10": math.log10(number),     # 2.0
        "natural_log": math.log(number), # 4.605...
        "log2": math.log2(number)        # 6.644...
    }
}]
```

---

## Module 8: random - Random Numbers

**Moderately useful** - Generate random data, sampling.

### Random Numbers

```python
import random

return [{
    "json": {
        "random_float": random.random(),           # 0.0 to 1.0
        "random_int": random.randint(1, 100),      # 1 to 100
        "random_range": random.randrange(0, 100, 5) # 0, 5, 10, ..., 95
    }
}]
```

### Random Choice

```python
import random

colors = ["red", "green", "blue", "yellow"]
users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

return [{
    "json": {
        "random_color": random.choice(colors),
        "random_user": random.choice(users)
    }
}]
```

### Shuffle List

```python
import random

items = [1, 2, 3, 4, 5]
shuffled = items.copy()
random.shuffle(shuffled)

return [{
    "json": {
        "original": items,
        "shuffled": shuffled
    }
}]
```

### Random Sample

```python
import random

items = list(range(1, 101))

# Get 10 random items without replacement
sample = random.sample(items, 10)

return [{
    "json": {
        "sample": sample,
        "count": len(sample)
    }
}]
```

---

## Module 9: statistics - Statistical Functions

**Moderately useful** - Calculate stats from data.

### Basic Statistics

```python
import statistics

numbers = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

return [{
    "json": {
        "mean": statistics.mean(numbers),           # 55.0
        "median": statistics.median(numbers),       # 55.0
        "mode": statistics.mode([1, 2, 2, 3]),     # 2
        "stdev": statistics.stdev(numbers),        # 30.28...
        "variance": statistics.variance(numbers)   # 916.67...
    }
}]
```

### Aggregate from Items

```python
import statistics

all_items = _input.all()

# Extract amounts
amounts = [item["json"].get("amount", 0) for item in all_items]

if amounts:
    return [{
        "json": {
            "count": len(amounts),
            "total": sum(amounts),
            "average": statistics.mean(amounts),
            "median": statistics.median(amounts),
            "min": min(amounts),
            "max": max(amounts),
            "range": max(amounts) - min(amounts)
        }
    }]
else:
    return [{"json": {"error": "No data"}}]
```

---

## Workarounds for Missing Libraries

### HTTP Requests (No requests library)

```python
# ❌ Can't use requests library
# import requests  # ModuleNotFoundError!

# ✅ Use HTTP Request node instead
# Add HTTP Request node BEFORE Code node
# Access the response in Code node

response_data = _input.first()["json"]

return [{
    "json": {
        "status": response_data.get("status"),
        "data": response_data.get("body"),
        "processed": True
    }
}]
```

### Data Processing (No pandas)

```python
# ❌ Can't use pandas
# import pandas as pd  # ModuleNotFoundError!

# ✅ Use Python's built-in list comprehensions
all_items = _input.all()

# Filter
active_items = [
    item for item in all_items
    if item["json"].get("status") == "active"
]

# Group by
from collections import defaultdict
grouped = defaultdict(list)

for item in all_items:
    category = item["json"].get("category", "other")
    grouped[category].append(item["json"])

# Aggregate
import statistics
amounts = [item["json"].get("amount", 0) for item in all_items]
total = sum(amounts)
average = statistics.mean(amounts) if amounts else 0

return [{
    "json": {
        "active_count": len(active_items),
        "grouped": dict(grouped),
        "total": total,
        "average": average
    }
}]
```

### Database Operations (No drivers)

```python
# ❌ Can't use database drivers
# import psycopg2  # ModuleNotFoundError!
# import pymongo   # ModuleNotFoundError!

# ✅ Use n8n database nodes instead
# Add Postgres/MySQL/MongoDB node BEFORE Code node
# Process results in Code node

db_results = _input.first()["json"]

return [{
    "json": {
        "record_count": len(db_results) if isinstance(db_results, list) else 1,
        "processed": True
    }
}]
```

---

## Complete Standard Library List

**Available** (commonly useful):
- json
- datetime, time
- re
- base64
- hashlib
- urllib.parse, urllib.request, urllib.error
- math
- random
- statistics
- collections (defaultdict, Counter, namedtuple)
- itertools
- functools
- operator
- string
- textwrap

**Available** (less common):
- os.path (path operations only)
- copy
- typing
- enum
- decimal
- fractions

**NOT Available** (external libraries):
- requests (HTTP)
- pandas (data analysis)
- numpy (numerical computing)
- bs4/beautifulsoup4 (HTML parsing)
- selenium (browser automation)
- psycopg2, pymongo, sqlalchemy (databases)
- flask, fastapi (web frameworks)
- pillow (image processing)
- openpyxl, xlsxwriter (Excel)

---

## Best Practices

### 1. Use Standard Library When Possible

```python
# ✅ GOOD: Use standard library
import json
import datetime
import re

data = _input.first()["json"]
processed = json.loads(data.get("json_string", "{}"))

return [{"json": processed}]
```

### 2. Fall Back to n8n Nodes

```python
# For operations requiring external libraries,
# use n8n nodes instead:
# - HTTP Request for API calls
# - Postgres/MySQL for databases
# - Extract from File for parsing

# Then process results in Code node
result = _input.first()["json"]
return [{"json": {"processed": result}}]
```

### 3. Combine Multiple Modules

```python
import json
import base64
import hashlib
from datetime import datetime

# Combine modules for complex operations
data = _input.first()["json"]["body"]

# Hash sensitive data
user_id = hashlib.sha256(data.get("email", "").encode()).hexdigest()[:16]

# Encode for storage
encoded_data = base64.b64encode(json.dumps(data).encode()).decode()

return [{
    "json": {
        "user_id": user_id,
        "encoded_data": encoded_data,
        "timestamp": datetime.now().isoformat()
    }
}]
```

---

## Summary

**Most Useful Modules**:
1. json - Parse/generate JSON
2. datetime - Date operations
3. re - Regular expressions
4. base64 - Encoding
5. hashlib - Hashing
6. urllib.parse - URL operations

**Critical Limitation**:
- NO external libraries (requests, pandas, numpy, etc.)

**Recommended Approach**:
- Use **JavaScript** for 95% of use cases
- Use Python only when specifically needed
- Use n8n nodes for operations requiring external libraries

**See Also**:
- [SKILL.md](SKILL.md) - Python Code overview
- [DATA_ACCESS.md](DATA_ACCESS.md) - Data access patterns
- [COMMON_PATTERNS.md](COMMON_PATTERNS.md) - Production patterns
- [ERROR_PATTERNS.md](ERROR_PATTERNS.md) - Avoid common mistakes
