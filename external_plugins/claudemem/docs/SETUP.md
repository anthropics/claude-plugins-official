# Setup Guide

## Quick Install (Recommended)

In Claude Code:

```
/plugin marketplace add Dammyjay93/claudemem
/claudemem:setup
```

The setup command creates the vault structure and shows configuration steps.

---

## Post-Setup Configuration

After running `/claudemem:setup`, you need to:

### 1. Update CLAUDE.md

Add to `~/.claude/CLAUDE.md`:

```markdown
---

# Memory Protocol (ClaudeMem)

@~/Vault/_manifest.md

## On Every Session Start

1. Read the manifest imported above
2. Check `Active Context` section for current project/task
3. If active context exists:
   - Announce: "Resuming {project}, currently on: {task}"
4. If no active context:
   - Announce: "No active project. Ready to start something new."
```

### 2. Configure Hooks

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start-memory.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-stop-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

If you have existing hooks, merge these with yours.

---

## Manual Installation

If you prefer not to use the plugin system:

### 1. Create Vault Structure

```bash
mkdir -p ~/Vault/{Projects,Sessions,.schemas}
```

### 2. Copy Files from Repository

```bash
git clone https://github.com/Dammyjay93/claudemem.git
cp claudemem/vault/_manifest.md ~/Vault/
cp claudemem/vault/.schemas/*.md ~/Vault/.schemas/
```

### 3. Copy Commands

```bash
mkdir -p ~/.claude/commands/claudemem
cp claudemem/commands/claudemem.md ~/.claude/commands/
cp claudemem/commands/claudemem/*.md ~/.claude/commands/claudemem/
```

### 4. Copy Hooks

```bash
mkdir -p ~/.claude/hooks
cp claudemem/hooks/*.sh ~/.claude/hooks/
cp claudemem/hooks/*.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

### 5. Configure (see above)

Update CLAUDE.md and settings.json as described above, but use `~/.claude/hooks/` paths instead of `${CLAUDE_PLUGIN_ROOT}/hooks/`.

---

## Verify Installation

Start a new Claude Code session and run:

```
/claudemem:status
```

You should see:

```
CLAUDEMEM

No active project.

Projects: None yet
Sessions: None yet

Use /claudemem:plan to create a project from conversation.
```

---

## Troubleshooting

### Command not found

1. Check plugin is installed: `/plugin list`
2. Restart Claude Code to pick up new commands

### Hooks not running

1. Check settings.json is valid JSON
2. Check hook paths are correct
3. For plugin hooks, ensure `${CLAUDE_PLUGIN_ROOT}` is supported

### Manifest not loading

1. Check file exists: `cat ~/Vault/_manifest.md`
2. Check CLAUDE.md has the import: `@~/Vault/_manifest.md`
