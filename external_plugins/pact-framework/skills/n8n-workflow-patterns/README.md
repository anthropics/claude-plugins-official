# n8n Workflow Patterns

Proven architectural patterns for building n8n workflows.

---

## Purpose

Teaches architectural patterns for building n8n workflows. Provides structure, best practices, and proven approaches for common use cases.

## Activates On

- build workflow
- workflow pattern
- workflow architecture
- workflow structure
- webhook processing
- http api
- api integration
- database sync
- ai agent
- chatbot
- scheduled task
- automation pattern

## File Count

7 files, ~3,700 lines total

## Priority

**HIGH** - Addresses 813 webhook searches (most common use case)

## Dependencies

**n8n-mcp tools**:
- search_nodes (find nodes for patterns)
- get_node (understand node operations)
- search_templates (find example workflows)
- ai_agents_guide (AI pattern guidance)

**Related skills**:
- n8n MCP Tools Expert (find and configure nodes)
- n8n Expression Syntax (write expressions in patterns)
- n8n Node Configuration (configure pattern nodes)
- n8n Validation Expert (validate pattern implementations)

## Coverage

### The 5 Core Patterns

1. **Webhook Processing** (Most Common - 813 searches)
   - Receive HTTP requests → Process → Respond
   - Critical gotcha: Data under $json.body
   - Authentication, validation, error handling

2. **HTTP API Integration** (892 templates)
   - Fetch from REST APIs → Transform → Store/Use
   - Authentication methods, pagination, rate limiting
   - Error handling and retries

3. **Database Operations** (456 templates)
   - Read/Write/Sync database data
   - Batch processing, transactions, performance
   - Security: parameterized queries, read-only access

4. **AI Agent Workflow** (234 templates, 270 AI nodes)
   - AI agents with tool access and memory
   - 8 AI connection types
   - ANY node can be an AI tool

5. **Scheduled Tasks** (28% of all workflows)
   - Recurring automation workflows
   - Cron schedules, timezone handling
   - Monitoring and error handling

### Cross-Cutting Concerns

- Data flow patterns (linear, branching, parallel, loops)
- Error handling strategies
- Performance optimization
- Security best practices
- Testing approaches
- Monitoring and logging

## Evaluations

5 scenarios (100% coverage expected):
1. **eval-001**: Webhook workflow structure
2. **eval-002**: HTTP API integration pattern
3. **eval-003**: Database sync pattern
4. **eval-004**: AI agent workflow with tools
5. **eval-005**: Scheduled report generation

## Key Features

✅ **5 Proven Patterns**: Webhook, HTTP API, Database, AI Agent, Scheduled tasks
✅ **Complete Examples**: Working workflow configurations for each pattern
✅ **Best Practices**: Proven approaches from real-world n8n usage
✅ **Common Gotchas**: Documented mistakes and their fixes
✅ **Integration Guide**: How patterns work with other skills
✅ **Template Examples**: Real examples from 2,653+ n8n templates

## Files

- **SKILL.md** (486 lines) - Pattern overview, selection guide, checklist
- **webhook_processing.md** (554 lines) - Webhook patterns, data structure, auth
- **http_api_integration.md** (763 lines) - REST APIs, pagination, rate limiting
- **database_operations.md** (854 lines) - DB operations, batch processing, security
- **ai_agent_workflow.md** (918 lines) - AI agents, tools, memory, 8 connection types
- **scheduled_tasks.md** (845 lines) - Cron schedules, timezone, monitoring
- **README.md** (this file) - Skill metadata

## Success Metrics

**Expected outcomes**:
- Users select appropriate pattern for their use case
- Workflows follow proven structural patterns
- Common gotchas avoided (webhook $json.body, SQL injection, etc.)
- Proper error handling implemented
- Security best practices followed

## Pattern Selection Stats

Common workflow composition:

**Trigger Distribution**:
- Webhook: 35% (most common)
- Schedule: 28%
- Manual: 22%
- Service triggers: 15%

**Transformation Nodes**:
- Set: 68%
- Code: 42%
- IF: 38%
- Switch: 18%

**Output Channels**:
- HTTP Request: 45%
- Slack: 32%
- Database: 28%
- Email: 24%

**Complexity**:
- Simple (3-5 nodes): 42%
- Medium (6-10 nodes): 38%
- Complex (11+ nodes): 20%

## Critical Insights

**Webhook Processing**:
- 813 searches (most common use case!)
- #1 gotcha: Data under $json.body (not $json directly)
- Must choose response mode: onReceived vs lastNode

**API Integration**:
- Authentication via credentials (never hardcode!)
- Pagination essential for large datasets
- Rate limiting prevents API bans
- continueOnFail: true for error handling

**Database Operations**:
- Always use parameterized queries (SQL injection prevention)
- Batch processing for large datasets
- Read-only access for AI tools
- Transaction handling for multi-step operations

**AI Agents**:
- 8 AI connection types (ai_languageModel, ai_tool, ai_memory, etc.)
- ANY node can be an AI tool (connect to ai_tool port)
- Memory essential for conversations (Window Buffer recommended)
- Tool descriptions critical (AI uses them to decide when to call)

**Scheduled Tasks**:
- Set workflow timezone explicitly (DST handling)
- Prevent overlapping executions (use locks)
- Error Trigger workflow for alerts
- Batch processing for large data

## Workflow Creation Checklist

Every pattern follows this checklist:

### Planning Phase
- [ ] Identify the pattern (webhook, API, database, AI, scheduled)
- [ ] List required nodes (use search_nodes)
- [ ] Understand data flow (input → transform → output)
- [ ] Plan error handling strategy

### Implementation Phase
- [ ] Create workflow with appropriate trigger
- [ ] Add data source nodes
- [ ] Configure authentication/credentials
- [ ] Add transformation nodes (Set, Code, IF)
- [ ] Add output/action nodes
- [ ] Configure error handling

### Validation Phase
- [ ] Validate each node configuration
- [ ] Validate complete workflow
- [ ] Test with sample data
- [ ] Handle edge cases

### Deployment Phase
- [ ] Review workflow settings
- [ ] Activate workflow
- [ ] Monitor first executions
- [ ] Document workflow

## Real Template Examples

**Weather to Slack** (Template #2947):
```
Schedule (daily 8 AM) → HTTP Request (weather) → Set → Slack
```

**Webhook Processing**: 1,085 templates
**HTTP API Integration**: 892 templates
**Database Operations**: 456 templates
**AI Workflows**: 234 templates

Use `search_templates` to find examples for your use case!

## Integration with Other Skills

**Pattern Selection** (this skill):
1. Identify use case
2. Select appropriate pattern
3. Follow pattern structure

**Node Discovery** (n8n MCP Tools Expert):
4. Find nodes for pattern (search_nodes)
5. Understand node operations (get_node)

**Implementation** (n8n Expression Syntax + Node Configuration):
6. Write expressions ({{$json.body.field}})
7. Configure nodes properly

**Validation** (n8n Validation Expert):
8. Validate workflow structure
9. Fix validation errors

## Last Updated

2025-10-20

---

**Part of**: n8n-skills repository
**Conceived by**: Romuald Członkowski - [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)
