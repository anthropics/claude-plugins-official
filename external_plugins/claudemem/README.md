# ClaudeMem

**AI-native project management for Claude Code.**

No app switching. No manual updates. Claude is the PM.

---

## The Problem

Every Claude Code session starts with amnesia:

```
Session 1: Deep discussion, decisions made, code written
[Session ends]
Session 2: "What were we working on?"
```

Context disappears. Decisions forgotten. You repeat yourself endlessly.

## The Solution

ClaudeMem gives Claude Code persistent memory across sessions:

```
You: "What was I working on?"
Claude: "Resuming your project. Task: Set up database. Continue?"
```

---

## Installation

```
/plugin marketplace add Dammyjay93/claudemem
/claudemem:setup
```

Then follow the setup instructions to configure hooks and CLAUDE.md.

---

## How It Works

```
~/Vault/                        Your workspace memory
├── _manifest.md                Quick state (loaded every session)
├── Projects/
│   └── my-project/
│       ├── _index.md           Project overview
│       ├── PRD.md              Requirements
│       ├── Decisions.md        Architecture decisions
│       └── Epics/              Tasks by epic
└── Sessions/                   Session history
```

---

## Commands

| Command | What It Does |
|---------|--------------|
| `/claudemem` | Smart dispatcher - reads context, suggests action |
| `/claudemem:setup` | Initialize vault structure |
| `/claudemem:status` | Show current project/epic/task |
| `/claudemem:plan` | Create project from conversation |
| `/claudemem:start` | Begin working on a task |
| `/claudemem:done` | Mark current task complete |
| `/claudemem:save` | Write session notes |
| `/claudemem:switch` | Change active project |

---

## The Workflow

### 1. Plan a Project

```
You: "I want to build an app that does X, Y, Z..."

[Conversation happens]

You: /claudemem:plan

Claude: Creates PRD, epics, tasks from conversation
        "Created project: 5 epics, 32 tasks. Start?"
```

### 2. Work on Tasks

```
You: /claudemem:start

Claude: Loads context, marks task in-progress
        "Working on: Set up database schema"

[You code]

You: /claudemem:done

Claude: Marks complete, suggests next
        "Done. Next: Implement auth flow. Continue?"
```

### 3. Resume Next Session

```
[New Claude Code session]

Claude: "Resuming project. Task: Implement auth flow. Continue?"
```

No re-explaining. No lost context. Just continue.

---

## Why Not Linear/Jira/Notion?

| Traditional PM | ClaudeMem |
|----------------|-----------|
| Manual task creation | Claude generates from conversation |
| Manual status updates | Claude updates as you work |
| Context in your head | Context in files Claude reads |
| Switch apps to check status | Ask Claude, stay in flow |
| Separate from your code | Integrated into Claude Code |

---

## Documentation

- [Commands Reference](docs/COMMANDS.md) - All commands
- [Setup Guide](docs/SETUP.md) - Manual installation
- [Future: Obsidian Integration](docs/FUTURE.md) - Visual layer roadmap

---

## License

MIT
