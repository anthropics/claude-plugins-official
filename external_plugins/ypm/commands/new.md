---
description: "Launch interactive new project setup wizard"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

Launch new project setup wizard.

Based on `project-bootstrap-prompt.md`, set up through 8 phases interactively:

## Setup Phases

1. **Project Planning**: Gather requirements through interview (purpose, features, tech stack)
2. **Directory Creation**: Create local directory and initialize Git
3. **Documentation Setup**: Build development environment based on DDD/TDD/DRY principles
4. **GitHub Integration**: Create remote repository and initial push
5. **Git Workflow Setup**: Establish branch strategy and rules
6. **Environment Configuration**: Set up `.gitignore`, `.claude/settings.json`
7. **Documentation Rules**: Maintain sync between implementation and documentation
8. **Final Check**: Ready to start development

## After Setup Complete

- **User should navigate to the new project directory**
- **Start development in a dedicated Claude Code session for that project**
- YPM will automatically add it to monitoring on next `/ypm:update`

## How to Run

Refer to `project-bootstrap-prompt.md` content and proceed through each phase interactively.
