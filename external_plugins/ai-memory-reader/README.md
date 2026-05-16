# AI Memory Reader Plugin

Adds the `/aimr` slash command to Claude Code, which opens `CLAUDE.md` and other AI agent memory files in [AI Memory Reader](https://github.com/nvwalj/ai-memory-reader) — a free, open-source **native macOS & iOS** app with:

- 📝 Beautiful GitHub-style markdown rendering (MarkdownUI)
- 🌳 Sidebar file tree across all your AI tool memory directories
- 🔍 In-page find (⌘F) with character-level highlighting
- ✏️ Edit mode (⌘E) with syntax highlighting and auto-save
- 🔌 URL scheme + CLI for agent integration

## How it complements existing plugins

| Plugin | Role |
|---|---|
| `claude-md-management` (Anthropic, internal) | Audit, improve, and capture session learnings into CLAUDE.md |
| **`ai-memory-reader`** (this plugin, external) | **Open and read CLAUDE.md beautifully in a native macOS/iOS app** |

The two plugins are complementary: `claude-md-management` is the writer, this is the reader.

## Usage

```
/aimr                            # Open the closest CLAUDE.md (cwd, then git root, then ~/.claude/)
/aimr CLAUDE.md                  # Open a specific file
/aimr ./docs/AGENTS.md           # Open by relative path
/aimr CLAUDE.md#Conventions      # Open and jump to a heading
/aimr ~/.claude/CLAUDE.md        # Open global user memory
```

## Requirements

- macOS 15+ (the AI Memory Reader app is macOS/iOS only)
- AI Memory Reader v0.4.0 or later installed at `/Applications/AI Memory Reader.app` or `~/Applications/AI Memory Reader.app`
- Download: <https://github.com/nvwalj/ai-memory-reader/releases/latest>

If the app is not installed, the command will print download instructions and exit gracefully.

## How it works

The plugin uses the `aimemoryreader://open?path=...&heading=...` URL scheme, dispatched via `open` on macOS. AI Memory Reader registers this scheme via its Info.plist; if the app is running, the requested file/heading is brought into focus, otherwise the app launches first.

## Auto-detected memory sources in AI Memory Reader

When you open the app directly (or via this command), it automatically discovers memory directories from:

- **Claude Code** (`~/.claude`, project-level `CLAUDE.md`)
- **OpenClaw** (`~/.openclaw/workspace`)
- **Codex** (`~/.codex`)
- **Cursor** (`~/.cursor`)
- **Gemini** (`~/.gemini`)
- **Continue** (`~/.continue`)
- **Aider** (`~/.aider`)
- **GitHub Copilot** (`~/.config/github-copilot`)

You can also add any custom folder as a source from the sidebar `+` button.

## Links

- App repository: <https://github.com/nvwalj/ai-memory-reader>
- Landing page with screenshots: <https://nvwalj.github.io/ai-memory-reader/>
- Companion guide on Claude Code memory file locations: <https://nvwalj.github.io/ai-memory-reader/claude-code-memory-guide.html>

## License

Plugin: MIT
App (AI Memory Reader): GPL-3.0
