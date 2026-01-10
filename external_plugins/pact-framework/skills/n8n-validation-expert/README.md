# n8n Validation Expert

Expert guidance for interpreting and fixing n8n validation errors.

## Overview

**Skill Name**: n8n Validation Expert
**Priority**: Medium
**Purpose**: Interpret validation errors and guide systematic fixing through the validation loop

## The Problem This Solves

Validation errors are common:

- Validation often requires iteration (79% lead to feedback loops)
- **7,841 validate → fix cycles** (avg 23s thinking + 58s fixing)
- **2-3 iterations** average to achieve valid configuration

**Key insight**: Validation is an iterative process, not a one-shot fix!

## What This Skill Teaches

### Core Concepts

1. **Error Severity Levels**
   - Errors (must fix) - Block execution
   - Warnings (should fix) - Don't block but indicate issues
   - Suggestions (optional) - Nice-to-have improvements

2. **The Validation Loop**
   - Configure → Validate → Read errors → Fix → Validate again
   - Average 2-3 iterations to success
   - 23 seconds thinking + 58 seconds fixing per cycle

3. **Validation Profiles**
   - `minimal` - Quick checks, most permissive
   - `runtime` - Recommended for most use cases
   - `ai-friendly` - Reduces false positives for AI workflows
   - `strict` - Maximum safety, many warnings

4. **Auto-Sanitization System**
   - Automatically fixes operator structure issues
   - Runs on every workflow save
   - Fixes binary/unary operator problems
   - Adds IF/Switch metadata

5. **False Positives**
   - Not all warnings need fixing
   - 40% of warnings are acceptable in context
   - Use `ai-friendly` profile to reduce by 60%
   - Document accepted warnings

## File Structure

```
n8n-validation-expert/
├── SKILL.md (690 lines)
│   Core validation concepts and workflow
│   - Validation philosophy
│   - Error severity levels
│   - The validation loop pattern
│   - Validation profiles
│   - Common error types
│   - Auto-sanitization system
│   - Workflow validation
│   - Recovery strategies
│   - Best practices
│
├── ERROR_CATALOG.md (865 lines)
│   Complete error reference with examples
│   - 9 error types with real examples
│   - missing_required (45% of errors)
│   - invalid_value (28%)
│   - type_mismatch (12%)
│   - invalid_expression (8%)
│   - invalid_reference (5%)
│   - operator_structure (2%, auto-fixed)
│   - Recovery patterns
│   - Summary with frequencies
│
├── FALSE_POSITIVES.md (669 lines)
│   When warnings are acceptable
│   - Philosophy of warning acceptance
│   - 6 common false positive types
│   - When acceptable vs when to fix
│   - Validation profile strategies
│   - Decision framework
│   - Documentation template
│   - Known n8n issues (#304, #306, #338)
│
└── README.md (this file)
    Skill metadata and statistics
```

**Total**: ~2,224 lines across 4 files

## Common Error Types

| Error Type | Priority | Auto-Fix | Severity |
|---|---|---|---|
| missing_required | Highest | ❌ | Error |
| invalid_value | High | ❌ | Error |
| type_mismatch | Medium | ❌ | Error |
| invalid_expression | Medium | ❌ | Error |
| invalid_reference | Low | ❌ | Error |
| operator_structure | Low | ✅ | Warning |

## Key Insights

### 1. Validation is Iterative
Don't expect to get it right on the first try. Multiple validation cycles (typically 2-3) are normal and expected!

### 2. False Positives Exist
Many validation warnings are acceptable in production workflows. This skill helps you recognize which ones to address vs. which to ignore.

### 3. Auto-Sanitization Works
Certain error types (like operator structure issues) are automatically fixed by n8n. Don't waste time manually fixing these!

### 4. Profile Matters
- `ai-friendly` reduces false positives by 60%
- `runtime` is the sweet spot for most use cases
- `strict` has value pre-production but is noisy

### 5. Error Messages Help
Validation errors include fix guidance - read them carefully!

## Usage Examples

### Example 1: Basic Validation Loop

```javascript
// Iteration 1
let config = {
  resource: "channel",
  operation: "create"
};

const result1 = validate_node_operation({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
});
// → Error: Missing "name"

// Iteration 2
config.name = "general";
const result2 = validate_node_operation({...});
// → Valid! ✅
```

### Example 2: Handling False Positives

```javascript
// Run validation
const result = validate_node_operation({
  nodeType: "nodes-base.slack",
  config,
  profile: "runtime"
});

// Fix errors (must fix)
if (!result.valid) {
  result.errors.forEach(error => {
    console.log(`MUST FIX: ${error.message}`);
  });
}

// Review warnings (context-dependent)
result.warnings.forEach(warning => {
  if (warning.type === 'best_practice' && isDevWorkflow) {
    console.log(`ACCEPTABLE: ${warning.message}`);
  } else {
    console.log(`SHOULD FIX: ${warning.message}`);
  }
});
```

### Example 3: Using Auto-Fix

```javascript
// Check what can be auto-fixed
const preview = n8n_autofix_workflow({
  id: "workflow-id",
  applyFixes: false  // Preview mode
});

console.log(`Can auto-fix: ${preview.fixCount} issues`);

// Apply fixes
if (preview.fixCount > 0) {
  n8n_autofix_workflow({
    id: "workflow-id",
    applyFixes: true
  });
}
```

## When This Skill Activates

**Trigger phrases**:
- "validation error"
- "validation failing"
- "what does this error mean"
- "false positive"
- "validation loop"
- "operator structure"
- "validation profile"

**Common scenarios**:
- Encountering validation errors
- Stuck in validation feedback loops
- Wondering if warnings need fixing
- Choosing the right validation profile
- Understanding auto-sanitization

## Integration with Other Skills

### Works With:
- **n8n MCP Tools Expert** - How to use validation tools correctly
- **n8n Expression Syntax** - Fix invalid_expression errors
- **n8n Node Configuration** - Understand required fields
- **n8n Workflow Patterns** - Validate pattern implementations

### Complementary:
- Use MCP Tools Expert to call validation tools
- Use Expression Syntax to fix expression errors
- Use Node Configuration to understand dependencies
- Use Workflow Patterns to validate structure

## Testing

**Evaluations**: 4 test scenarios

1. **eval-001-missing-required-field.json**
   - Tests error interpretation
   - Guides to get_node_essentials
   - References ERROR_CATALOG.md

2. **eval-002-false-positive.json**
   - Tests warning vs error distinction
   - Explains false positives
   - References FALSE_POSITIVES.md
   - Suggests ai-friendly profile

3. **eval-003-auto-sanitization.json**
   - Tests auto-sanitization understanding
   - Explains operator structure fixes
   - Advises trusting auto-fix

4. **eval-004-validation-loop.json**
   - Tests iterative validation process
   - Explains 2-3 iteration pattern
   - Provides systematic approach

## Success Metrics

**Before this skill**:
- Users confused by validation errors
- Multiple failed attempts to fix
- Frustration with "validation loops"
- Fixing issues that auto-fix handles
- Fixing all warnings unnecessarily

**After this skill**:
- Systematic error resolution
- Understanding of iteration process
- Recognition of false positives
- Trust in auto-sanitization
- Context-aware warning handling
- 94% success within 3 iterations

## Related Documentation

- **n8n-mcp MCP Server**: Provides validation tools
- **n8n Validation API**: validate_node_operation, validate_workflow, n8n_autofix_workflow
- **n8n Issues**: #304 (IF metadata), #306 (Switch branches), #338 (credentials)

## Version History

- **v1.0** (2025-10-20): Initial implementation
  - SKILL.md with core concepts
  - ERROR_CATALOG.md with 9 error types
  - FALSE_POSITIVES.md with 6 false positive patterns
  - 4 evaluation scenarios

## Author

Conceived by Romuald Członkowski - [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)

Part of the n8n-skills meta-skill collection.
