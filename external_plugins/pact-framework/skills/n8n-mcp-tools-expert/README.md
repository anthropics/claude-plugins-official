# n8n MCP Tools Expert

Expert guide for using n8n-mcp MCP tools effectively.

---

## Purpose

Teaches how to use n8n-mcp MCP server tools correctly for efficient workflow building.

## Activates On

- search nodes
- find node
- validate
- MCP tools
- template
- workflow
- n8n-mcp
- tool selection

## File Count

5 files, ~1,150 lines total

## Priority

**HIGHEST** - Essential for correct MCP tool usage

## Dependencies

**n8n-mcp tools**: All of them! (40+ tools)

**Related skills**:
- n8n Expression Syntax (write expressions for workflows)
- n8n Workflow Patterns (use tools to build patterns)
- n8n Validation Expert (interpret validation results)
- n8n Node Configuration (configure nodes found with tools)

## Coverage

### Core Topics
- Tool selection guide (which tool for which task)
- nodeType format differences (nodes-base.* vs n8n-nodes-base.*)
- Validation profiles (minimal/runtime/ai-friendly/strict)
- Smart parameters (branch, case for multi-output nodes)
- Auto-sanitization system
- Workflow management (15 operation types)
- AI connection types (8 types)

### Tool Categories
- Node Discovery (search, list, essentials, info)
- Configuration Validation (minimal, operation, workflow)
- Workflow Management (create, update, validate)
- Template Library (search, get)
- Documentation (tools, database stats)

## Evaluations

5 scenarios (100% coverage expected):
1. **eval-001**: Tool selection (search_nodes)
2. **eval-002**: nodeType format (nodes-base.* prefix)
3. **eval-003**: Validation workflow (profiles)
4. **eval-004**: essentials vs info (5KB vs 100KB)
5. **eval-005**: Smart parameters (branch, case)

## Key Features

✅ **Tool Selection Guide**: Which tool to use for each task
✅ **Common Patterns**: Most effective tool usage sequences
✅ **Format Guidance**: nodeType format differences explained
✅ **Smart Parameters**: Semantic branch/case routing for multi-output nodes
✅ **Auto-Sanitization**: Explains automatic validation fixes
✅ **Comprehensive**: Covers all 40+ MCP tools

## Files

- **SKILL.md** (480 lines) - Core tool usage guide
- **SEARCH_GUIDE.md** (220 lines) - Node discovery tools
- **VALIDATION_GUIDE.md** (250 lines) - Validation tools and profiles
- **WORKFLOW_GUIDE.md** (200 lines) - Workflow management
- **README.md** (this file) - Skill metadata

## What You'll Learn

- Correct nodeType formats (nodes-base.* for search tools)
- When to use get_node_essentials vs get_node_info
- How to use validation profiles effectively
- Smart parameters for multi-output nodes (IF/Switch)
- Common tool usage patterns and workflows

## Last Updated

2025-10-20

---

**Part of**: n8n-skills repository
**Conceived by**: Romuald Członkowski - [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)
