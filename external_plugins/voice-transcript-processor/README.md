# Voice Transcript Processor — Claude Code Plugin

A Claude Code plugin that transforms voice recording transcripts into structured project context documents, keeping Claude aligned with your instructions across sessions.

## The Problem

When working with AI on complex projects, you often think of instructions, answers, and tasks away from the keyboard — during a walk, in the car, between meetings. You record a voice note. But raw transcripts are:

- Long and rambling
- Mixed — instructions, answers, research tasks, and feedback all jumbled together
- Easy for the LLM to lose track of mid-session

## What This Does

Invoke `/transcript` with a transcript and Claude will:

1. **Parse** the transcript into structured categories
2. **Create** `.claude/voice/LATEST_CONTEXT.md` — a clean session document
3. **Update** `.claude/voice/PENDING_TASKS.md` — persistent task tracker across sessions
4. **Archive** the session to `.claude/voice/session_YYYYMMDD_HHMMSS.md`
5. **Immediately execute** clear instructions from the transcript

## Extracted Categories

| Category | What It Captures |
|----------|-----------------|
| **Instructions** | Things you want Claude to do this session |
| **Answers** | Your responses to questions Claude asked previously |
| **Research Tasks** | Things to look up or investigate |
| **Feedback** | Your reaction to previous work |
| **Decisions** | Committed architectural/business/content choices |
| **Todo Updates** | Completions, deferrals, cancellations |
| **Context / Notes** | Background info, constraints, anything else |

## Usage

```
/transcript path/to/my-note.txt
```

Or invoke without an argument and paste the transcript when prompted:

```
/transcript
```

## Workflow

1. Record a voice note on your phone answering Claude's questions and giving new instructions
2. Get it transcribed (iOS Voice Memos, Whisper, Otter, etc.)
3. Run `/transcript` at the start of your session
4. Claude processes it and starts executing immediately

## Files Created

All output goes to `.claude/voice/` in your project:

```
.claude/
└── voice/
    ├── LATEST_CONTEXT.md          ← Current session context (always current)
    ├── PENDING_TASKS.md           ← Cross-session task tracker
    ├── session_20260328_143022.md ← Archived session history
    └── session_20260327_091500.md
```

## Installation

```
/install voice-transcript-processor
```

Or add to your `settings.json`:

```json
{
  "enabledPlugins": {
    "voice-transcript-processor@claude-plugins-official": true
  }
}
```

## License

MIT
