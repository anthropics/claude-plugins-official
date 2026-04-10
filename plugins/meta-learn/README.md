# meta-learn

An AI-powered interactive learning coach that helps you master any topic 10x faster.

## What it does

Instead of answering questions like a search engine, meta-learn acts as a Socratic sparring partner. It:

- Builds a **knowledge skeleton** (3-layer map: core / important / advanced) before diving into details
- Creates a **personalized learning path** based on your baseline, goal, time budget, and deadline
- Offers 5 interactive learning modes you can switch between anytime:
  - **[拆] Deep Dive** — first-principles explanation with analogies
  - **[练] Feynman Sparring** — you explain, AI probes until you truly understand
  - **[查] Socratic Drill** — causal "why" chains, not just facts
  - **[改] Instant Feedback** — specific critique on your notes/work
  - **[融] Cross-Domain Transfer** — connect new knowledge to what you already know
- Supports **Chinese and English** (auto-detects and matches your language)

## When to use

Say things like:
- "我想学Python，零基础，每天1小时，1个月内能写简单脚本"
- "I want to understand transformer architecture — I know basic ML but not NLP"
- "我刚学完复利，你来考考我"
- "帮我快速了解区块链，能跟人聊天时不露怯就行"

## Installation

### Claude Code
```bash
/plugin install meta-learn
```

### Manual
Copy the `skill/` directory into your Claude skills folder:
```
~/.claude/skills/meta-learn/
```

## Platform support

| Platform | Status | Config file | Install |
|----------|--------|-------------|---------|
| Claude Code | ✅ | `.claude-plugin/plugin.json` | `/plugin install meta-learn` |
| ClawHub (OpenClaw) | ✅ | `skill/SKILL.md` | `npx clawhub@latest install meta-learn` |
| Friday Skills Hub | ✅ | `skill/SKILL.md` frontmatter | `friday-skill install meta-learn` |
| Cursor | ✅ | `platform/cursor-plugin.json` | Cursor marketplace |
| Gemini CLI | ✅ | `platform/gemini-extension.json` | Manual |
| agentskills.io | ✅ | `skill/SKILL.md` | 待确认 |

## Repository structure

```
meta-learn/
├── skill/                    # The skill itself (what gets installed)
│   ├── SKILL.md              # Core skill definition — all platforms
│   └── references/           # Optional reference docs
├── .claude-plugin/
│   └── plugin.json           # Claude Code marketplace manifest
├── platform/                 # Platform-specific adapters
│   ├── cursor-plugin.json
│   └── gemini-extension.json
├── evals/                    # Development & testing (not distributed)
│   ├── evals.json
│   └── workspace/
├── CHANGELOG.md
└── README.md
```

## Contributing

PRs welcome. When modifying the skill:
1. Edit `skill/SKILL.md`
2. Run evals: `python evals/workspace/run_desc_optimizer.py`
3. Update `CHANGELOG.md`
4. Bump `version` in `skill/SKILL.md` and `.claude-plugin/plugin.json`

## License

MIT
