# PACT Framework Plugin

**Prepare, Architect, Code, Test** - A systematic methodology for AI-assisted software development using specialized agents.

## Overview

PACT is a multi-agent framework that breaks down software development into four distinct phases, each handled by specialized agents. This ensures thorough preparation, sound architecture, quality code, and comprehensive testing.

## Installation

```bash
claude plugin install pact-framework@claude-plugins-official
```

Or via the Discover menu:
```
/plugin > Discover > pact-framework
```

## Commands

| Command | Description |
|---------|-------------|
| `/pact-framework:orchestrate` | Full PACT workflow with all specialist agents |
| `/pact-framework:comPACT` | Lightweight single-specialist mode for simpler tasks |
| `/pact-framework:peer-review` | Multi-agent code review before merge |
| `/pact-framework:plan-mode` | Multi-agent planning consultation |
| `/pact-framework:imPACT` | Triage when hitting blockers |
| `/pact-framework:wrap-up` | End-of-session cleanup and documentation |
| `/pact-framework:log-changes` | Update project documentation with recent changes |

## Specialist Agents

### Phase 1: Prepare
- **pact-preparer**: Research, documentation gathering, requirements analysis

### Phase 2: Architect
- **pact-architect**: System design, component planning, interface definition

### Phase 3: Code
- **pact-backend-coder**: Server-side implementation, APIs, business logic
- **pact-frontend-coder**: Client-side implementation, UI components
- **pact-database-engineer**: Schema design, queries, migrations
- **pact-n8n**: n8n workflow automation (requires n8n-mcp server)

### Phase 4: Test
- **pact-test-engineer**: Unit, integration, E2E, and security testing

## Skills

The plugin includes 14 skills that auto-activate based on context:

**PACT Core Skills:**
- `pact-prepare-research` - Research and documentation patterns
- `pact-architecture-patterns` - C4 diagrams, design patterns, anti-patterns
- `pact-coding-standards` - Clean code principles, error handling
- `pact-security-patterns` - OWASP mitigations, authentication patterns
- `pact-testing-strategies` - Test pyramid, integration patterns

**n8n Workflow Skills:**
- `n8n-workflow-patterns` - Common workflow architectures
- `n8n-code-javascript` - Code node JavaScript patterns
- `n8n-code-python` - Code node Python patterns
- `n8n-expression-syntax` - n8n expression language
- `n8n-node-configuration` - Node setup and dependencies
- `n8n-validation-expert` - Error diagnosis and fixes
- `n8n-mcp-tools-expert` - MCP server integration

**Context Engineering Skills:**
- `context-compression` - Session summarization techniques
- `filesystem-context` - File-based context management

## Hooks

The plugin includes hooks that enforce PACT protocols:

- **SessionStart**: Detects active plans and notifies user
- **PreToolUse (git commit)**: Validates security rules (no secrets, proper documentation)
- **SubagentStop**: Validates proper handoff format between agents
- **Stop**: Reminds about decision logs and testing

## Security Features

PACT enforces **SACROSANCT security rules**:

1. **No credentials in code**: Blocks commits containing API keys, tokens, or secrets
2. **Backend proxy pattern**: Warns about frontend credential exposure
3. **Environment protection**: Validates .env files are gitignored

## Usage Example

```
User: Build a user authentication system with JWT tokens

Claude: I'll use /pact-framework:orchestrate to systematically build this feature.

[PREPARE Phase]
- pact-preparer researches JWT best practices, security requirements

[ARCHITECT Phase]
- pact-architect designs auth flow, token structure, API contracts

[CODE Phase]
- pact-backend-coder implements auth endpoints, middleware
- pact-database-engineer creates user schema, session storage

[TEST Phase]
- pact-test-engineer writes security tests, integration tests
```

## Requirements

- Claude Code CLI
- Git (for commit hooks)
- Python 3 (for hooks)
- Optional: n8n-mcp server (for n8n workflows)

## Documentation

- [PACT Framework Guide](https://github.com/ProfSynapse/PACT-prompt)
- [Agent Protocols](./protocols/pact-protocols.md)

## License

MIT License - See [LICENSE](https://github.com/ProfSynapse/PACT-prompt/blob/main/LICENSE)

## Author

**ProfSynapse** - [GitHub](https://github.com/ProfSynapse)
