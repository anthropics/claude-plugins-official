# Conductor for Claude Code

**Measure twice, code once.**

Conductor is a Claude Code plugin that enables **Spec-Driven Development**. It transforms Claude into a proactive project manager that follows a strict protocol to specify, plan, and implement software features.

Instead of just writing code, Conductor ensures a consistent, high-quality lifecycle for every task: **Context -> Spec & Plan -> Implement**.

## Installation

### From GitHub (recommended)

Add the Conductor marketplace and install the plugin:

```bash
claude plugin marketplace add https://github.com/gagarinyury/claude_conductor
claude plugin install conductor@conductor-marketplace
```

### From Official Marketplace (coming soon)

Once accepted into the official marketplace:

```bash
claude plugin install conductor
```

## Features

- **Plan before you build**: Create specs and plans that guide the agent for new and existing codebases
- **Maintain context**: Ensure Claude follows style guides, tech stack choices, and product goals
- **Iterate safely**: Review plans before code is written
- **Persistent Memory**: Project context is stored in markdown files, not in the chat history
- **Git-aware revert**: Intelligently revert tracks, phases, or tasks with full git history awareness

## Commands

| Command | Description |
|---------|-------------|
| `/conductor:setup` | Initialize Conductor in a new project. Creates `conductor/` folder with product, tech stack, and workflow definitions |
| `/conductor:new <description>` | Create a new feature track or bug fix. Generates `spec.md` and `plan.md` |
| `/conductor:implement [track]` | Execute the tasks defined in a track's plan following your workflow |
| `/conductor:status` | Display the current progress of all tracks |
| `/conductor:revert` | Revert previous work (tracks, phases, or tasks) with git awareness |

## Usage

### 1. Initialize Project

```
> /conductor:setup
```

Claude will interview you about your product goals, tech stack, and workflow preferences, then create the `conductor/` context folder.

### 2. Create a Track

When you want to build a feature or fix a bug, create a track instead of coding immediately:

```
> /conductor:new "Add dark mode to settings"
```

Claude will create a detailed `spec.md` and `plan.md` in `conductor/tracks/`.

### 3. Implement

Execute the plan. Claude will follow TDD or your custom workflow defined in `conductor/workflow.md`:

```
> /conductor:implement
```

Claude works through the checklist in `plan.md`, marking tasks as done and committing changes.

### 4. Check Status

```
> /conductor:status
```

Get an overview of all tracks and their progress.

## Project Structure

Conductor creates a `conductor/` directory in your project root:

```
conductor/
├── product.md            # What are we building?
├── tech-stack.md         # What tools are we using?
├── workflow.md           # How do we work? (TDD, commits, etc.)
├── product-guidelines.md # Brand voice, style guidelines
├── tracks.md             # Registry of all features/bugs
└── tracks/
    └── feature-dark-mode/
        ├── spec.md       # Requirements
        ├── plan.md       # Implementation checklist
        └── metadata.json
```

## Plugin Structure

```
conductor/
├── .claude-plugin/
│   ├── plugin.json       # Plugin manifest
│   └── marketplace.json  # Marketplace definition
├── commands/             # Slash commands
│   ├── setup.md
│   ├── new.md
│   ├── implement.md
│   ├── status.md
│   └── revert.md
├── skills/               # Auto-activated skills
│   └── conductor-context/
│       └── SKILL.md
└── templates/            # Workflow templates
```

## Contributing

We welcome contributions! Please open issues or submit PRs.

## License & Credits

This project is a derivative work based on [Conductor](https://github.com/gemini-cli-extensions/conductor) by the Gemini CLI Extensions team, licensed under Apache License 2.0.

**Changes made in this fork:**
- Migrated from Gemini TOML format to Claude Code Markdown commands
- Converted to Claude Code plugin format
- Renamed commands with `conductor-` prefix
- Added `conductor-status` and `conductor-revert` commands
- Added skill for automatic context loading

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
