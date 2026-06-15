# Project Analyzer Plugin

A Claude Code plugin providing the **Project Analyzer** skill — a deep 8-dimension analysis framework for open-source projects and software architectures.

## Installation

```bash
/plugin install project-analyzer@claude-plugins-official
```

## What It Does

Transforms shallow code tours into living architectural analysis across 8 dimensions:

| Dimension | Core Question |
|-----------|--------------|
| Progressive Disclosure | Can readers get what they need at their level? |
| Architecture Decision Records | Why was it designed this way? |
| Scenario Walkthrough | Can the architecture actually run? |
| Degradation & Fallback | What happens when it breaks? |
| Competitive Landscape | Where does this stand vs alternatives? |
| Quantification | Are there real numbers? |
| Closed Loop | Does the system evolve over time? |
| Longitudinal Narrative | What happens long-term? |

## Usage

Trigger with natural language:

- "Analyze this project"
- "Deep dive into this repo"
- "Review the system design"
- "How does X work architecturally"

## Skill

The `project-analyzer` skill provides the full 8-dimension framework with quality checklist and anti-pattern guidance. See `skills/project-analyzer/SKILL.md` for details.

## License

Apache-2.0
