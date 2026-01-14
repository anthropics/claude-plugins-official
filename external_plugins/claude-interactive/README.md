# Claude Interactive

Human-in-the-loop result filtering for Claude Code. Filter search results **BEFORE** they pollute your context window.

## The Problem

Every search result returned by Grep, Glob, or WebSearch consumes tokens in your context window. Large codebases can return dozens of matches, many irrelevant. By the time Claude processes them, your context is full of noise.

## The Solution

**Claude Interactive** lets you select which search results to keep before they enter context:

1. You request a search
2. Claude shows numbered results
3. You pick which ones matter
4. Only selected results are used

## Installation

Copy this folder to your Claude Code plugins directory:

```bash
# macOS/Linux
cp -r claude-interactive ~/.claude/plugins/

# Windows (PowerShell)
Copy-Item -Recurse claude-interactive "$env:USERPROFILE\.claude\plugins\"
```

Restart Claude Code.

## Usage

### Phrase-Triggered (Default)

Add trigger words to your search requests:

```
"Find all TODO comments interactively"
"Search for useState and let me pick which files"
"Grep for errors, filter results first"
```

Trigger phrases:
- `interactively`
- `let me pick`
- `filter results`
- `select results`

### Auto-Mode

Enable auto-mode to make ALL searches interactive:

```
/interactive auto on    # Enable
/interactive auto off   # Disable
/interactive status     # Check status
```

When auto-mode is enabled, every Grep, Glob, and WebSearch will prompt for result selection.

## Example

**You:** "Find files with useState interactively"

**Claude:**
```
Found 5 results for "useState":

1. src/App.tsx:12 - const [count, setCount] = useState(0)
2. src/Form.tsx:8 - const [value, setValue] = useState('')
3. src/Modal.tsx:15 - const [open, setOpen] = useState(false)
4. src/List.tsx:22 - const [items, setItems] = useState([])
5. src/tests/App.test.tsx:5 - import { useState } from 'react'

Select which results to keep: [1] [2] [3] [All] [None]
```

**You:** Select 1, 2, 3

**Claude:** (continues with only App.tsx, Form.tsx, Modal.tsx)

## How It Works

This plugin uses Claude Code's native features:

1. **CLAUDE.md** - Instructions that teach Claude the interactive protocol
2. **AskUserQuestion** - Native multi-select UI for result selection
3. **Flag file** - Simple `.claude-interactive-automode` for auto-mode toggle

No external dependencies. No MCP servers. No GUI required.

## Why This Matters

Context is precious. In a 200k token window:
- System prompt: ~4k tokens
- Tools: ~20k tokens
- That leaves ~175k for your conversation

A single broad Grep can return 50+ matches, each consuming tokens. With interactive filtering, you keep only what matters.

## License

MIT
