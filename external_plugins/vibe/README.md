# vibe

SPEC-driven AI coding framework for Claude Code.

## Features

- **12 Slash Commands**: `/vibe.spec`, `/vibe.run`, `/vibe.verify`, `/vibe.review`, and more
- **16 Specialist Agents**: Security, performance, architecture reviewers + language-specific reviewers
- **ULTRAWORK Pipeline**: Parallel execution with ~50% speed improvement
- **BDD Verification**: Behavior-driven development testing
- **Context7 Integration**: Up-to-date documentation lookup

## Quick Start

```bash
/plugin install vibe
```

Or for project-local installation:

```bash
npx @anthropic/claude-plugin-manager init vibe
```

## Commands

| Command | Description |
|---------|-------------|
| `/vibe.spec "feature"` | Create SPEC document with parallel research |
| `/vibe.run "feature"` | Execute implementation with ULTRAWORK pipeline |
| `/vibe.verify "feature"` | Verify against SPEC requirements |
| `/vibe.review` | Parallel code review with 13+ specialist agents |
| `/vibe.reason "problem"` | Systematic reasoning framework |
| `/vibe.diagram` | Generate architecture diagrams |

## ULTRAWORK Mode

Add `ultrawork` or `ulw` for maximum performance:

```bash
/vibe.run "login feature" ultrawork
```

Enables:
- Parallel subagent exploration (3+ concurrent)
- Background agents during implementation
- Phase pipelining
- Auto-retry on errors

## Links

- [Repository](https://github.com/su-record/vibe)
- [Documentation](https://github.com/su-record/vibe#readme)

## License

MIT
