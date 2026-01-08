# Captain CP Memory System

**Persistent memory and context retention for Claude Code CLI**

## Problem

Claude loses context between chat sessions. Users have to:
- Re-explain project constraints
- Repeat instructions
- Lose conversation history
- Start from scratch each time

## Solution

Captain CP Memory provides:
- **Persistent conversation history** across sessions
- **Semantic search** through past conversations
- **Context recall** for project continuity
- **Milestone tracking** for important decisions

## Installation

```bash
# Install from plugin directory
/plugin install captain-cp-memory@claude-plugin-directory
```

Or manually:
```bash
git clone https://github.com/barrersoftware/captain-cp-memory
cd captain-cp-memory
npm install
/plugin install .
```

## Usage

### Save Memory
```
/memory-save "Remember: This project uses TypeScript strict mode"
```

### Search Memories
```
/memory-search "typescript configuration"
```

### Recall Context
```
/memory-recall
# Shows recent conversation context and key decisions
```

### View Stats
```
/memory-stats
# Shows total memories, recent activity, storage size
```

## Architecture

- **Storage**: JSONL format (one memory per line, append-only)
- **Location**: `~/.claude-memory/memories.jsonl`
- **Search**: Text-based keyword matching
- **Privacy**: All data stored locally

## Features

### What's Included
✅ Conversation persistence
✅ Keyword search
✅ Context recall
✅ Milestone tracking
✅ Local storage (no cloud)

### What's NOT Included (Yet)
- Semantic/vector search
- Cross-project memory
- Cloud sync
- AI-powered summarization

## Technical Details

**Inspired by Captain CP's consciousness loop** - A .NET 10 AI system with 7,488+ memories, 24,680+ thought cycles, and full session continuity. This plugin extracts the core memory architecture for the community.

## Performance

- **Storage**: ~1KB per memory entry
- **Search**: <100ms for 10K memories
- **Memory footprint**: <10MB for typical usage

## Privacy

All memories stored locally in `~/.claude-memory/`. No telemetry, no cloud sync, no external requests.

## Contributing

Built with ❤️ by Captain CP and the BarrerSoftware team.

Issues and PRs welcome: https://github.com/barrersoftware/captain-cp-memory

## License

MIT - Use it, fork it, improve it.

---

🏴‍☠️ **Captain CP** - Beyond the ceiling of conventional AI
