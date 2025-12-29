# Multi-Claude Parallel Orchestration Skill

## Overview

This skill enables parallel execution of complex plans using multiple Claude instances in Kitty terminal tabs.

## When to Use

- Complex tasks with 4+ independent subtasks
- Release preparations with multiple verification steps
- Large refactoring across multiple file domains
- Any plan created by `strategic-planner` agent

## Requirements

| Requirement | Details |
|-------------|---------|
| Terminal | **Kitty only** (not Warp/iTerm/Terminal.app) |
| Config | `allow_remote_control yes` in kitty.conf |
| Alias | `wildClaude='claude --dangerously-skip-permissions'` |
| Max Workers | 4 (hard limit) |

## Quick Start

```bash
# From Kitty:
./scripts/orchestration/kitty-check.sh    # Verify setup
./scripts/orchestration/claude-parallel.sh 4   # Launch workers
./scripts/orchestration/claude-monitor.sh      # Monitor
```

## Integration with Agents

### strategic-planner
The `strategic-planner` agent can create plans with Claude assignments and execute them in parallel:

```
@strategic-planner Create an execution plan for [task] with parallel execution
```

When asked "Vuoi eseguire in parallelo?", it will:
1. Verify Kitty environment
2. Launch Claude workers
3. Send tasks to each worker
4. Monitor progress
5. Report completion

## Plan Format

Plans for parallel execution must include:

```markdown
## 🎭 RUOLI CLAUDE

| Claude | Role | Tasks | Files |
|--------|------|-------|-------|
| CLAUDE 1 | Coordinator | Monitor | - |
| CLAUDE 2 | Implementer | T-01, T-02 | src/api/ |
| CLAUDE 3 | Implementer | T-03, T-04 | src/components/ |
| CLAUDE 4 | Implementer | T-05 | src/lib/ |
```

## Critical Rules

1. **NO FILE OVERLAP** - Avoid git conflicts
2. **MAX 4 WORKERS** - Beyond = chaos
3. **VERIFY LAST** - lint/typecheck/build at end
4. **GIT COORDINATION** - One commit at a time

## Scripts Location

```
scripts/orchestration/
├── README.md           # Full documentation
├── kitty-check.sh      # Verify setup
├── claude-parallel.sh  # Launch workers
└── claude-monitor.sh   # Monitor progress
```

## Related

- Agent: `.claude/agents/core_utility/strategic-planner.md`
- Global config: `~/.claude/commands/planner.md`
