# Neko Gundan

Multi-agent orchestration framework for Claude Code that organizes agents into a hierarchical team with structured quality assurance.

## Overview

Neko Gundan ("Cat Squad") turns Claude Code into a coordinated development team with clear roles, communication protocols, and quality gates.

```
Commander (Human)
    |
Oyakata-neko (General / Opus) --- Strategy & delegation
    |
Shigoto-neko (Manager / Sonnet) --- Task decomposition & QA
    |
Genba-neko (Worker / Sonnet) --- Implementation
    |
Kurouto-neko (Specialist / Opus) --- Independent review
```

## Features

- **Auto-scaling**: Recon (single agent) to Battalion (full team) based on task complexity
- **Bidirectional objection protocols**: Lower-level agents can challenge incorrect instructions
- **Evidence-based completion gates**: Mandatory checkpoints with recorded proof before declaring "done"
- **Review loop protocol**: Implementer != Reviewer, read-only review, max 3 cycles
- **Whiteboard system**: Cross-agent knowledge sharing with objection visibility
- **Safety measures**: File deletion buffer, race condition prevention, trust level tagging (FIDES)

## Contents

| Component | Description |
|-----------|-------------|
| `agents/oyakata-neko.md` | General - strategy & delegation |
| `agents/shigoto-neko.md` | Manager - task decomposition & QA |
| `agents/genba-neko.md` | Worker - implementation |
| `agents/kurouto-neko.md` | Specialist - independent review |
| `commands/neko-gundan.md` | Team deployment command |
| `rules/review-protocol.md` | Review loop protocol |
| `rules/handoff-schema.md` | Agent handoff data schema |
| `rules/completion-gates.md` | Start/completion gate definitions |
| `rules/spec-driven-review.md` | Spec-driven review process |

## Usage

After installing the plugin, Claude Code operates as "Oyakata-neko" and automatically scales the team based on task complexity.

For the full repository with documentation and examples, see: https://github.com/aliksir/neko-gundan

## License

MIT License
