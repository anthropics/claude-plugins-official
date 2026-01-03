---
description: Review work for blindspots, gaps, and improvements
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Task, mcp__linear__*
---

# Review Work

Strategic review using subagent for analysis, preserving main context for action decisions.

## Step 1: Determine Scope

Based on $ARGUMENTS:
- No args: Review current branch vs base
- `--session`: Review work captured in current session context
- Topic/area: Focus review on specific aspect

## Step 2: Gather Context

- Read session context from `<git-root>/.bonfire/index.md`
- Get branch diff: `git diff main...HEAD` (or appropriate base)
- Read relevant specs/docs from `.bonfire/`
- Understand intent: what were we trying to accomplish?

## Step 3: Run Review (Subagent)

Use the Task tool to invoke the **work-reviewer** subagent.

Provide the review context:

```
Review this work for blindspots, gaps, and improvements.

**Scope**: [Branch diff / session work / specific area]

**Intent**: [What we were trying to accomplish - from session context]

**Files changed**:
[List of modified files from git diff]

**Session context**:
[Relevant notes from index.md]

Return categorized findings with severity and effort estimates.
```

**Wait for the subagent to return findings** before proceeding.

The subagent runs in isolated context (sonnet model), preserving main context for action decisions.

## Step 4: Session Scripts Review

Check if `<git-root>/.bonfire/scripts/` contains any files.

If scripts exist, include in findings:
- List scripts that may need attention
- Note if any appear to be temporary/one-off vs reusable
- Suggest moving useful scripts to project `scripts/` directory

This is informational - actual script management happens during `/bonfire:end`.

## Step 5: Present Findings

Present the subagent's findings grouped by recommended action:

### Fix Now (trivial effort)
[List items from subagent that can be fixed immediately]

> Ask: "Want me to fix these now?"

### Needs Spec (important, needs planning)
[List items that need implementation planning]

> Ask: "Want me to create an implementation spec?"

### Create Issues (large effort or nice-to-have)
[List items for future sessions]

> Ask: "Want me to create GitHub/Linear issues?"

## Step 6: Execute Chosen Action

Based on user choice:
- **Fix now**: Make the changes directly
- **Spec**: Run `/bonfire:spec` with findings
- **Create issues**: See below

### Creating Issues

First, read `<git-root>/.bonfire/config.json` and check `linearEnabled`.

**Offer choices based on config:**
- Always offer: "Create GitHub issue"
- If `linearEnabled` is true: Also offer "Create Linear issue"

**GitHub Issue Creation:**
```bash
gh issue create --title "Finding title" --body "Finding details"
```

**Linear Issue Creation (if enabled):**
1. Use Linear MCP `linear_create_issue` tool with:
   - `title`: Finding summary
   - `description`: Finding details with context
   - `teamId`: Infer from session context if available, otherwise use default
2. On success: Return issue URL/ID
3. On failure: Warn user, offer to create GitHub issue instead

Note: Tool names may vary by Linear MCP implementation.

**For each created issue:**
- Record the issue ID and URL
- Note which tracker (GitHub/Linear) was used

## Step 7: Update Session Context

Add review outcomes to `<git-root>/.bonfire/index.md`:
- Key findings noted
- Issues created (with links)
- Work deferred to future sessions
