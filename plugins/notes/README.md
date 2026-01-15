# Notes Plugin

Save, manage, and retrieve contextual notes from Claude Code sessions.

## Installation

This plugin is part of the arizonabay claude-plugins collection. If using the collection, it auto-loads when configured.

For standalone testing:
```bash
claude --plugin-dir ~/projects/arizonabay/claude-plugins/plugins/notes
```

## Features

- **Persist session context** as markdown files in `~/.claude/notes/`
- **AI-generated summaries** with user constraints and approval
- **Search and filter** notes by time or keywords
- **Simple CRUD operations** for note management

## Commands

| Command | Description |
|---------|-------------|
| `/notes:update [name]` | Create or update a note with session context |
| `/notes:add [name]` | Alias for `notes:update` |
| `/notes:list [filter]` | List all notes, optionally filtered |
| `/notes:show <name>` | Display a specific note |
| `/notes:remove <name>` | Delete a note |

## Usage Examples

```
/notes:update                    # Interactive: proposes name and summary
/notes:update api-refactor       # Update/create note with specific name
/notes:list                      # List all notes
/notes:list since yesterday      # Filter by time
/notes:list authentication       # Filter by keyword
/notes:show api-refactor         # Show specific note
/notes:remove old-notes          # Delete a note (with confirmation)
```

## Note Format

Notes are stored as markdown files with YAML frontmatter:

```markdown
---
title: API Refactoring Notes
created: 2026-01-15T10:30:00
updated: 2026-01-15T14:45:00
tags: [api, refactoring]
project: myapp
---

# API Refactoring Notes

[Note content...]
```

## Storage Location

All notes are stored in `~/.claude/notes/` as kebab-case markdown files.

## How notes:update Works

1. **Context Analysis** - Claude reviews the conversation history
2. **Name Proposal** - Suggests a descriptive kebab-case filename
3. **User Approval** - You can accept, modify, or provide focus constraints
4. **Summary Generation** - Creates markdown with frontmatter and AI summary
5. **File Creation** - Writes to `~/.claude/notes/[name].md`

If a note with the same name exists, it updates rather than overwrites.

## Filtering Notes

### Time-based filters
- `since yesterday`, `since today` - last 24 hours
- `last week`, `past week` - last 7 days
- `last month`, `past month` - last 30 days
- `recent` - last 5 notes

### Keyword filters
- Searches filenames and frontmatter (title, tags, project)
- Case-insensitive matching
