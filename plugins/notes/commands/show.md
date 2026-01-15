---
description: Display a specific note
argument-hint: <name>
allowed-tools: Bash, Read
---

Display the contents of a specific note from `~/.claude/notes/`.

## Validate Argument

If `$ARGUMENTS` is empty, inform the user that a note name is required:
- Show usage: `/notes:show <name>`
- Suggest using `/notes:list` to see available notes

## Find the Note

The name argument can be:
- Exact filename (without .md extension): `api-refactor`
- Partial match: `api` might match `api-refactor.md`
- Case-insensitive

### Exact match first
```bash
test -f ~/.claude/notes/$ARGUMENTS.md && echo "FOUND: $ARGUMENTS.md"
```

### Partial match fallback
```bash
ls ~/.claude/notes/*.md 2>/dev/null | xargs -I{} basename {} .md | grep -i "$ARGUMENTS"
```

## Handle Results

### Single match found
Read and display the full note content using the Read tool:
- Show the complete markdown content
- Format nicely for readability

### Multiple matches found
List all matching notes and ask user to be more specific:
```
Multiple notes match "api":
- api-refactor
- api-authentication
- api-docs-update

Please specify which note to show.
```

### No match found
Inform user and suggest alternatives:
- Show similar note names if any exist
- Suggest `/notes:list` to see all available notes

## Output

Display the note with clear formatting:
1. Show the filename and path
2. Display frontmatter metadata in a readable format
3. Show the full note content
