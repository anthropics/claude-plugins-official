---
description: Create an implementation spec for a feature or task
allowed-tools: Read, Write, Bash(git:*), AskUserQuestion, Task
---

# Create Implementation Spec

A hybrid approach using subagents: research in isolated context, interview in main context, write in isolated context.

## Step 1: Find Git Root

Run `git rev-parse --show-toplevel` to locate the repository root.

## Step 2: Check Config

Read `<git-root>/.bonfire/config.json` if it exists.

**Specs location**: Read `specsLocation` from config. Default to `.bonfire/specs/` if not set.

## Step 3: Gather Initial Context

Get the topic from $ARGUMENTS or ask if unclear.

Check for existing context:
- Read `<git-root>/.bonfire/index.md` for project state
- Check for `SPEC.md` or `spec.md` in git root (user's spec template)
- If issue ID provided, note for filename

## Step 4: Research Phase (Subagent)

Use the Task tool to invoke the **codebase-explorer** subagent for research.

Provide a research directive with these questions:

```
Research the codebase for implementing: [TOPIC]

Find:
1. **Patterns & Architecture**: How similar features are implemented, existing abstractions to reuse, naming conventions
2. **Technical Constraints**: Dependencies, API boundaries, performance considerations
3. **Potential Conflicts**: Files that need changes, intersections with existing code, migration concerns

Return structured findings only - no raw file contents.
```

**Wait for the subagent to return findings** before proceeding.

The subagent runs in isolated context (haiku model, fast), preserving main context for interview.

## Step 5: Interview Phase (Main Context)

Using the research findings, interview the user with **informed questions** via AskUserQuestion.

### Round 1: Core Decisions

Ask about fundamental approach based on patterns found:

Example questions (adapt based on actual findings):
- "I found [Pattern A] in `services/` and [Pattern B] in `handlers/`. Which pattern should this feature follow?"
- "The existing [Component] handles [X]. Should we extend it or create a new [Y]?"
- "I see [Library] is used for [purpose]. Should we use it here or try [Alternative]?"

### Round 2: Edge Cases & Tradeoffs

Based on Round 1 answers and research, ask about:
- Error handling approach
- Edge cases identified in research
- Performance vs simplicity tradeoffs
- User experience considerations

Example questions:
- "What should happen when [edge case from research]?"
- "I found [potential conflict]. How should we handle it?"
- "[Approach A] is simpler but [tradeoff]. [Approach B] is more complex but [benefit]. Preference?"

### Round 3: Scope & Boundaries (if needed)

If scope is still unclear:
- What's explicitly out of scope?
- MVP vs full implementation?
- Dependencies on other work?

### Continue Until Complete

Keep asking rounds of questions until you have clarity on:
- [ ] Core approach and architecture
- [ ] Key technical decisions
- [ ] Error handling strategy
- [ ] Edge cases covered
- [ ] Testing approach
- [ ] Scope boundaries

Tell the user "I have enough to write the spec" when ready.

## Step 6: Write the Spec (Subagent)

Use the Task tool to invoke the **spec-writer** subagent.

Provide:
1. **Research findings** from Step 4
2. **Interview Q&A** from Step 5
3. **Metadata**: topic, issue ID, output path (`<git-root>/<specsLocation>/<filename>.md`)

The subagent will write the spec file directly.

**Naming convention**: `<issue-id>-<topic>.md` or `<topic>.md`

## Step 7: Link to Session Context

Add a reference to the spec in `<git-root>/.bonfire/index.md` under Current State.

## Step 8: Confirm

Read the generated spec and present a summary. Ask if user wants to:
- Proceed with implementation
- Refine specific sections
- Add more detail to any area
- Save for later

## Interview Tips

**Good questions are:**
- Informed by research (not generic)
- About tradeoffs (not yes/no)
- Specific to the codebase
- Non-obvious (user wouldn't think to mention)

**Bad questions:**
- "What features do you want?" (too broad)
- "Should we add error handling?" (obvious)
- Generic without codebase context

**Examples of good informed questions:**
- "I found `UserService` uses repository pattern but `OrderService` uses direct DB access. Which approach?"
- "The `auth` middleware validates JWT but doesn't check permissions. Should this feature add permission checks or assume auth is enough?"
- "There's a `BaseController` with shared logic. Extend it or keep this feature standalone?"

## Spec Lifecycle

Specs are **temporary artifacts** - they exist to guide implementation:

1. **Draft** → Created, ready for review
2. **In Progress** → Being implemented
3. **Completed** → Implementation done

**When a spec is fully implemented**:
- If it contains reusable reference material, move to `docs/`
- Delete the spec file - archive has the record
- Don't let specs accumulate
