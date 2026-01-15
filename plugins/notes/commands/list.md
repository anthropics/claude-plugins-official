---
description: List notes, optionally filtered by time or keyword
argument-hint: [filter]
allowed-tools: Bash, Read, Grep
---

List all notes stored in `~/.claude/notes/`, with optional filtering.

## Check Notes Directory

First check if the notes directory exists and has files:

```bash
ls -la ~/.claude/notes/*.md 2>/dev/null || echo "NO_NOTES_FOUND"
```

If no notes exist, inform the user and suggest using `/notes:update` to create their first note.

## Parse Filter Argument

The filter `$ARGUMENTS` can be:

### Time-based filters
- "since yesterday", "since today" - notes created/updated in last 24 hours
- "last week", "past week", "since last week" - notes from last 7 days
- "last month", "past month" - notes from last 30 days
- "recent" - last 5 notes by modification date

### Keyword filters
- Any other text is treated as a keyword search
- Search note filenames AND frontmatter (title, tags, project fields)

## List Notes

### No filter provided
List all notes with their metadata:

```bash
for f in ~/.claude/notes/*.md; do
  echo "---"
  echo "File: $(basename "$f" .md)"
  head -20 "$f" | grep -E "^(title|created|updated|tags|project):" || true
done
```

### Time filter
Use file modification time or parse frontmatter dates:

```bash
# Example: find notes modified in last 7 days
find ~/.claude/notes -name "*.md" -mtime -7 -exec basename {} .md \;
```

### Keyword filter
Search filenames and frontmatter for the keyword:

```bash
# Search in filenames
ls ~/.claude/notes/*.md 2>/dev/null | xargs -I{} basename {} .md | grep -i "keyword"

# Search in frontmatter (first 15 lines of each file)
grep -l -i "keyword" ~/.claude/notes/*.md 2>/dev/null | xargs -I{} basename {} .md
```

## Output Format

Present results as a formatted table:

| Note | Title | Created | Tags |
|------|-------|---------|------|
| api-refactor | API Refactoring Notes | 2026-01-15 | api, refactor |
| auth-setup | Authentication Setup | 2026-01-14 | auth, security |

If filter returns no results, suggest broadening the search or show all available notes.

## Tips
- Show note count at the end (e.g., "Found 5 notes")
- For time filters, also show the date range searched
- For keyword filters, highlight which field matched (filename, title, tags, etc.)
