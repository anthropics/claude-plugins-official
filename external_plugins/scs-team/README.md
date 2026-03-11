# SCS Team

> Transform your documentation into context Claude actually uses.

Your team has PRDs, architecture docs, security requirements, compliance checklists. Claude doesn't know any of it. SCS Team takes your existing documentation and transforms it into structured context — so Claude gets the full picture before it writes a single line of code.

**Dual-layer output**: maintains structured source (`.scs/`) AND compiled Claude Code rules (`.claude/rules/`). Edit the source, compilation keeps Claude in sync.

## Installation

```bash
/plugin install scs-team@claude-plugin-directory
```

## Commands

- `/scs-team:init` — Scaffold `.scs/` with all 11 concern bundles
- `/scs-team:add <file>` — Process an existing doc into structured context
- `/scs-team:use <standard>` — Add HIPAA, SOC2, PCI DSS, CHAI, or GDPR standards from the bundled library
- `/scs-team:draft <concern>` — Conversational drafting when you don't have docs yet
- `/scs-team:status` — See coverage across all 11 concerns
- `/scs-team:validate` — Five-level structure and content check
- `/scs-team:version` — Semantic versioning with git integration

## Bundled Standards Library

HIPAA · SOC 2 · PCI DSS · CHAI · GDPR — pre-built, concrete requirements ready to copy into your project.

## Links

- Documentation: https://structuredcontext.dev
- GitHub: https://github.com/tim-mccrimmon/scs-team
- For Solo Devs: https://github.com/tim-mccrimmon/scs-vibe
