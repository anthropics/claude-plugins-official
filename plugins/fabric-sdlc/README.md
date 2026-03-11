# fabric-sdlc

**The Fabric** — an autonomous SDLC agent team for Claude Code that transforms a business objective into a working application.

## What it does

Give it a business objective. It orchestrates 8 specialist AI agents through a complete software development lifecycle:

1. **Requirements Analysis** — Business analyst produces requirements and user stories
2. **Architecture & UX Design** — Architect and UX engineer work in parallel on system design and UI specs
3. **Implementation** — Lead developer builds the application (with parallel sub-agents for independent modules)
4. **Testing & Security Review** — QA and security engineers review in parallel
5. **Bug Fix Loop** — Critical/high issues get fixed and re-tested (up to 3 iterations)
6. **Deployment Setup** — DevOps engineer creates Dockerfiles, CI/CD, and deployment docs
7. **Documentation** — Technical writer produces README, user guide, and API docs

Every decision is documented. Every requirement is traceable through design, implementation, and testing.

## Requirements

- Claude Code with **Agent Teams** enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`)
- Recommended: Claude Opus for best results with complex orchestration

## Usage

```
/fabric Build me a task management API with user authentication and team workspaces
```

Or just type `/fabric` and it will ask you what to build.

## What you get

After execution, your current directory will contain:

```
./
├── docs/
│   ├── 00-project-charter.md      # Business objective and scope
│   ├── 00-progress-log.md         # Full audit trail
│   ├── 01-requirements.md         # Requirements with IDs
│   ├── 01-user-stories.md         # User stories with acceptance criteria
│   ├── 02-architecture.md         # System architecture and ADRs
│   ├── 02-tech-stack.md           # Technology selections
│   ├── 02-api-contracts.md        # API specifications
│   ├── 02b-wireframes.md          # ASCII wireframes
│   ├── 02b-ui-spec.md             # UI specifications
│   ├── 02b-design-system.md       # Design system
│   ├── 03-implementation-log.md   # What was built and why
│   ├── 04-test-plan.md            # Test strategy
│   ├── 04-test-results.md         # Test execution results
│   ├── 04b-threat-model.md        # STRIDE threat model
│   ├── 04b-security-review.md     # Security findings
│   ├── 05-deployment.md           # Deployment guide
│   ├── 06-user-guide.md           # End-user documentation
│   └── 06-api-docs.md             # API documentation
├── src/                            # Application source code
├── tests/                          # Test suite
├── infra/                          # Dockerfile, CI/CD, docker-compose
└── README.md                       # Project README
```

## The Team

| Agent | Role |
|-------|------|
| `fabric-pm` | Project Manager (orchestrator) |
| `fabric-ba` | Business Analyst |
| `fabric-architect` | Solution Architect |
| `fabric-ux` | UX/UI Engineer |
| `fabric-dev-lead` | Lead Developer |
| `fabric-qa` | QA Engineer |
| `fabric-security` | Security Engineer |
| `fabric-devops` | DevOps Engineer |
| `fabric-docs` | Technical Writer |

## License

MIT
