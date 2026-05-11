---
name: uninstall
description: >
  Uninstall a community skill that was installed via the hub. Confirms before
  deleting files, refuses to touch first-party plugin skills, and logs every
  action. Use when the user wants to fully remove a community skill
  ("uninstall [skill]", "remove this skill") rather than just disable it.
argument-hint: "[skill name]"
---

# /uninstall

Run the `uninstall` workflow from the skill-manager reference skill against
the named skill.

Safety rules:

1. **Only uninstall community skills installed through this hub.** Check
   `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/install-log.yaml`
   and the CLAUDE.md installed starter pack table. If the skill is not recorded
   there, refuse and tell the user.
2. **Never uninstall a first-party plugin's skill.** The 12 core plugins that
   ship with claude-for-legal are off-limits from this command. If the named
   skill resolves to a path inside one of those plugins, refuse.
3. **Confirm before removing files.** Show the user every path that will be
   deleted. Proceed only on explicit `yes`.
4. **Log the uninstall.** Append to `install-log.yaml` with action `uninstall`
   and timestamp so the audit trail is intact.

If the user wants to stop a skill from running but keep the files (e.g., for
later re-enable, or to preserve configuration), suggest `/legal-builder-hub:disable`
instead.

> Detailed uninstall, disable, and re-enable workflows live in the
> `skill-manager` reference skill — load it before doing substantive work.
