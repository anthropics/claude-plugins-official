# Contributing to Pseudo-Code Prompting Plugin

Welcome to the Pseudo-Code Prompting Plugin for Claude Code! We're excited that you're interested in contributing. This plugin transforms natural language requirements into structured, validated pseudo-code using the PROMPTCONVERTER methodology.

## How to Contribute

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pseudo-code-prompting.git
   cd pseudo-code-prompting/pseudo-code-prompting-plugin
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or for bug fixes:
   git checkout -b fix/issue-description
   ```
4. **Make your changes** following the guidelines below
5. **Test your changes** thoroughly with Claude Code
6. **Submit a Pull Request** to the `main` branch

### Branch Naming Convention

- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring without functional changes

## Plugin Structure

This plugin follows Claude Code's official auto-discovery structure:

```
pseudo-code-prompting-plugin/
├── .claude-plugin/              # Marketplace configuration
│   ├── marketplace.json         # Marketplace metadata
│   └── README.md               # Installation guide
├── plugin.json                  # Plugin manifest (minimal)
├── skills/                      # 6 skills with progressive loading
│   ├── context-compressor/
│   │   ├── capabilities.json    # Tier 1: Discovery
│   │   ├── SKILL.md            # Tier 2: Overview
│   │   └── references/          # Tier 3: Specific patterns
│   ├── feature-dev-enhancement/
│   ├── prompt-analyzer/
│   ├── prompt-optimizer/
│   ├── prompt-structurer/
│   └── requirement-validator/
├── agents/                      # 5 agent definitions
│   ├── context-compressor.md
│   ├── prompt-analyzer.md
│   ├── prompt-optimizer.md
│   ├── prompt-transformer.md
│   └── requirement-validator.md
├── commands/                    # 4 slash commands
│   ├── compress-context.md
│   ├── optimize-prompt.md
│   ├── transform-query.md
│   └── validate-requirements.md
├── hooks/                       # 3 hooks + registration
│   ├── hooks.json              # Hook registration
│   ├── user-prompt-submit.sh
│   ├── post-transform-validation.sh
│   └── context-compression-helper.sh
├── README.md                    # Main documentation
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # This file
└── LICENSE                      # MIT License
```

**Key Principles:**

- **Auto-Discovery**: Claude Code automatically finds skills/, agents/, commands/, hooks/
- **No .claude/ folder**: That's for user workspace configuration, not plugin distribution
- **Progressive Loading**: Skills use 4-tier architecture for token efficiency
- **hooks.json**: Required file to register hook scripts properly

## Adding New Skills

Skills provide specialized knowledge and patterns for transformation, validation, or optimization.

### Skill Structure

Each skill should have:

```
skills/your-skill-name/
├── capabilities.json           # Tier 1: Discovery (100 tokens)
├── SKILL.md                    # Tier 2: Overview (300-800 tokens)
├── references/                 # Tier 3: Specific patterns
│   └── *.md
└── templates/                  # Tier 4: Code generation (optional)
    └── *.md
```

### Creating a New Skill

1. **Create the skill directory**:

   ```bash
   mkdir -p skills/your-skill-name/{references,templates}
   ```

2. **Create `capabilities.json`** (Tier 1 - Discovery):
   ```json
   {
     "skill_id": "your-skill-name",
     "name": "Your Skill Name",
     "version": "1.0.0",
     "description": "Brief description of what this skill does",
     "tags": ["category", "type", "domain"],
     "capabilities": [
       "specific-capability-1",
       "specific-capability-2"
     ],
     "triggers": {
       "keywords": ["keyword1", "keyword2"],
       "patterns": ["pattern.*regex"]
     },
     "provides": [
       "deliverable-1",
       "deliverable-2"
     ],
     "dependencies": ["other-skill-id"],
     "progressive_loading": {
       "tier_2": "SKILL.md",
       "tier_3": ["references/*.md"],
       "tier_4": ["templates/*.md"]
     }
   }
   ```

3. **Create `SKILL.md`** (Tier 2 - Overview):
   ```markdown
   # Your Skill Name

   Description of the skill and its purpose.

   ## When to Use

   - Use case 1
   - Use case 2

   ## Key Patterns

   ### Pattern 1
   Description and example

   ### Pattern 2
   Description and example

   ## Examples

   Concrete examples of using this skill

   ## Integration

   How this skill works with other skills
   ```

4. **Add reference files** (Tier 3 - Specific):
   - Create focused reference files in `references/`
   - Each file should be 90-300 tokens
   - Cover specific patterns, checklists, or examples

5. **Add templates** (Tier 4 - Generation):
   - Optional: Add code generation templates
   - Keep templates focused and reusable

6. **No plugin.json updates needed!**

   Claude Code auto-discovers skills from the `skills/` folder. Just make sure your skill has:
   - `capabilities.json` for discovery triggers
   - `SKILL.md` for the main skill content
   - Optional `references/` and `templates/` subdirectories

### Skill Best Practices

- **Keep it focused**: Each skill should have a single, clear purpose
- **Use progressive loading**: Structure content in 4 tiers for token efficiency
- **Provide examples**: Include concrete examples for each pattern
- **Document triggers**: Clear keywords and patterns for semantic discovery
- **Test thoroughly**: Verify the skill works in various scenarios

## Adding New Agents

Agents are specialized sub-processes that execute specific tasks within the plugin.

### Agent Structure

Create agent definition in `agents/your-agent-name.md`:

```markdown
---
name: your-agent-name
description: What this agent does and when to use it
tools: ["Read", "Write", "Grep"]
model: sonnet
color: blue
---

# Your Agent Name

Agent prompt and instructions...

## Your Task

Specific task description...

## Process

Step-by-step process...

## Output Format

Expected output format...

## Examples

Concrete examples...
```

### Agent Auto-Discovery

**No registration needed!** Claude Code automatically discovers agents from the `agents/` folder.

Key requirements:

- Agent file must be in `agents/*.md`
- Must have YAML frontmatter with `name`, `description`, `tools`
- Optional fields: `model`, `color`

**That's it!** The agent will be automatically available.

## Adding New Commands

Commands are user-invocable shortcuts for common operations.

### Command Structure

Create command file in `commands/your-command.md`:

```markdown
---
description: Brief description of what this command does
argument-hint: [expected-arguments]
allowed-tools: ["Read", "Write", "Skill", "Task"]
---

# Your Command Name

Description of the command and its purpose.

## Task

Command execution instructions...

## Usage Examples

Example invocations and expected results...
```

### Command Auto-Discovery

**No registration needed!** Commands are automatically discovered from the `commands/` folder.

The command will be available as `/your-command` in Claude Code.

## Adding New Hooks

Hooks execute at specific lifecycle events to automate workflows or enforce policies.

### Hook Structure

Create hook script in `hooks/your-hook.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Read hook input from stdin (JSON format)
INPUT=$(cat)

# Extract relevant data using bash regex (no jq dependency)
if [[ "$INPUT" =~ \"prompt\":[[:space:]]*\"([^\"]*)\" ]]; then
  PROMPT="${BASH_REMATCH[1]}"
else
  exit 0
fi

# Your hook logic here
if [[ condition ]]; then
  cat <<EOF

[Your context injection or message]
EOF
  exit 0
fi

# Pass through unchanged
exit 0
```

Make it executable:

```bash
chmod +x hooks/your-hook.sh
```

### Registering the Hook

Update `hooks/hooks.json`:

```json
{
  "description": "Your plugin hooks",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/your-hook.sh",
            "statusMessage": "Running your hook...",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**Important:**

- Use `${CLAUDE_PLUGIN_ROOT}` for portable paths (not hardcoded)
- Always use `set -euo pipefail` for proper error handling
- Exit 0 for normal pass-through
- Exit 2 with JSON output for interactive approval (`permissionDecision: "ask"`)

## Testing Your Changes

1. **Install the plugin locally**:

   ```bash
   # Symlink to Claude Code plugins directory
   ln -s $(pwd) ~/.claude/plugins/pseudo-code-prompting
   ```

2. **Test with Claude Code**:

   ```bash
   # Start a new session
   cc

   # Verify plugin is loaded
   /plugin list

   # Try your new feature
   /your-command test input
   ```

3. **Verify progressive loading**:

   - Check that skills load incrementally (view Claude logs)
   - Monitor token usage
   - Ensure `capabilities.json` discovery works

4. **Test hooks**:

   - Trigger UserPromptSubmit hooks (type any message)
   - Trigger PostToolUse hooks (make a file edit)
   - Verify hook scripts execute and output correctly

5. **Test commands**:

   - Invoke your new command with `/command-name`
   - Verify command appears in `/help` output
   - Test with various argument patterns

## Code Quality Guidelines

### Skill Files
- Use clear, concise language
- Include concrete examples for every pattern
- Structure content for progressive loading
- Keep Tier 1 (capabilities.json) under 110 tokens
- Keep Tier 3 (references) files under 300 tokens each

### Agent Definitions
- Clearly define the agent's purpose and scope
- Specify all required tools
- Document expected input and output formats
- Include quality checks and validation steps

### Hooks
- Keep hooks focused on a single responsibility
- Exit with code 0 for pass-through behavior
- Use clear, informative status messages
- Handle edge cases gracefully
- Log errors appropriately

### Documentation
- Update README.md for major features
- Add entries to CHANGELOG.md
- Include usage examples
- Document any breaking changes

## Pull Request Process

1. **Update documentation**:
   - Update README.md if adding major features
   - Add entry to CHANGELOG.md
   - Update SKILL.md if changing plugin overview

2. **Test thoroughly**:
   - Test all affected workflows
   - Verify progressive loading works
   - Check agent coordination

3. **Submit PR** with:
   - Clear title describing the change
   - Description of what was added/changed/fixed
   - Examples of usage (if applicable)
   - Screenshots/recordings (if UI changes)

4. **Address review feedback**:
   - Respond to comments promptly
   - Make requested changes
   - Update PR description if scope changes

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers and help them contribute
- Focus on what is best for the community
- Show empathy towards other contributors

## Questions?

- Open an issue for bug reports or feature requests
- Join discussions for design questions
- Check existing issues before creating new ones

Thank you for contributing to the Pseudo-Code Prompting Plugin!
