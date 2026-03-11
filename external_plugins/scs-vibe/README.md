# SCS Vibe

> Stop Claude from coding you into corners. In 15 minutes.

You're vibe coding — moving fast, building something cool. But Claude doesn't know your project. Without context, it makes confident decisions that conflict with choices you made last week, don't fit the patterns you've established, and require rework to integrate.

SCS Vibe is a quick, conversational setup. Answer a few questions and Claude gets enough context to work WITH your system instead of against it.

## Installation

```bash
/plugin install scs-vibe@claude-plugin-directory
```

## Commands

- `/scs-vibe:init` — Interactive wizard that scans your project and generates a structured CLAUDE.md
- `/scs-vibe:validate` — Check your existing context for missing sections, stale references, and gaps
- `/scs-vibe:explain` — Learn why structured context matters

## Templates

| Template | Use Case |
|----------|----------|
| `minimal` | Small projects, quick start |
| `saas` | Standard SaaS applications |
| `healthcare` | HIPAA considerations (PHI, audit logging) |
| `fintech` | Financial services (SOC2, transactions) |

## Links

- Documentation: https://structuredcontext.dev
- GitHub: https://github.com/tim-mccrimmon/scs-vibe
- For Teams: https://github.com/tim-mccrimmon/scs-team
