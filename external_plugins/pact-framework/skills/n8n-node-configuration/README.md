# n8n Node Configuration

Expert guidance for operation-aware node configuration with property dependencies.

## Overview

**Skill Name**: n8n Node Configuration
**Priority**: Medium
**Purpose**: Teach operation-aware configuration with progressive discovery and dependency awareness

## The Problem This Solves

Node configuration patterns:

- get_node_essentials is the primary discovery tool (18s avg from search → essentials)
- 91.7% success rate with essentials-based configuration
- 56 seconds average between configuration edits

**Key insight**: Most configurations only need essentials, not full schema!

## What This Skill Teaches

### Core Concepts

1. **Operation-Aware Configuration**
   - Resource + operation determine required fields
   - Different operations = different requirements
   - Always check requirements when changing operation

2. **Property Dependencies**
   - Fields appear/disappear based on other field values
   - displayOptions control visibility
   - Conditional required fields
   - Understanding dependency chains

3. **Progressive Discovery**
   - Start with get_node_essentials (91.7% success)
   - Escalate to get_property_dependencies if needed
   - Use get_node_info only when necessary
   - Right tool for right job

4. **Configuration Workflow**
   - Identify → Discover → Configure → Validate → Iterate
   - Average 2-3 validation cycles
   - Read errors for dependency hints
   - 56 seconds between edits average

5. **Common Patterns**
   - Resource/operation nodes (Slack, Sheets)
   - HTTP-based nodes (HTTP Request, Webhook)
   - Database nodes (Postgres, MySQL)
   - Conditional logic nodes (IF, Switch)

## File Structure

```
n8n-node-configuration/
├── SKILL.md (692 lines)
│   Main configuration guide
│   - Configuration philosophy (progressive disclosure)
│   - Core concepts (operation-aware, dependencies)
│   - Configuration workflow (8-step process)
│   - get_node_essentials vs get_node_info
│   - Property dependencies deep dive
│   - Common node patterns (4 categories)
│   - Operation-specific examples
│   - Conditional requirements
│   - Anti-patterns and best practices
│
├── DEPENDENCIES.md (671 lines)
│   Property dependencies reference
│   - displayOptions mechanism
│   - show vs hide rules
│   - Multiple conditions (AND logic)
│   - Multiple values (OR logic)
│   - 4 common dependency patterns
│   - Using get_property_dependencies
│   - Complex dependency examples
│   - Nested dependencies
│   - Auto-sanitization interaction
│   - Troubleshooting guide
│   - Advanced patterns
│
├── OPERATION_PATTERNS.md (783 lines)
│   Common configurations by node type
│   - HTTP Request (GET/POST/PUT/DELETE)
│   - Webhook (basic/auth/response)
│   - Slack (post/update/create)
│   - Gmail (send/get)
│   - Postgres (query/insert/update)
│   - Set (values/mapping)
│   - Code (per-item/all-items)
│   - IF (string/number/boolean)
│   - Switch (rules/fallback)
│   - OpenAI (chat completion)
│   - Schedule (daily/interval/cron)
│   - Gotchas and tips for each
│
└── README.md (this file)
    Skill metadata and statistics
```

**Total**: ~2,146 lines across 4 files + 4 evaluations

## Usage Statistics

Configuration metrics:

| Metric | Value | Insight |
|---|---|---|
| get_node_essentials | Primary tool | Most popular discovery pattern |
| Success rate (essentials) | 91.7% | Essentials sufficient for most |
| Avg time search→essentials | 18 seconds | Fast discovery workflow |
| Avg time between edits | 56 seconds | Iterative configuration |

## Tool Usage Pattern

**Most common discovery pattern**:
```
search_nodes → get_node_essentials (18s average)
```

**Configuration cycle**:
```
get_node_essentials → configure → validate → iterate (56s avg per edit)
```

## Key Insights

### 1. Progressive Disclosure Works

**91.7% success rate** with get_node_essentials proves most configurations don't need full schema.

**Strategy**:
1. Start with essentials
2. Escalate to dependencies if stuck
3. Use full schema only when necessary

### 2. Operations Determine Requirements

**Same node, different operation = different requirements**

Example: Slack message
- `operation="post"` → needs channel + text
- `operation="update"` → needs messageId + text (different!)

### 3. Dependencies Control Visibility

**Fields appear/disappear based on other values**

Example: HTTP Request
- `method="GET"` → body hidden
- `method="POST"` + `sendBody=true` → body required

### 4. Configuration is Iterative

**Average 56 seconds between edits** shows configuration is iterative, not one-shot.

**Normal workflow**:
1. Configure minimal
2. Validate → error
3. Add missing field
4. Validate → error
5. Adjust value
6. Validate → valid ✅

### 5. Common Gotchas Exist

**Top 5 gotchas** from patterns:
1. Webhook data under `$json.body` (not `$json`)
2. POST needs `sendBody: true`
3. Slack channel format (`#name`)
4. SQL parameterized queries (injection prevention)
5. Timezone must be explicit (schedule nodes)

## Usage Examples

### Example 1: Basic Configuration Flow

```javascript
// Step 1: Get essentials
const info = get_node_essentials({
  nodeType: "nodes-base.slack"
});

// Step 2: Configure for operation
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "Hello!"
}

// Step 3: Validate
validate_node_operation({...});
// ✅ Valid!
```

### Example 2: Handling Dependencies

```javascript
// Step 1: Configure HTTP POST
{
  "method": "POST",
  "url": "https://api.example.com/create"
}

// Step 2: Validate → Error: "sendBody required"
// Step 3: Check dependencies
get_property_dependencies({
  nodeType: "nodes-base.httpRequest"
});
// Shows: body visible when sendBody=true

// Step 4: Fix
{
  "method": "POST",
  "url": "https://api.example.com/create",
  "sendBody": true,
  "body": {
    "contentType": "json",
    "content": {...}
  }
}
// ✅ Valid!
```

### Example 3: Operation Change

```javascript
// Initial config (post operation)
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "Hello"
}

// Change operation
{
  "resource": "message",
  "operation": "update",  // Changed!
  // Need to check new requirements
}

// Get essentials for update operation
get_node_essentials({nodeType: "nodes-base.slack"});
// Shows: messageId required, channel optional

// Correct config
{
  "resource": "message",
  "operation": "update",
  "messageId": "1234567890.123456",
  "text": "Updated"
}
```

## When This Skill Activates

**Trigger phrases**:
- "how to configure"
- "what fields are required"
- "property dependencies"
- "get_node_essentials vs get_node_info"
- "operation-specific"
- "field not visible"

**Common scenarios**:
- Configuring new nodes
- Understanding required fields
- Field appears/disappears unexpectedly
- Choosing between discovery tools
- Switching operations
- Learning common patterns

## Integration with Other Skills

### Works With:
- **n8n MCP Tools Expert** - How to call discovery tools correctly
- **n8n Validation Expert** - Interpret missing_required errors
- **n8n Expression Syntax** - Configure expression fields
- **n8n Workflow Patterns** - Apply patterns with proper node config

### Complementary:
- Use MCP Tools Expert to learn tool selection
- Use Validation Expert to fix configuration errors
- Use Expression Syntax for dynamic field values
- Use Workflow Patterns to understand node relationships

## Testing

**Evaluations**: 4 test scenarios

1. **eval-001-property-dependencies.json**
   - Tests understanding of displayOptions
   - Guides to get_property_dependencies
   - Explains conditional requirements

2. **eval-002-operation-specific-config.json**
   - Tests operation-aware configuration
   - Identifies resource + operation pattern
   - References OPERATION_PATTERNS.md

3. **eval-003-conditional-fields.json**
   - Tests unary vs binary operators
   - Explains singleValue dependency
   - Mentions auto-sanitization

4. **eval-004-essentials-vs-info.json**
   - Tests tool selection knowledge
   - Explains progressive disclosure
   - Provides success rate statistics

## Success Metrics

**Before this skill**:
- Using get_node_info for everything (slow, overwhelming)
- Not understanding property dependencies
- Confused when fields appear/disappear
- Not aware of operation-specific requirements
- Trial and error configuration

**After this skill**:
- Start with get_node_essentials (91.7% success)
- Understand displayOptions mechanism
- Predict field visibility based on dependencies
- Check requirements when changing operations
- Systematic configuration approach
- Know common patterns by node type

## Coverage

**Node types covered**: Top 20 most-used nodes

| Category | Nodes | Coverage |
|---|---|---|
| HTTP/API | HTTP Request, Webhook | Complete |
| Communication | Slack, Gmail | Common operations |
| Database | Postgres, MySQL | CRUD operations |
| Transform | Set, Code | All modes |
| Conditional | IF, Switch | All operator types |
| AI | OpenAI | Chat completion |
| Schedule | Schedule Trigger | All modes |

## Related Documentation

- **n8n-mcp MCP Server**: Provides discovery tools
- **n8n Node API**: get_node_essentials, get_property_dependencies, get_node_info
- **n8n Schema**: displayOptions mechanism, property definitions

## Version History

- **v1.0** (2025-10-20): Initial implementation
  - SKILL.md with configuration workflow
  - DEPENDENCIES.md with displayOptions deep dive
  - OPERATION_PATTERNS.md with 20+ node patterns
  - 4 evaluation scenarios

## Author

Conceived by Romuald Członkowski - [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)

Part of the n8n-skills meta-skill collection.
