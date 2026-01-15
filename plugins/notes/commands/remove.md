---
description: Delete a note (with confirmation)
argument-hint: <name>
allowed-tools: Bash, Read, AskUserQuestion
---

Delete a note from `~/.claude/notes/` after user confirmation.

## Validate Argument

If `$ARGUMENTS` is empty, inform the user that a note name is required:
- Show usage: `/notes:remove <name>`
- Suggest using `/notes:list` to see available notes

## Find the Note

The name argument can be:
- Exact filename (without .md extension): `api-refactor`
- Partial match: `api` might match `api-refactor.md`

### Exact match first
```bash
test -f ~/.claude/notes/$ARGUMENTS.md && echo "FOUND"
```

### Partial match fallback
```bash
ls ~/.claude/notes/*.md 2>/dev/null | xargs -I{} basename {} .md | grep -i "$ARGUMENTS"
```

## Handle Results

### Single match found
1. Read the note to show a preview (title and summary)
2. Use AskUserQuestion to confirm deletion:
   - Show the note name and title
   - Ask "Are you sure you want to delete this note?"
   - Options: "Yes, delete it" / "No, keep it"

### Multiple matches found
List all matching notes and ask user to be more specific:
```
Multiple notes match "api":
- api-refactor
- api-authentication

Please specify the exact note name to remove.
```

### No match found
Inform user the note doesn't exist and suggest `/notes:list` to see available notes.

## Delete the Note

If user confirms deletion:

```bash
rm ~/.claude/notes/[name].md
```

Report success: "Note '[name]' has been deleted."

If user cancels, acknowledge: "Deletion cancelled. Note '[name]' was not removed."
