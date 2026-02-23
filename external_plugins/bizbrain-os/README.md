# BizBrain OS

[BizBrain OS](https://github.com/TechIntegrationLabs/bizbrain-os-plugin) is a Claude Code plugin that builds a persistent knowledge brain from your actual work. Install it once, and Claude Code learns your projects, clients, tools, and preferences — compounding knowledge across every session.

## Setup

### 1. Install the Plugin

```bash
claude plugin install bizbrain-os@claude-plugin-directory
```

### 2. Run First-Time Setup

```
/brain setup
```

This scans your machine, discovers projects and services, lets you pick a profile, and creates your brain folder at `~/bizbrain-os/`.

### 3. Restart Claude Code

Your brain context will be automatically injected into every future session.

## Available Commands

| Command | Description |
|---------|-------------|
| `/brain` | Brain status, scan, configure, and profile management |
| `/brain setup` | First-time setup: scan machine, pick profile, create brain |
| `/knowledge <topic>` | Load specific knowledge from the brain |
| `/todo` | View and manage tasks across all sources |
| `/entity <name>` | Look up or add a client, partner, vendor, or contact |
| `/hours` | Time tracking summary |
| `/gsd` | Structured project execution workflow |
| `/intake` | Process files dropped into the intake folder |
| `/mcp` | MCP server management |

## Skills

- **Brain Bootstrap** — Machine scanning, profile selection, brain creation
- **Entity Management** — Client, partner, vendor, and contact tracking with auto-detection
- **Project Tracking** — Auto-discovers repos and tracks status across all projects
- **GSD Workflow** — Structured project execution with phases, waves, and tasks
- **Knowledge Management** — Persistent knowledge base for systems, decisions, and references
- **Credential Management** — Secure cataloging and retrieval of API keys
- **MCP Management** — Detect, configure, and manage MCP servers with profiles
- **Time Tracking** — Automatic session time logging
- **Todo Management** — Aggregated task tracking
- **Intake Processing** — Process voice notes, documents, and files into the brain
- **Communications** — Unified communication tracking
- **Content Pipeline** — Content creation and publishing workflow
- **Session Archiving** — Archive sessions for searchability

## Profiles

Choose a profile during setup that matches your role:

- **Developer** — Software developers, indie hackers, technical founders
- **Content Creator** — Bloggers, YouTubers, social creators
- **Consultant** — Freelancers, service providers
- **Agency** — Agency owners managing multiple clients
- **Personal** — Anyone organizing work with AI

## Example Usage

Ask Claude Code to:

- "What projects am I working on?" (brain already knows)
- "Show me my open tasks" (`/todo`)
- "Update client Acme's contact info" (entity watchdog handles it)
- "Set up the Notion MCP" (`/mcp enable notion`)
- "Plan the next phase of my project" (`/gsd`)

## Documentation

For full documentation, visit [github.com/TechIntegrationLabs/bizbrain-os-plugin](https://github.com/TechIntegrationLabs/bizbrain-os-plugin).
