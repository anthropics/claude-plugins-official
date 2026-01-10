# Node Discovery Tools Guide

Complete guide for finding and understanding n8n nodes.

---

## search_nodes (START HERE!)

**Speed**: <20ms

**Use when**: You know what you're looking for (keyword, service, use case)

**Syntax**:
```javascript
search_nodes({
  query: "slack",      // Required: search keywords
  mode: "OR",          // Optional: OR (default), AND, FUZZY
  limit: 20,           // Optional: max results (default 20)
  source: "all",       // Optional: all, core, community, verified
  includeExamples: false  // Optional: include template configs
})
```

**Returns**:
```javascript
{
  "query": "slack",
  "results": [
    {
      "nodeType": "nodes-base.slack",                    // For search/validate tools
      "workflowNodeType": "n8n-nodes-base.slack",       // For workflow tools
      "displayName": "Slack",
      "description": "Consume Slack API",
      "category": "output",
      "relevance": "high"
    }
  ]
}
```

**Tips**:
- Common searches: webhook, http, database, email, slack, google, ai
- `OR` mode (default): matches any word
- `AND` mode: requires all words
- `FUZZY` mode: typo-tolerant (finds "slak" → Slack)
- Use `source: "core"` for only built-in nodes
- Use `includeExamples: true` for real-world configs

---

## get_node (UNIFIED NODE INFORMATION)

The `get_node` tool provides all node information with different detail levels and modes.

### Detail Levels (mode="info")

| Detail | Tokens | Use When |
|--------|--------|----------|
| `minimal` | ~200 | Quick metadata check |
| `standard` | ~1-2K | **Most use cases (DEFAULT)** |
| `full` | ~3-8K | Complex debugging only |

### Standard Detail (RECOMMENDED)

**Speed**: <10ms | **Size**: ~1-2K tokens

**Use when**: You've found the node and need configuration details

```javascript
get_node({
  nodeType: "nodes-base.slack",      // Required: SHORT prefix format
  includeExamples: true              // Optional: get real template configs
})
// detail="standard" is the default
```

**Returns**:
- Available operations and resources
- Essential properties (10-20 most common)
- Metadata (isAITool, isTrigger, hasCredentials)
- Real examples from templates (if includeExamples: true)

### Minimal Detail

**Speed**: <5ms | **Size**: ~200 tokens

**Use when**: Just need basic metadata

```javascript
get_node({
  nodeType: "nodes-base.slack",
  detail: "minimal"
})
```

**Returns**: nodeType, displayName, description, category

### Full Detail (USE SPARINGLY)

**Speed**: <100ms | **Size**: ~3-8K tokens

**Use when**: Debugging complex configuration, need complete schema

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  detail: "full"
})
```

**Warning**: Large payload! Use `standard` for most cases.

---

## get_node Modes

### mode="docs" (READABLE DOCUMENTATION)

**Use when**: Need human-readable documentation with examples

```javascript
get_node({
  nodeType: "nodes-base.slack",
  mode: "docs"
})
```

**Returns**: Formatted markdown with:
- Usage examples
- Authentication guide
- Common patterns
- Best practices

**Better than raw schema for learning!**

### mode="search_properties" (FIND SPECIFIC FIELDS)

**Use when**: Looking for specific property in a node

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "auth",           // Required for this mode
  maxPropertyResults: 20           // Optional: default 20
})
```

**Returns**: Property paths and descriptions matching query

**Common searches**: auth, header, body, json, url, method, credential

### mode="versions" (VERSION HISTORY)

**Use when**: Need to check node version history

```javascript
get_node({
  nodeType: "nodes-base.executeWorkflow",
  mode: "versions"
})
```

**Returns**: Version history with breaking changes flags

### mode="compare" (COMPARE VERSIONS)

**Use when**: Need to see differences between versions

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "compare",
  fromVersion: "3.0",
  toVersion: "4.1"       // Optional: defaults to latest
})
```

**Returns**: Property-level changes between versions

### mode="breaking" (BREAKING CHANGES ONLY)

**Use when**: Checking for breaking changes before upgrades

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "breaking",
  fromVersion: "3.0"
})
```

**Returns**: Only breaking changes (not all changes)

### mode="migrations" (AUTO-MIGRATABLE)

**Use when**: Checking what can be auto-migrated

```javascript
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "migrations",
  fromVersion: "3.0"
})
```

**Returns**: Changes that can be automatically migrated

---

## Additional Parameters

### includeTypeInfo

Add type structure metadata (validation rules, JS types)

```javascript
get_node({
  nodeType: "nodes-base.if",
  includeTypeInfo: true   // Adds ~80-120 tokens per property
})
```

Use for complex nodes like filter, resourceMapper

### includeExamples

Include real-world configuration examples from templates

```javascript
get_node({
  nodeType: "nodes-base.slack",
  includeExamples: true   // Adds ~200-400 tokens per example
})
```

Only works with `mode: "info"` and `detail: "standard"`

---

## Common Workflow: Finding & Configuring

```
Step 1: Search
search_nodes({query: "slack"})
→ Returns: nodes-base.slack

Step 2: Get Operations (18s avg thinking time)
get_node({
  nodeType: "nodes-base.slack",
  includeExamples: true
})
→ Returns: operations list + example configs

Step 3: Validate Config
validate_node({
  nodeType: "nodes-base.slack",
  config: {resource: "channel", operation: "create"},
  profile: "runtime"
})
→ Returns: validation result

Step 4: Use in Workflow
(Configuration ready!)
```

**Most common pattern**: search → get_node (18s average)

---

## Quick Comparison

| Tool/Mode | When to Use | Speed | Size |
|-----------|-------------|-------|------|
| `search_nodes` | Find by keyword | <20ms | Small |
| `get_node (standard)` | **Get config (DEFAULT)** | <10ms | 1-2K |
| `get_node (minimal)` | Quick metadata | <5ms | 200 |
| `get_node (full)` | Complex debugging | <100ms | 3-8K |
| `get_node (docs)` | Learn usage | Fast | Medium |
| `get_node (search_properties)` | Find specific field | Fast | Small |
| `get_node (versions)` | Check versions | Fast | Small |

**Best Practice**: search → get_node(standard) → validate

---

## nodeType Format (CRITICAL!)

**Search/Validate Tools** (SHORT prefix):
```javascript
"nodes-base.slack"
"nodes-base.httpRequest"
"nodes-langchain.agent"
```

**Workflow Tools** (FULL prefix):
```javascript
"n8n-nodes-base.slack"
"n8n-nodes-base.httpRequest"
"@n8n/n8n-nodes-langchain.agent"
```

**Conversion**: search_nodes returns BOTH formats:
```javascript
{
  "nodeType": "nodes-base.slack",          // Use with get_node, validate_node
  "workflowNodeType": "n8n-nodes-base.slack"  // Use with n8n_create_workflow
}
```

---

## Examples

### Find and Configure HTTP Request

```javascript
// Step 1: Search
search_nodes({query: "http request"})

// Step 2: Get standard info
get_node({nodeType: "nodes-base.httpRequest"})

// Step 3: Find auth options
get_node({
  nodeType: "nodes-base.httpRequest",
  mode: "search_properties",
  propertyQuery: "authentication"
})

// Step 4: Validate config
validate_node({
  nodeType: "nodes-base.httpRequest",
  config: {method: "POST", url: "https://api.example.com"},
  profile: "runtime"
})
```

### Explore AI Nodes

```javascript
// Find all AI-related nodes
search_nodes({query: "ai agent", source: "all"})

// Get AI Agent documentation
get_node({nodeType: "nodes-langchain.agent", mode: "docs"})

// Get configuration details with examples
get_node({
  nodeType: "nodes-langchain.agent",
  includeExamples: true
})
```

### Check Version Compatibility

```javascript
// See all versions
get_node({nodeType: "nodes-base.executeWorkflow", mode: "versions"})

// Check breaking changes from v1 to v2
get_node({
  nodeType: "nodes-base.executeWorkflow",
  mode: "breaking",
  fromVersion: "1.0"
})
```

---

## Related

- [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md) - Validate node configs
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Use nodes in workflows
