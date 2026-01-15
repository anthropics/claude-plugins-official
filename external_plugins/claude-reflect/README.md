# claude-reflect

Self-learning system for Claude Code that captures corrections during sessions and syncs them to CLAUDE.md.

## What it does

When you correct Claude Code ("no, use gpt-5.1 not gpt-5", "remember: always use venv"), these corrections are captured automatically and can be reviewed with `/reflect` before being added to your CLAUDE.md files.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  You correct    │ ──► │  Hook captures  │ ──► │  /reflect adds  │
│  Claude Code    │     │  to queue       │     │  to CLAUDE.md   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      (automatic)            (automatic)            (manual review)
```

## Installation

```bash
/plugin install claude-reflect@claude-plugins-official
```

## Commands

| Command | Description |
|---------|-------------|
| `/reflect` | Process queued learnings with human review |
| `/reflect --scan-history` | Scan past sessions for missed learnings |
| `/reflect --dry-run` | Preview changes without applying |
| `/skip-reflect` | Discard all queued learnings |
| `/view-queue` | View pending learnings without processing |

## Features

- **Automatic capture**: Hooks detect correction patterns and queue them
- **Confidence scoring**: 0.60-0.90 based on pattern strength
- **Human review**: Nothing is written without your approval
- **Multi-target sync**: Updates CLAUDE.md and AGENTS.md (industry standard)
- **Historical scan**: Find corrections from past sessions

## Pattern Detection

**Corrections**: "no, use X", "don't use Y", "actually...", "use X not Y"

**Positive feedback**: "perfect!", "exactly right", "great approach"

**Explicit markers**: "remember:" (highest confidence)

## Links

- Repository: https://github.com/bayramannakov/claude-reflect
- Author: [Bayram Annakov](https://github.com/bayramannakov)
- License: MIT
