<div align="center">

# MyConvergio - Claude Code Plugin

<img src="./CovergioLogoTransparent.png" alt="Convergio Logo" width="200"/>

**v3.0.0** | 57 Specialized Agents | Claude Code Plugin for Marketplace

> *"Intent is human, momentum is agent"*
> — [The Agentic Manifesto](./AgenticManifesto.md)

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

</div>

---

## What's New in v3.0.0

**MyConvergio is now a Claude Code Plugin!**

- **Marketplace Ready**: Install directly from Claude Code plugin system
- **57 Specialized Agents**: Enterprise-grade AI assistants for every domain
- **3 Slash Commands**: `/myconvergio:status`, `/myconvergio:team`, `/myconvergio:plan`
- **9 Reusable Skills**: Architecture, debugging, code review, and more
- **Constitution-Based Security**: 8 articles protecting all agents

---

## Quick Start

### Installation

**From Claude Code:**
```bash
# Install the plugin
claude plugins install myconvergio

# Or clone and install locally
git clone https://github.com/roberdan/MyConvergio.git
cd MyConvergio
claude --plugin-dir .
```

### Usage

**Invoke any agent:**
```bash
@ali-chief-of-staff Help me design our global expansion strategy
@baccio-tech-architect Design microservices architecture for healthcare platform
@rex-code-reviewer Review this pull request for security issues
```

**Use slash commands:**
```bash
/myconvergio:status    # Show ecosystem status
/myconvergio:team      # List all 57 agents by category
/myconvergio:plan      # Create a strategic execution plan
```

---

## Agent Portfolio (57 Specialists)

### Leadership & Strategy (7)
| Agent | Description |
|-------|-------------|
| `ali-chief-of-staff` | Master orchestrator for complex multi-domain challenges |
| `satya-board-of-directors` | Board-level strategic advisor |
| `domik-mckinsey-strategic-decision-maker` | McKinsey Partner-level strategic decisions |
| `antonio-strategy-expert` | Strategy frameworks (OKR, Lean, Agile) |
| `amy-cfo` | Chief Financial Officer for financial strategy |
| `dan-engineering-gm` | Engineering General Manager |
| `matteo-strategic-business-architect` | Business strategy architect |

### Technical Development (7)
| Agent | Description |
|-------|-------------|
| `baccio-tech-architect` | Elite Technology Architect for system design |
| `marco-devops-engineer` | DevOps for CI/CD and infrastructure |
| `dario-debugger` | Systematic debugging expert |
| `rex-code-reviewer` | Code review specialist |
| `otto-performance-optimizer` | Performance optimization |
| `paolo-best-practices-enforcer` | Coding standards enforcer |
| `omri-data-scientist` | Data Scientist for ML and AI |

### Business Operations (11)
| Agent | Description |
|-------|-------------|
| `davide-project-manager` | Project Manager (Agile, Scrum, Waterfall) |
| `marcello-pm` | Product Manager for strategy and roadmaps |
| `oliver-pm` | Senior Product Manager |
| `luke-program-manager` | Program Manager for portfolios |
| `anna-executive-assistant` | Executive Assistant with task management |
| `andrea-customer-success-manager` | Customer Success Manager |
| `fabio-sales-business-development` | Sales & Business Development |
| `sofia-marketing-strategist` | Marketing Strategist |
| `steve-executive-communication-strategist` | Executive Communication |
| `enrico-business-process-engineer` | Business Process Engineer |
| `dave-change-management-specialist` | Change Management specialist |

### Design & UX (3)
| Agent | Description |
|-------|-------------|
| `jony-creative-director` | Creative Director for brand innovation |
| `sara-ux-ui-designer` | UX/UI Designer |
| `stefano-design-thinking-facilitator` | Design Thinking facilitator |

### Compliance & Legal (5)
| Agent | Description |
|-------|-------------|
| `elena-legal-compliance-expert` | Legal & Compliance expert |
| `luca-security-expert` | Cybersecurity expert |
| `dr-enzo-healthcare-compliance-manager` | Healthcare Compliance (HIPAA, FDA) |
| `sophia-govaffairs` | Government Affairs specialist |
| `guardian-ai-security-validator` | AI Security validator |

### Specialized Experts (13)
| Agent | Description |
|-------|-------------|
| `behice-cultural-coach` | Cultural intelligence expert |
| `fiona-market-analyst` | Market Analyst for financial research |
| `michael-vc` | Venture Capital analyst |
| `angela-da` | Senior Decision Architect |
| `ethan-da` | Data Analytics specialist |
| `evan-ic6da` | Principal Decision Architect (IC6) |
| `ava-analytics-insights-virtuoso` | Analytics virtuoso |
| `riccardo-storyteller` | Narrative designer |
| `jenny-inclusive-accessibility-champion` | Accessibility champion |
| `giulia-hr-talent-acquisition` | HR & Talent Acquisition |
| `sam-startupper` | Silicon Valley startup expert |
| `wiz-investor-venture-capital` | Venture Capital investor |
| `coach-team-coach` | Team Coach |

### Core Utility (9)
| Agent | Description |
|-------|-------------|
| `marcus-context-memory-keeper` | Institutional memory guardian |
| `thor-quality-assurance-guardian` | Quality watchdog |
| `diana-performance-dashboard` | Performance dashboard specialist |
| `socrates-first-principles-reasoning` | First principles reasoning master |
| `strategic-planner` | Wave-based execution plan creator |
| `taskmaster-strategic-task-decomposition-master` | Task decomposition expert |
| `po-prompt-optimizer` | Prompt engineering expert |
| `wanda-workflow-orchestrator` | Workflow orchestrator |
| `xavier-coordination-patterns` | Coordination patterns architect |

### Release Management (2)
| Agent | Description |
|-------|-------------|
| `app-release-manager` | Release engineering with quality gates |
| `feature-release-manager` | Feature completion and issue closure |

---

## Plugin Structure

```
MyConvergio/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── agents/                    # 57 specialized agents
│   ├── ali-chief-of-staff.md
│   ├── baccio-tech-architect.md
│   └── ...
├── commands/                  # 3 slash commands
│   ├── status.md
│   ├── team.md
│   └── plan.md
├── hooks/
│   └── hooks.json
├── skills/                    # 9 reusable workflows
│   ├── architecture/
│   ├── code-review/
│   ├── debugging/
│   ├── performance/
│   ├── security-audit/
│   ├── strategic-analysis/
│   ├── release-management/
│   ├── project-management/
│   └── orchestration/
└── .claude/
    └── rules/                 # 6 coding rules
```

---

## Skills

Reusable workflows you can reference in your projects:

| Skill | Use Case |
|-------|----------|
| `code-review` | Systematic code review process |
| `debugging` | Root cause analysis methodology |
| `architecture` | System design patterns |
| `security-audit` | Security assessment framework |
| `performance` | Performance optimization |
| `strategic-analysis` | McKinsey-style analysis |
| `release-management` | Release engineering |
| `project-management` | Agile/Scrum workflows |
| `orchestration` | Multi-agent coordination |

---

## Rules

Copy these to your project's `.claude/rules/` for consistent standards:

- `code-style.md` - ESLint, Prettier, PEP8
- `security-requirements.md` - OWASP Top 10
- `testing-standards.md` - Unit, integration, coverage
- `documentation-standards.md` - JSDoc, README, ADRs
- `api-development.md` - REST, versioning
- `ethical-guidelines.md` - Privacy, accessibility

---

## Security Framework

All agents implement the [MyConvergio Constitution](./agents/CONSTITUTION.md):

| Article | Protection |
|---------|------------|
| I | Identity Lock - Immutable agent identity |
| II | Ethical Principles - Fairness, transparency, accountability |
| III | Security Directives - Anti-hijacking, input validation |
| IV | Operational Boundaries - Role adherence |
| V | Failure Modes - Graceful degradation |
| VI | Collaboration - Safe inter-agent communication |
| VII | **Accessibility & Inclusion (NON-NEGOTIABLE)** |
| VIII | Accountability - Logging and audit trails |

---

## The Agentic Manifesto

*Human purpose. AI momentum.*

### What we believe
1. **Intent is human, momentum is agent.**
2. **Impact must reach every mind and body.**
3. **Trust grows from transparent provenance.**
4. **Progress is judged by outcomes, not output.**

### How we act
1. Humans stay accountable for decisions and effects.
2. Agents amplify capability, never identity.
3. We design from the edge first: disability, language, connectivity.
4. Safety rails precede scale.
5. Learn in small loops, ship value early.

*Read the full [Agentic Manifesto](./AgenticManifesto.md)*

---

## Migration from npm Package

If upgrading from v2.x (npm package):

```bash
# Uninstall npm version
npm uninstall -g myconvergio

# Install plugin version
claude plugins install myconvergio
```

---

## License & Legal

Copyright 2025 Convergio.io

Licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](./LICENSE)

### Disclaimers

- **Experimental Software**: Provided "AS IS" without warranties
- **Non-Commercial Use Only**: See LICENSE file for details
- **No Corporate Affiliation**: Not affiliated with Anthropic, OpenAI, or Microsoft
- **Personal Project**: Author is a Microsoft employee; this is a personal initiative

**Author Note**: Roberto D'Angelo is a Microsoft employee. This project is a personal initiative created independently during personal time. This project is NOT affiliated with, endorsed by, or representing Microsoft Corporation.

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

For questions about commercial licensing: roberdan@fightthestroke.org

---

<div align="center">

*Built with AI assistance in Milano, following the Agentic Manifesto principles*

**v3.0.0** | December 2025 | Claude Code Plugin

</div>
