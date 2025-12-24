# YPM Documentation Index

**Last Updated**: 2025-11-12

This directory contains documentation about the design and usage of YPM (Your Project Manager).

---

## 📚 Documentation List

### Essential Documentation

| Document | Description | Target Audience |
|----------|-------------|-----------------|
| [../README.md](../README.md) | YPM overview and usage guide | Everyone |
| [../CLAUDE.md](../CLAUDE.md) | Instructions for Claude Code | AI Developers |
| [../config.example.yml](../config.example.yml) | Configuration file sample (watch targets, detection patterns) | Configuration Editors |
| [../project-bootstrap-prompt.md](../project-bootstrap-prompt.md) | New project launch guide | Everyone |

### Developer Documentation

| Document | Description | Target Audience |
|----------|-------------|-----------------|
| [development/architecture.md](development/architecture.md) | Overall YPM architecture and design principles | Contributors, Developers |
| [development/onboarding-script-spec.md](development/onboarding-script-spec.md) | Onboarding wizard specification | Contributors, Developers |
| [development/ypm-open-spec.md](development/ypm-open-spec.md) | `/ypm:open` command specification | Contributors, Developers |
| [development/global-export-system.md](development/global-export-system.md) | Global export system design and usage | Contributors, Developers |

---

## 📖 Reading Order

### For First-Time Users

1. **[README.md](../README.md)** - What is YPM and how to use it
2. **[config.yml](../config.yml)** - Watch target configuration
3. **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Check current project status

### For Development with Claude Code

1. **[CLAUDE.md](../CLAUDE.md)** - Session startup procedures
2. **[docs/INDEX.md](INDEX.md)** - Documentation index

### For Customizing Configuration

1. **[config.yml](../config.yml)** - Watch target directories, detection patterns, classification criteria
2. **[README.md](../README.md)** - Explanation of customization methods

### For Contributing to YPM

1. **[development/architecture.md](development/architecture.md)** - Understand overall architecture
2. **[CLAUDE.md](../CLAUDE.md)** - DDD principles and development flow
3. **[development/onboarding-script-spec.md](development/onboarding-script-spec.md)** - Reference as implementation example

---

## 🎯 Document Purposes

### README.md
- **Purpose**: Explain how to use YPM
- **Target**: Everyone who wants to use YPM
- **Contents**: Overview, features, setup, usage, FAQ

### CLAUDE.md
- **Purpose**: Enable Claude Code to execute tasks
- **Target**: AI Developers (Claude Code)
- **Contents**: Session startup procedures, main features, PROJECT_STATUS.md structure, update rules

### config.yml
- **Purpose**: Define watch targets and project detection rules
- **Target**: People configuring YPM
- **Contents**: Watch directories, exclusion patterns, detection patterns, classification criteria, progress rate estimation criteria

### PROJECT_STATUS.md
- **Purpose**: Display a list of all project progress statuses
- **Target**: Project managers, developers
- **Contents**: List by project category, progress rates, next tasks, last update timestamps


### development/architecture.md
- **Purpose**: Explain overall YPM architecture and design principles
- **Target**: Contributors, developers
- **Contents**: DDD principles, directory structure, components, data flow, extensibility

### development/onboarding-script-spec.md
- **Purpose**: Provide complete specification for the onboarding wizard
- **Target**: Contributors, developers
- **Contents**: Functional requirements, input specifications, output specifications, error handling, implementation skeleton

---

## 🔄 Documentation Update Rules

### When to Update

- **config.yml**: When changing watch targets or detection rules
- **README.md**: When usage changes or FAQ grows
- **CLAUDE.md**: When YPM features are added or rules are changed

### Who Updates

- **config.yml**: Users edit manually
- **README.md, CLAUDE.md**: Edit manually as needed

---

## 📝 Documentation Management Principles

### 1. Keep Documentation Always Up-to-Date

Please update outdated information immediately. When documentation diverges from reality, YPM's credibility is compromised.

### 2. Keep It Concise and Clear

Avoid verbose explanations and provide only the minimum necessary information.

### 3. Include Concrete Examples

Include not just abstract explanations, but concrete code examples and configuration examples.

---

## 🚀 Future Expansion Plans

### Documentation Addition Plans

- **Configuration Guide** (`docs/config_guide.md`) - Detailed explanation of config.yml
- **Troubleshooting** (`docs/troubleshooting.md`) - Common issues and solutions
- **Automation Guide** (`docs/automation.md`) - How to set up cron and scripting
- **Dashboard Design** (`docs/dashboard_design.md`) - Design for web-based visualization tools

---

## 📞 Support

- **Configuration Questions**: Refer to comments in [config.example.yml](../config.example.yml)
- **Usage Questions**: Check [README.md](../README.md)
- **Development Questions**: Check procedures in [CLAUDE.md](../CLAUDE.md)

---

**This document is an index for understanding the overall picture of YPM.** 📚
