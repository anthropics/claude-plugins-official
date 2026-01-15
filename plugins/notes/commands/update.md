---
description: Create or update a note with session context
argument-hint: [name]
allowed-tools: Bash, Write, Read, AskUserQuestion
---

Create or update a note capturing the current session's context in `~/.claude/notes/`.

## Setup

First, ensure the notes directory exists:

```bash
mkdir -p ~/.claude/notes
```

## Process

### Step 1: Analyze Session Context

Review the conversation history and identify:
- Main topics discussed
- Key decisions made
- Problems solved
- Code changes or implementations
- Important learnings or insights

### Step 2: Propose Note Details

If a name was provided as `$ARGUMENTS`, use that as the base name (convert to kebab-case if needed).

If no name was provided, derive a descriptive name from the session content (e.g., "api-authentication-setup", "debugging-memory-leak", "react-component-refactor").

Use AskUserQuestion to present:
1. **Proposed filename** (kebab-case, no extension)
2. **Suggested tags** (2-4 relevant keywords)
3. **Summary scope** - ask user if they want to focus on specific aspects or capture everything

### Step 3: Generate Note Content

Based on user's constraints and approval, create a markdown note with this structure:

```markdown
---
title: [Descriptive Title]
created: [ISO 8601 timestamp]
updated: [ISO 8601 timestamp]
tags: [tag1, tag2, tag3]
project: [current project name if applicable]
---

# [Title]

## Summary
[2-3 sentence overview of what was accomplished]

## Key Points
- [Important point 1]
- [Important point 2]
- [Important point 3]

## Details
[More detailed content based on session context]

## Related Files
[List any files that were created, modified, or discussed]
```

### Step 4: Write the Note

Write the note to `~/.claude/notes/[name].md`.

If a note with the same name exists:
- Read the existing note
- Update the `updated` timestamp
- Merge or replace content based on user preference (ask if unclear)

### Step 5: Confirm

Report the note was saved successfully with:
- Full path to the note
- Brief summary of what was captured
