# Misar Dev — Claude Code Plugin Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/MisarDev/misar-ai-plugins/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-7.6.0-green.svg)](https://github.com/MisarDev/misar-ai-plugins)
[![npx skills](https://img.shields.io/badge/npx%20skills-compatible-blue.svg)](https://skills.sh)

48-agent audit and optimization suite for Claude Code. 16 categories, 3D model routing, interactive flag prompting, and parallel agent dispatch. Works on Claude Code and 40+ AI agents via `npx skills`.

**Built by [Misar.Dev](https://misar.dev)** — Open-source tools for developers.

---

## Install

```bash
git clone https://github.com/MisarDev/misar-ai-plugins.git \
  ~/.claude/plugins/marketplaces/misar-ai-plugins
```

Or via `npx skills` (Cursor, Cline, Copilot, Windsurf):

```bash
npx skills add MisarDev/misar-ai-plugins
```

---

## Commands (16)

| Command | Description |
| ------- | ----------- |
| `/misar-dev:full-suite` | All 48 agents — 4-phase orchestrated audit |
| `/misar-dev:security` | Security hardening, penetration testing, data privacy |
| `/misar-dev:qa` | Code review, standards, bug detection, technical debt |
| `/misar-dev:uiux` | UI/UX audit — 8 dimensions, WCAG 2.2 AA |
| `/misar-dev:uiux-designer` | Design system, brand, component advisor |
| `/misar-dev:tester` | Unit, integration, E2E, beta, regression |
| `/misar-dev:compliance` | 49 global regulatory frameworks |
| `/misar-dev:marketing` | SEO, SXO, analytics, AI search optimization |
| `/misar-dev:brand` | Brand development, psychology, CRO, emotional design |
| `/misar-dev:product` | PM, designer, development, feature prioritization |
| `/misar-dev:content` | Grammar, copy, localization, documentation |
| `/misar-dev:seo-content-generator` | End-to-end SEO/AEO content pipeline |
| `/misar-dev:software-engineer` | PRD → plan → generate → validate |
| `/misar-dev:auditor` | Website audit — SEO, accessibility, performance, security |
| `/misar-dev:context-saver` | Manual 3D model router control |
| `/misar-dev:guidelines` | LLM coding behavioral guidelines |

Each command prompts interactively for flags before launching.

---

## 3D Model Router (Auto-Enabled)

Routes every task to the optimal `model × effort × version` via `SessionStart` hook:

| Task Type | Model | Effort |
| --------- | ----- | ------ |
| File reads, grep | haiku | low |
| Simple Q&A | haiku | medium |
| Code implementation | sonnet | medium |
| Code review, security | sonnet | high |
| Architecture, design | opus | high |
| Full-suite audit | opus | max |

Saves **90-97% context tokens** on lightweight tasks.

---

**Source**: [github.com/MisarDev/misar-ai-plugins](https://github.com/MisarDev/misar-ai-plugins) · **License**: MIT
