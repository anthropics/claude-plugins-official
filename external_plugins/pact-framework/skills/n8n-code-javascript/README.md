# n8n Code JavaScript

Expert guidance for writing JavaScript code in n8n Code nodes.

---

## Purpose

Teaches how to write effective JavaScript in n8n Code nodes, avoid common errors, and use built-in functions effectively.

---

## Activates On

**Trigger keywords**:
- "javascript code node"
- "write javascript in n8n"
- "code node javascript"
- "$input syntax"
- "$json syntax"
- "$helpers.httpRequest"
- "DateTime luxon"
- "code node error"
- "webhook data code"
- "return format code node"

**Common scenarios**:
- Writing JavaScript code in Code nodes
- Troubleshooting Code node errors
- Making HTTP requests from code
- Working with dates and times
- Accessing webhook data
- Choosing between All Items and Each Item mode

---

## What You'll Learn

### Quick Start
- Mode selection (All Items vs Each Item)
- Data access patterns ($input.all(), $input.first(), $input.item)
- Correct return format: `[{json: {...}}]`
- Webhook data structure (.body nesting)
- Built-in functions overview

### Data Access Mastery
- $input.all() - Batch operations (most common)
- $input.first() - Single item operations
- $input.item - Each Item mode processing
- $node - Reference other workflow nodes
- **Critical gotcha**: Webhook data under `.body`

### Common Patterns (Production-Tested)
1. Multi-source Data Aggregation
2. Regex Filtering & Pattern Matching
3. Markdown Parsing & Structured Extraction
4. JSON Comparison & Validation
5. CRM Data Transformation
6. Release Information Processing
7. Array Transformation with Context
8. Slack Block Kit Formatting
9. Top N Filtering & Ranking
10. String Aggregation & Reporting

### Error Prevention
Top 5 errors to avoid:
1. **Empty code / missing return** (38% of failures)
2. **Expression syntax confusion** (using `{{}}` in code)
3. **Incorrect return format** (missing array wrapper or json property)
4. **Unmatched brackets** (string escaping issues)
5. **Missing null checks** (crashes on undefined)

### Built-in Functions
- **$helpers.httpRequest()** - Make HTTP requests
- **DateTime (Luxon)** - Advanced date/time operations
- **$jmespath()** - Query JSON structures
- **$getWorkflowStaticData()** - Persistent storage
- Standard JavaScript globals (Math, JSON, console)
- Available Node.js modules (crypto, Buffer, URL)

---

## File Structure

```
n8n-code-javascript/
├── SKILL.md (500 lines)
│   Overview, quick start, mode selection, best practices
│   - Mode selection guide (All Items vs Each Item)
│   - Data access patterns overview
│   - Return format requirements
│   - Critical webhook gotcha
│   - Error prevention overview
│   - Quick reference checklist
│
├── DATA_ACCESS.md (400 lines)
│   Complete data access patterns
│   - $input.all() - Most common (26% usage)
│   - $input.first() - Very common (25% usage)
│   - $input.item - Each Item mode (19% usage)
│   - $node - Reference other nodes
│   - Webhook data structure (.body nesting)
│   - Choosing the right pattern
│   - Common mistakes to avoid
│
├── COMMON_PATTERNS.md (600 lines)
│   10 production-tested patterns
│   - Pattern 1: Multi-source Aggregation
│   - Pattern 2: Regex Filtering
│   - Pattern 3: Markdown Parsing
│   - Pattern 4: JSON Comparison
│   - Pattern 5: CRM Transformation
│   - Pattern 6: Release Processing
│   - Pattern 7: Array Transformation
│   - Pattern 8: Slack Block Kit
│   - Pattern 9: Top N Filtering
│   - Pattern 10: String Aggregation
│   - Pattern selection guide
│
├── ERROR_PATTERNS.md (450 lines)
│   Top 5 errors with solutions
│   - Error #1: Empty Code / Missing Return (38%)
│   - Error #2: Expression Syntax Confusion (8%)
│   - Error #3: Incorrect Return Wrapper (5%)
│   - Error #4: Unmatched Brackets (6%)
│   - Error #5: Missing Null Checks
│   - Error prevention checklist
│   - Quick error reference
│   - Debugging tips
│
├── BUILTIN_FUNCTIONS.md (450 lines)
│   Complete built-in function reference
│   - $helpers.httpRequest() API reference
│   - DateTime (Luxon) complete guide
│   - $jmespath() JSON querying
│   - $getWorkflowStaticData() persistent storage
│   - Standard JavaScript globals
│   - Available Node.js modules
│   - What's NOT available
│
└── README.md (this file)
    Skill metadata and overview
```

**Total**: ~2,400 lines across 6 files

---

## Coverage

### Mode Selection
- **Run Once for All Items** - Recommended for 95% of use cases
- **Run Once for Each Item** - Specialized cases only
- Decision guide and performance implications

### Data Access
- Most common patterns with usage statistics
- Webhook data structure (critical .body gotcha)
- Safe access patterns with null checks
- When to use which pattern

### Error Prevention
- Top 5 errors covering 62%+ of all failures
- Clear wrong vs right examples
- Error prevention checklist
- Debugging tips and console.log usage

### Production Patterns
- 10 patterns from real workflows
- Complete working examples
- Use cases and key techniques
- Pattern selection guide

### Built-in Functions
- Complete $helpers.httpRequest() reference
- DateTime/Luxon operations (formatting, parsing, arithmetic)
- $jmespath() for JSON queries
- Persistent storage with $getWorkflowStaticData()
- Standard JavaScript and Node.js modules

---

## Critical Gotchas Highlighted

### #1: Webhook Data Structure
**MOST COMMON MISTAKE**: Webhook data is under `.body`

```javascript
// ❌ WRONG
const name = $json.name;

// ✅ CORRECT
const name = $json.body.name;
```

### #2: Return Format
**CRITICAL**: Must return array with json property

```javascript
// ❌ WRONG
return {json: {result: 'success'}};

// ✅ CORRECT
return [{json: {result: 'success'}}];
```

### #3: Expression Syntax
**Don't use `{{}}` in Code nodes**

```javascript
// ❌ WRONG
const value = "{{ $json.field }}";

// ✅ CORRECT
const value = $json.field;
```

---

## Integration with Other Skills

### n8n Expression Syntax
- **Distinction**: Expressions use `{{}}` in OTHER nodes
- **Code nodes**: Use JavaScript directly (no `{{}}`)
- **When to use each**: Code vs expressions decision guide

### n8n MCP Tools Expert
- Find Code node: `search_nodes({query: "code"})`
- Get configuration: `get_node_essentials("nodes-base.code")`
- Validate code: `validate_node_operation()`

### n8n Node Configuration
- Mode selection (All Items vs Each Item)
- Language selection (JavaScript vs Python)
- Understanding property dependencies

### n8n Workflow Patterns
- Code nodes in transformation step
- Webhook → Code → API pattern
- Error handling in workflows

### n8n Validation Expert
- Validate Code node configuration
- Handle validation errors
- Auto-fix common issues

---

## When to Use Code Node

**Use Code node when:**
- ✅ Complex transformations requiring multiple steps
- ✅ Custom calculations or business logic
- ✅ Recursive operations
- ✅ API response parsing with complex structure
- ✅ Multi-step conditionals
- ✅ Data aggregation across items

**Consider other nodes when:**
- ❌ Simple field mapping → Use **Set** node
- ❌ Basic filtering → Use **Filter** node
- ❌ Simple conditionals → Use **IF** or **Switch** node
- ❌ HTTP requests only → Use **HTTP Request** node

**Code node excels at**: Complex logic that would require chaining many simple nodes

---

## Success Metrics

**Before this skill**:
- Users confused by mode selection
- Frequent return format errors
- Expression syntax mistakes
- Webhook data access failures
- Missing null check crashes

**After this skill**:
- Clear mode selection guidance
- Understanding of return format
- JavaScript vs expression distinction
- Correct webhook data access
- Safe null-handling patterns
- Production-ready code patterns

---

## Quick Reference

### Essential Rules
1. Choose "All Items" mode (recommended)
2. Access data: `$input.all()`, `$input.first()`, `$input.item`
3. **MUST return**: `[{json: {...}}]` format
4. **Webhook data**: Under `.body` property
5. **No `{{}}` syntax**: Use JavaScript directly

### Most Common Patterns
- Batch processing → $input.all() + map/filter
- Single item → $input.first()
- Aggregation → reduce()
- HTTP requests → $helpers.httpRequest()
- Date handling → DateTime (Luxon)

### Error Prevention
- Always return data
- Check for null/undefined
- Use try-catch for risky operations
- Test with empty input
- Use console.log() for debugging

---

## Related Documentation

- **n8n Code Node Guide**: https://docs.n8n.io/code/code-node/
- **Built-in Methods Reference**: https://docs.n8n.io/code-examples/methods-variables-reference/
- **Luxon Documentation**: https://moment.github.io/luxon/

---

## Evaluations

**5 test scenarios** covering:
1. Webhook body gotcha (most common mistake)
2. Return format error (missing array wrapper)
3. HTTP request with $helpers.httpRequest()
4. Aggregation pattern with $input.all()
5. Expression syntax confusion (using `{{}}`)

Each evaluation tests skill activation, correct guidance, and reference to appropriate documentation files.

---

## Version History

- **v1.0** (2025-01-20): Initial implementation
  - SKILL.md with comprehensive overview
  - DATA_ACCESS.md covering all access patterns
  - COMMON_PATTERNS.md with 10 production patterns
  - ERROR_PATTERNS.md covering top 5 errors
  - BUILTIN_FUNCTIONS.md complete reference
  - 5 evaluation scenarios

---

## Author

Conceived by Romuald Członkowski - [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)

Part of the n8n-skills collection.
