---
description: "Show only active projects updated within 1 week"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

Display only active projects updated within 1 week from `~/.ypm/PROJECT_STATUS.md`.

**Prerequisites**:
- Run `/ypm:setup` first if `~/.ypm/config.yml` doesn't exist
- Run `/ypm:update` first if `~/.ypm/PROJECT_STATUS.md` doesn't exist

**Display Content**:
- Project name
- Overview
- Current branch
- Last update date
- Phase
- Implementation progress
- Next task

**Display Format**:
Show active projects in descending order by update date (newest first).

**Additional Information**:
- Total count of active projects
- Most progressed project
- Most recently updated project
