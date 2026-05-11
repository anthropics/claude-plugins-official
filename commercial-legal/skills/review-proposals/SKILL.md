---
name: review-proposals
description: >
  Review and approve (or reject) pending playbook update proposals from the
  playbook-monitor agent and apply approved changes to the practice profile. Use
  when the playbook-monitor agent has surfaced proposals, when the user says
  "review playbook proposals", "what playbook updates are pending", or wants to
  step through deviation-driven playbook changes.
argument-hint: "[no arguments needed — works from the pending proposals file]"
---

# /review-proposals

Steps through pending playbook update proposals from the monitor agent and applies approved changes to `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`.

## Instructions

1. **Load the playbook-monitor agent** and run Step 5 (review and approval flow).

2. **If no proposals file exists** or it is empty: respond *"No pending proposals. Playbook is up to date."* Do not proceed further.

3. **Present proposals one at a time.** For each, show the full proposal block and offer four options: Accept, Reject, Edit, Defer.

4. **For Accept or Edit:** show the exact diff to `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` before writing. Only apply after the attorney explicitly confirms.

5. **For Reject or Defer:** log the decision. Do not modify `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`.

6. **After all proposals are resolved:** show a summary of what changed, then archive the proposals file.

## Examples

```
/commercial-legal:review-proposals
```

```
/commercial-legal:review-proposals
(runs automatically after playbook-monitor notifies you)
```
