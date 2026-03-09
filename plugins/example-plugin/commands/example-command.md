---
description: An example slash command that demonstrates command frontmatter options
argument-hint: <required-arg> [optional-arg]
allowed-tools: [Read, Glob, Grep, Bash]
---

# Example Command

This command demonstrates slash command structure and frontmatter options.

## Arguments

The user invoked this command with: $ARGUMENTS

`$ARGUMENTS` is a template variable that Claude Code automatically replaces with whatever the user typed after the command name. For example, if the user runs `/example-command src/app.ts --verbose`, then `$ARGUMENTS` becomes `src/app.ts --verbose`.

## Instructions

When this command is invoked:

1. Parse the arguments provided by the user
2. Perform the requested action using allowed tools
3. Report results back to the user

## Frontmatter Options Reference

Commands support these frontmatter fields:

- **description**: Short description shown in /help
- **argument-hint**: Hints for command arguments shown to user
- **allowed-tools**: Pre-approved tools for this command (reduces permission prompts)
- **model**: Override the model (e.g., "haiku", "sonnet", "opus")

## Example Usage

```
/example-command my-argument
/example-command arg1 arg2
```

### How arguments flow

Given this command definition:
```markdown
The user wants to search for: $ARGUMENTS
```

When the user runs `/example-command login bug`, Claude sees:
```markdown
The user wants to search for: login bug
```
