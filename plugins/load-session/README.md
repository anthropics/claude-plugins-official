# Load Session Plugin

Restore working context from a previous Claude Code session so you can continue where things left off — without re-explaining everything.

## Overview

When you start a new session, Claude has no memory of what was built, discussed, or decided before. This plugin reads the previous session's JSONL transcript and surfaces a structured summary: what the user asked for, which files were changed, which Jira tickets were referenced, and what was in progress at the end.

## Skills

### `/load-session`

**Trigger phrases:**
- "load context from last session"
- "qué hicimos la vez pasada"
- "cargá el contexto de la sesión anterior"
- `/load-session [session-id]`

**What it does:**
1. Runs `parse-session.mjs` against the most recent (or specified) session JSONL file for the current project
2. Extracts user messages, edited files, Jira ticket references, and last assistant state
3. Presents a formatted context summary
4. Asks what to continue

**Example output:**
```
## Contexto cargado — sesión abc12345
📅 2026-06-18 09:00 → 2026-06-18 17:30 · 42 turnos

### Lo que se pidió
1. Agregar capturas de pantalla como evidencia en tickets Jira MR-2724 a MR-2733
2. Quitar botones "Jira Equipo" y "Métricas Equipo" del dashboard

### Archivos modificados
- C:/copilot/token-dashboard/server.js

### Tickets Jira referenciados
MR-2724, MR-2725, MR-2726, MR-2727, MR-2728, MR-2729, MR-2730, MR-2731, MR-2732, MR-2733

### Último estado (fin de sesión)
Se eliminaron los dos botones del dashboard y se reinició el servidor.
```

**Specific session by ID:**
```
/load-session 1ebf02f5
```

**List all sessions:**
```
/load-session  →  "mostrá todas las sesiones"
```

## Implementation

The skill uses `parse-session.mjs` — a Node.js script that:
- Finds the session JSONL files under `~/.claude/projects/<project-key>/`
- Reads the first 3 MB + last 1 MB of large files (captures start and end of long sessions)
- Extracts user messages, tool calls (Write/Edit for file tracking), Jira ticket references, and assistant text

## Requirements

- Node.js (any recent version)
- Claude Code with the session JSONL files present under `~/.claude/projects/`
