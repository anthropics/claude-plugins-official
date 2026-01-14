# Claude History

Automatic transcript backup for Claude Code. Every conversation saved, organized by date, fully searchable.

## Features

- **Auto-backup on every message** - Never lose work
- **Organized by date** - `exports/YYYY-MM-DD/[summary]_[id].jsonl`
- **Metadata files** - Session info, git branch, message count
- **Central index** - `exports/index.json` for easy searching
- **CLI feedback** - Shows `[OK] Transcript backed up` after each save

## Installation

### Project Scope (recommended)
Copy to your project's `.claude/plugins/` folder:
```bash
cp -r claude-history /path/to/project/.claude/plugins/
```

### User Scope
Copy to your user plugins folder:
```bash
cp -r claude-history ~/.claude/plugins/
```

Then restart Claude Code.

## Usage

Once installed, backups happen automatically. You'll see:
```
[OK] Transcript backed up
```

### Commands

- `/history` - Show backup statistics
- `/history list` - List recent sessions
- `/history open` - Open exports folder

## Export Structure

```
your-project/
└── exports/
    ├── index.json                              # Central registry
    ├── 2026-01-14/
    │   ├── 2026-01-14_feature-work_9e0db771.jsonl
    │   ├── 2026-01-14_feature-work_9e0db771.meta.json
    │   └── ...
    └── 2026-01-13/
        └── ...
```

### Metadata Schema

Each `.meta.json` contains:
```json
{
  "sessionId": "9e0db771-...",
  "summary": "Feature work session",
  "gitBranch": "main",
  "startTime": "2026-01-14T11:34:32Z",
  "messageCount": 245,
  "sizeBytes": 125000
}
```

## Requirements

- **Windows**: Works natively (PowerShell 5.1+)
- **Mac/Linux**: Requires PowerShell Core (`pwsh`)
  ```bash
  # Mac
  brew install powershell

  # Ubuntu/Debian
  sudo apt-get install -y powershell
  ```

## How It Works

The plugin uses Claude Code hooks to capture conversations:

1. **UserPromptSubmit** - Triggers after every message (3s timeout)
2. **Stop** - Triggers when session ends (10s timeout)

Both hooks run the same `export-transcript.ps1` script that:
1. Finds your current transcript in `~/.claude/projects/`
2. Extracts session metadata (ID, summary, timestamps)
3. Copies to dated folder in `exports/`
4. Updates the central `index.json`

## License

MIT
