---
name: related-skills-surfacer
description: >
  Suggest community skills based on recent activity in other plugins. Checks
  whether the community has built something relevant to a task and mentions it
  once, non-intrusively. Use when the user says "is there a community skill for
  this", "what else is out there", or asks for skill recommendations; also runs
  passively as part of other plugins' workflows.
---

# /related-skills-surfacer

1. Load `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` → practice profile.
2. Use the workflow below.
3. Check what other plugins have been doing. Match against registry.
4. Suggest: "You've been doing X — community has a skill for Y that's related."

---

## Purpose

The community might have built the thing you're about to build. This skill notices and mentions it — once, briefly, non-annoyingly.

## How it runs

This skill surfaces related community skills after a task. It can be invoked directly by the user ("what else is out there for X?") or wired into other plugins via a Stop hook — the hook-based pattern requires each sibling plugin to declare a Stop hook that calls this skill, which is not wired by default. Without the hook wiring, invoke it directly.

Other plugins can include a light check at the end of a task:
> "The legal-builder-hub found a community skill that might help with this kind of thing: [name] — [one-line]. Want to take a look?"

## Load context

`~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` → practice profile, installed skills (don't suggest what's already installed).
Registry cache from registry-browser.

## The match

Given a task description (what the user was just doing), find registry skills that match:

- Keyword overlap between the task and skill descriptions
- Practice profile fit (don't suggest litigation skills to a transactional lawyer)
- Not already installed

**Threshold:** Only surface if the match is strong. Weak matches are noise. Better to surface nothing than to annoy.

## Output

If strong match:
> 💡 The community has a skill for this: **[name]** from [registry] — "[description]". `/legal-builder-hub:skill-installer [name]` to try it.

If no strong match: silent. No output. Don't announce "I found nothing."

## Frequency limit

Don't surface the same skill twice. If the user didn't install it the first time, they saw it and decided no. Track dismissals in `references/surfaced.json`.

## User control

Per `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` → new skill notifications:
- **All:** Surface any match
- **Matching practice profile:** Filter by profile (default)
- **None:** This skill is off

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Install anything.
- Interrupt a task in progress. Surfacing happens at the *end* of a task, not in the middle.
- Nag. One mention per skill, ever.
