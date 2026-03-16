---
name: command-development
description: This skill should be used when the user asks to "create a slash command", "add a command", "write a custom command", "define command arguments", "use command frontmatter", "organize commands", "create command with file references", "interactive command", "use AskUserQuestion in command", or needs guidance on slash command structure, YAML frontmatter fields, dynamic arguments, bash execution in commands, user interaction patterns, or command development best practices for Claude Code.
version: 0.2.0
---

# Command Development for Claude Code

## Overview

Slash commands are frequently-used prompts defined as Markdown files that Claude executes during interactive sessions. Understanding command structure, frontmatter options, and dynamic features enables creating powerful, reusable workflows.

**Key concepts:**
- Markdown file format for commands
- YAML frontmatter for configuration
- Dynamic arguments and file references
- Bash execution for context
- Command organization and namespacing

## Command Basics

### What is a Slash Command?

A slash command is a Markdown file containing a prompt that Claude executes when invoked. Commands provide:
- **Reusability**: Define once, use repeatedly
- **Consistency**: Standardize common workflows
- **Sharing**: Distribute across team or projects
- **Efficiency**: Quick access to complex prompts

### Critical: Commands are Instructions FOR Claude

**Commands are written for agent consumption, not human consumption.**

When a user invokes `/command-name`, the command content becomes Claude's instructions. Write commands as directives TO Claude about what to do, not as messages TO the user.

**Correct approach (instructions for Claude):**
```markdown
Review this code for security vulnerabilities including:
- SQL injection
- XSS attacks
- Authentication issues

Provide specific line numbers and severity ratings.
```

**Incorrect approach (messages to user):**
```markdown
This command will review your code for security issues.
You'll receive a report with vulnerability details.
```

### Command Locations

**Project commands** (shared with team):
- Location: `.claude/commands/`
- Scope: Available in specific project
- Label: Shown as "(project)" in `/help`

**Personal commands** (available everywhere):
- Location: `~/.claude/commands/`
- Scope: Available in all projects
- Label: Shown as "(user)" in `/help`

**Plugin commands** (bundled with plugins):
- Location: `plugin-name/commands/`
- Scope: Available when plugin installed
- Label: Shown as "(plugin-name)" in `/help`

## File Format

Commands are Markdown files with `.md` extension. No frontmatter needed for basic commands:

```markdown
Review this code for security vulnerabilities including:
- SQL injection
- XSS attacks
- Authentication bypass
```

Add configuration using YAML frontmatter when needed:

```markdown
---
description: Review code for security issues
allowed-tools: Read, Grep, Bash(git:*)
model: sonnet
---

Review this code for security vulnerabilities...
```

For the complete frontmatter field specification, see [references/frontmatter-reference.md](references/frontmatter-reference.md).

## YAML Frontmatter Quick Reference

| Field | Type | Purpose |
|-------|------|---------|
| `description` | String | Brief description shown in `/help` (under 60 chars) |
| `allowed-tools` | String/Array | Tools the command can use (e.g., `Read, Bash(git:*)`) |
| `model` | String | Model override: `haiku`, `sonnet`, or `opus` |
| `argument-hint` | String | Documents expected arguments for autocomplete |
| `disable-model-invocation` | Boolean | Prevent programmatic invocation (default: false) |

## Dynamic Arguments

### $ARGUMENTS (all arguments as single string)

```markdown
---
argument-hint: [issue-number]
---
Fix issue #$ARGUMENTS following our coding standards.
```

Usage: `/fix-issue 123` expands to `Fix issue #123 following our coding standards.`

### Positional Arguments ($1, $2, $3...)

```markdown
---
argument-hint: [pr-number] [priority] [assignee]
---
Review pull request #$1 with priority level $2.
After review, assign to $3 for follow-up.
```

Usage: `/review-pr 123 high alice`

## File References

Include file contents using `@` syntax:

```markdown
Review @$1 for code quality and potential bugs.
```

Usage: `/review-file src/api/users.ts` — Claude reads the file before processing.

Static references also work: `Review @package.json and @tsconfig.json for consistency.`

## Bash Execution

Commands can execute bash inline to gather dynamic context. For complete syntax and examples, see [references/plugin-features-reference.md](references/plugin-features-reference.md).

## Command Organization

**Flat** (5-15 commands): All files in `.claude/commands/`

**Namespaced** (15+ commands): Use subdirectories:
```
.claude/commands/
├── ci/
│   ├── build.md        # /build (project:ci)
│   └── test.md         # /test (project:ci)
└── git/
    ├── commit.md       # /commit (project:git)
    └── pr.md           # /pr (project:git)
```

## Common Patterns

### Review Pattern
```markdown
---
description: Review code changes
allowed-tools: Read, Bash(git:*)
---
Files changed: !`git diff --name-only`
Review each file for code quality, bugs, test coverage, and documentation needs.
```

### Testing Pattern
```markdown
---
description: Run tests for specific file
argument-hint: [test-file]
allowed-tools: Bash(npm:*)
---
Run tests: !`npm test $1`
Analyze results and suggest fixes for failures.
```

### Documentation Pattern
```markdown
---
description: Generate documentation for file
argument-hint: [source-file]
---
Generate comprehensive documentation for @$1 including function descriptions,
parameters, return values, usage examples, and edge cases.
```

## Best Practices

1. **Single responsibility:** One command, one task
2. **Clear descriptions:** Self-explanatory in `/help`
3. **Document arguments:** Always provide `argument-hint`
4. **Limit tool scope:** Use `Bash(git:*)` not `Bash(*)`
5. **Consistent naming:** verb-noun pattern (`review-pr`, `fix-issue`)
6. **Validate inputs:** Check for required arguments and file existence

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Command not appearing | Check `.md` extension, correct directory, restart Claude Code |
| Arguments not working | Verify `$1`/`$2` syntax, check `argument-hint` |
| Bash execution failing | Ensure `allowed-tools` includes Bash, test command in terminal |
| File references not working | Verify `@` syntax, check path, ensure Read tool allowed |

---

**Additional resources:**
- Frontmatter field details: [references/frontmatter-reference.md](references/frontmatter-reference.md)
- Plugin-specific patterns (CLAUDE_PLUGIN_ROOT, agent/skill integration, validation): [references/plugin-command-patterns.md](references/plugin-command-patterns.md)
- Plugin features and bash syntax: [references/plugin-features-reference.md](references/plugin-features-reference.md)
- Interactive command patterns: [references/interactive-commands.md](references/interactive-commands.md)
- Command examples: [examples/](examples/)
