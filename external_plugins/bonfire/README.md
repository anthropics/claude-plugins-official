# Bonfire

<p align="center">
  <img src="bonfire.png" alt="Bonfire" width="200">
</p>

Your AI coding partner forgets everything between conversations. Bonfire fixes that.

```bash
claude plugin marketplace add vieko/bonfire
claude plugin install bonfire@vieko
```

## The Problem

AI agents are stateless. Every conversation starts from zero. The agent doesn't remember:

- What you decided yesterday
- Why you chose that architecture
- What blockers you hit
- Where you left off

You end up re-explaining context, re-making decisions, and watching your AI partner repeat the same mistakes.

## The Solution

Bonfire maintains a living context document that gets read at session start and updated at session end. Your AI partner picks up exactly where you left off. It's like a saved game for your work.

`/bonfire:start` → *reads context* → WORK → `/bonfire:end` → *saves context*

That's it. No complex setup. No external services. Just Markdown files in your repo.

## Not a Task Tracker

| Tool | Primary Question |
|------|------------------|
| Issue/task trackers | "What's the work?" |
| Bonfire | "Where are we and what did we decide?" |

Bonfire complements your issue tracker. Use GitHub Issues, Linear, Beads, or Beans for tasks. Use Bonfire for workflow context.

## Quick Start

```bash
# Install
claude plugin marketplace add vieko/bonfire
claude plugin install bonfire@vieko

# First run scaffolds .bonfire/ and asks setup questions
/bonfire:start
```

## Commands

| Command | What it does |
|---------|--------------|
| `/bonfire:start` | Read context, scaffold on first run |
| `/bonfire:end` | Update context, commit changes |
| `/bonfire:spec <topic>` | Create implementation spec (researches codebase, interviews you) |
| `/bonfire:document <topic>` | Document a codebase topic |
| `/bonfire:review` | Find blindspots, gaps, and quick wins |
| `/bonfire:archive` | Archive completed work |
| `/bonfire:configure` | Change project settings |

## What Gets Created

```
.bonfire/
├── index.md      # Living context (the important one)
├── config.json   # Your settings
├── archive/      # Completed work history
├── specs/        # Implementation specs
├── docs/         # Topic documentation
└── scripts/      # Temporary session scripts
```

The `index.md` is where the magic happens. It tracks:

- Current state and branch
- Recent session summaries
- Decisions made and why
- Blockers encountered
- Next priorities

## Context-Efficient Operations

Heavy commands (`/spec`, `/document`, `/review`) use subagents to avoid burning your main conversation context:

- Research runs in isolated context (fast, cheap)
- Only structured summaries return to main conversation
- Result: longer sessions without context exhaustion

This happens automatically.

## Configuration

First `/bonfire:start` asks you to configure:

| Setting | Options |
|---------|---------|
| Specs location | `.bonfire/specs/` or `specs/` |
| Docs location | `.bonfire/docs/` or `docs/` |
| Git strategy | ignore-all, hybrid, commit-all |
| Linear integration | Yes or No |

Change anytime with `/bonfire:configure`.

### Git Strategies

| Strategy | What's tracked | Best for |
|----------|---------------|----------|
| **ignore-all** | Nothing | Solo work, privacy |
| **hybrid** | docs/, specs/ only | Teams wanting shared docs |
| **commit-all** | Everything | Full transparency |

## Linear Integration

If you use Linear for issue tracking:

1. Install [Linear MCP](https://github.com/anthropics/anthropic-quickstarts/tree/main/mcp-linear)
2. Enable via `/bonfire:configure`
3. Reference issues by ID: `ENG-123`

Bonfire will fetch issue context on start, create issues from review findings, and mark issues Done on archive.

## Proactive Skills

Claude automatically reads your session context when you ask things like:
- "What's the project status?"
- "What were we working on?"
- "What decisions have we made?"

And suggests archiving when you merge PRs or mention shipping.

## Requirements

- [Claude Code CLI](https://claude.ai/code)
- Git repository

Optional: `gh` CLI for GitHub integration, Linear MCP for Linear integration.

## Learn More

**Blog post**: [Save Your Progress](https://vieko.dev/bonfire)

**Changelog**: [CHANGELOG.md](CHANGELOG.md)

## License

MIT © [Vieko Franetovic](https://vieko.dev)
