---
name: load-session
description: Load context from a previous Claude Code session in this project. Use when starting a new session to quickly restore context of what was built, discussed, and decided — without the user re-explaining everything.
---

# Load Session Context

Restore working context from a previous Claude Code session so you can continue where things left off.

## When to use

- User says "load context from last session" / "qué hicimos la vez pasada" / "cargá el contexto de la sesión anterior"
- User pastes a session ID and asks you to load it
- User says "/load-session" with optional session ID or "last"

## Steps

### 1. Run the parser

The script `parse-session.mjs` lives alongside this SKILL.md — use its absolute path.

**Default (latest session):**
```sh
node <skill-dir>/parse-session.mjs
```

**Specific session by ID (user provides UUID or partial):**
```sh
node <skill-dir>/parse-session.mjs <session-id>
```

**Example with skill dir resolved:**
```powershell
$skillDir = Split-Path -Parent (Resolve-Path "<skill-dir>/parse-session.mjs")
node "$skillDir/parse-session.mjs"
```

The script finds sessions in `~/.claude/projects/<project-key>/` based on the current working directory. It outputs JSON with:
- `userMessages` — all user messages (up to 800 chars each)
- `lastAssistantTexts` — last 30 assistant responses
- `filesWritten` / `filesEdited` — files the session touched
- `jiraTickets` — Jira issue references found
- `toolCounts` — how many times each tool was called
- `firstTs` / `lastTs` — session time range
- `turns` — number of assistant turns

### 2. Parse the output

Read the JSON. Focus on:
- `userMessages` — what the user asked for, in chronological order
- `filesEdited` + `filesWritten` — what was built/changed
- `jiraTickets` — issues being worked on
- `lastAssistantTexts` — what was in progress at the end of the session

### 3. Present context summary

Format a clear context summary in Spanish (matching the user's language):

```
## Contexto cargado — sesión [sessionId substring]
📅 [firstTs date] → [lastTs date] · [turns] turnos

### Lo que se pidió
1. [first user message]
2. [second user message]
...

### Archivos modificados
- [file1]
- [file2]

### Tickets Jira referenciados
MR-XXX, MR-YYY

### Último estado (fin de sesión)
[Summary of what the last assistant message was doing / what was left in progress]
```

### 4. Ask what to continue

After presenting the context, ask:
> "¿Querés que continuemos con [last task identified]? ¿O hay algo específico que retomar?"

## Multiple sessions

If the user says "mostrá todas las sesiones" or "listá sesiones", list the available `.jsonl` files from the project dir with their dates and sizes:

```powershell
$cwd = $PWD.Path
$key = $cwd -replace '[:\\\/]', '-' -replace '^-+', ''
Get-ChildItem "$env:USERPROFILE\.claude\projects\$key\*.jsonl" |
  Sort-Object LastWriteTime -Descending |
  Select-Object Name, @{N='KB';E={[math]::Round($_.Length/1KB)}}, LastWriteTime |
  Format-Table -AutoSize
```

Then let the user pick one by ID or number, and run the parser on that file.

## Notes

- The script reads the first 3 MB + last 1 MB of large files — for very long sessions it may miss content in the middle, but captures the start and end reliably.
- Jira tickets are extracted from both user messages and shell commands the assistant ran.
- `truncated: true` in output means the session was large and middle content was skipped.
- If no sessions are found, check the current working directory matches the project where sessions were recorded.
