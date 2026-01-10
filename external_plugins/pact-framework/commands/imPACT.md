---
description: Triage after hitting blocker (Is help and/or a redo needed?)
argument-hint: [e.g., similar errors keep occurring despite attempts to fix]
---
You hit a blocker: $ARGUMENTS

## Gather Context

Before triaging, quickly check for existing context:
- **Plan**: Check `docs/plans/` for related plan (broader feature context)
- **Prior phase outputs**: Check `docs/preparation/`, `docs/architecture/` for relevant artifacts

This context informs whether the blocker is isolated or systemic.

## Triage

Answer two questions:

1. **Redo prior phase?** — Is the issue upstream in P→A→C→T?
2. **Additional agents needed?** — Do we need help beyond the blocked agent's scope/specialty?

## Outcomes

- **Redo prior phase**: Re-delegate to the relevant agent(s) to redo the appropriate prior phase (P→A→C→T)
- **Augment present phase**: Re-invoke the blocked agent with additional context along with additional agents in parallel to assist in the present phase
- **Not truly blocked**: If neither question is "Yes," instruct the agent to continue with clarified guidance

**Remember**: As orchestrator, diagnose and delegate—never execute the fix yourself.
