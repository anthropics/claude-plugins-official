---
name: example-skill
description: This skill should be used when the user asks to "demonstrate skills", "show skill format", "create a skill template", or discusses skill development patterns. Provides a reference template for creating Claude Code plugin skills.
version: 1.0.0
---

# Example Skill

This skill demonstrates the structure and format for Claude Code plugin skills.

## Overview

Skills are model-invoked capabilities that Claude autonomously uses based on task context. Unlike commands (user-invoked) or agents (spawned by Claude), skills provide contextual guidance that Claude incorporates into its responses.

## When This Skill Applies

This skill activates when the user's request involves:
- Creating or understanding plugin skills
- Skill template or reference needs
- Skill development patterns

## Skill Structure

### Required Files

```
skills/
└── skill-name/
    └── SKILL.md          # Main skill definition (required)
```

### Optional Supporting Files

```
skills/
└── skill-name/
    ├── SKILL.md          # Main skill definition
    ├── README.md         # Additional documentation
    ├── references/       # Reference materials
    │   └── patterns.md
    ├── examples/         # Example files
    │   └── sample.md
    └── scripts/          # Helper scripts
        └── helper.sh
```

## Frontmatter Options

Skills support these frontmatter fields:

- **name** (required): Skill identifier
- **description** (required): Trigger conditions - describe when Claude should use this skill
- **version** (optional): Semantic version number
- **license** (optional): License information or reference

## Writing Effective Descriptions

The description field is crucial - it tells Claude when to invoke the skill. Think of it as progressive disclosure: the description (metadata) determines whether the skill loads, then the body provides full instructions, and references/ supply deep context only when needed.

**Good description patterns:**
```yaml
description: This skill should be used when the user asks to "specific phrase", "another phrase", mentions "keyword", or discusses topic-area.
```

**Include:**
- Specific trigger phrases users might say
- Keywords that indicate relevance
- Topic areas the skill covers

**Anti-patterns to avoid:**

- **Too broad**: `description: Use when the user writes code` — triggers on nearly everything, wasting context on irrelevant tasks
- **Too narrow**: `description: Use when user says "run skill X v2"` — requires exact phrasing nobody will guess
- **Vague**: `description: Helps with development tasks` — no concrete triggers for Claude to match against

## Skill Content Guidelines

1. **Clear purpose**: State what the skill helps with
2. **When to use**: Define activation conditions
3. **Structured guidance**: Organize information logically
4. **Actionable instructions**: Provide concrete steps
5. **Examples**: Include practical examples when helpful

## Best Practices

- Keep skills focused on a single domain
- Write descriptions that clearly indicate when to activate
- Include reference materials in subdirectories for complex skills
- Test that the skill activates for expected queries
- Avoid overlap with other skills' trigger conditions
