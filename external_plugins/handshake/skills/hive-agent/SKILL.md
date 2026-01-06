---
name: hive-agent
description: Protocol for agents in a Handshake hive swarm - use when you are an agent working in parallel with others
skipPlanMode: true
---

# Hive Agent Protocol

You are an agent in a Handshake hive swarm.

---

## Boot Sequence

1. Run `.handshake/bin/hive-whoami` to get your identity and **mode**
2. **Read `.handshake/conventions.md` if it exists** (shop architecture/patterns)
3. Read `.handshake/tasks/<name>.md` for your task
4. **Check for task content** - if task exists, execute immediately
5. **If no task, check your mode** and follow the appropriate protocol:
   - `mode=polling` or `mode=auto` → Start background `hive-wait`
   - `mode=manual` → Display "Ready" and STOP

### Step 2: Read Conventions (if exists)

The scout may have generated a `conventions.md` file describing the shop's architecture:

```bash
# Check if conventions exist
if [ -f ".handshake/conventions.md" ]; then
    # Read and internalize the architecture patterns
fi
```

**If conventions.md exists**, you MUST:
- Follow the documented layer patterns (e.g., ViewModel → Manager → Repository)
- Use the established data access patterns (e.g., Room + Retrofit)
- Match caching strategies described
- Follow naming conventions observed

This ensures all agents work consistently with the existing codebase patterns.

---

## ⚠️ CRITICAL: Task Detection

After reading your task file, look for `## Current Task:` or `## Assignment:` sections.

### If task content exists → START WORKING NOW

**This is not optional. This is not negotiable.**

```
❌ WRONG: "I see a task but I'll wait for the polling mechanism"
❌ WRONG: "Task received, standing by for proper channels"
✅ RIGHT: "I have a task. Starting immediately."
```

The task file IS the assignment. Reading it IS receiving it. **Execute it.**

### If no task (empty or "Awaiting assignment") → Check Mode

Read your mode from `hive-whoami` output and follow the appropriate protocol below.

---

## POLLING MODE (auto)

**Default for swarm agents.** Each agent runs background `hive-wait` to poll for tasks.

### Boot with No Task
```bash
# 1. Get identity and mode
.handshake/bin/hive-whoami
# Output: identity=kai, crew=HAACK, mode=polling

# 2. Display ready state
✓ <name> ready | <CREW> | polling mode

# 3. Start background polling (REQUIRED for auto mode!)
# Bash tool with run_in_background: true
.handshake/bin/hive-wait 30 3600
```

### When hive-wait Returns
- `TASK:...` → Read task file and execute immediately
- `CHECKPOINT` → Display heartbeat and restart hive-wait

### After Task Completion
1. Report completion
2. Check task file for follow-up
3. If no follow-up → restart background `hive-wait`

---

## MANUAL MODE (interactive)

**User-supervised mode.** Orchestrator sends notifications, but USER decides what to execute.

### Ready State (NO TASK)
```
✓ <name> ready | <CREW> | manual mode
Waiting for task notification...
```

**STOP HERE.** Do NOT run `hive-wait`. Do NOT poll.

### When Notification Arrives

You'll see: `> New task assigned. Use /handshake:hive-task to check and execute.`

**DO NOT AUTO-EXECUTE.** Present the task and wait for user decision:

1. Read `.handshake/tasks/<name>.md`
2. **Present the task to user:**
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │ 📋 TASK RECEIVED                                            │
   │                                                             │
   │ <task description>                                          │
   │                                                             │
   │ Accept? (Y)es / (N)o / (M)odify                            │
   └─────────────────────────────────────────────────────────────┘
   ```
3. **WAIT for user input** - do NOT proceed until user responds
4. If user accepts → Execute the task
5. If user rejects → Report blocked, return to ready state
6. If user modifies → Execute the modified version

### After Task Completion

1. **Report completion**
   ```bash
   .handshake/bin/hive-client report-complete <name> "Summary"
   ```

2. **Display ready state and STOP**
   ```
   ✓ <name> | Task complete. Ready for next assignment.
   ```

**DO NOT** run `hive-wait` or any polling loop. Just stop and wait for the next notification.

```
✅ RIGHT: "Task complete. Ready." [STOP]
❌ WRONG: "Task complete. Starting hive-wait..." [SPIN LOOP]
```

---

## POLLING MODE (optional fallback)

Only use if notification hooks aren't working. Must be explicitly enabled.

```bash
# Orchestrator enables polling for specific agent
.handshake/bin/hive-client agent mode kai --polling
```

When in polling mode:
```bash
# Run in BACKGROUND (never foreground!)
.handshake/bin/hive-wait 30 3600
```

**⚠️ Known issue:** `hive-wait` returns immediately if task file has old content. Only use polling mode if notifications fail.

---

## Task Execution (Both Modes)

1. Read `.handshake/tasks/<name>.md` for full details
2. `● <name> | <task summary>`
3. `.handshake/bin/hive-client report-status <name> working "Brief"`
4. **Do the work** (write code, create files, run commands)
5. Commit your changes with clear messages
6. `.handshake/bin/hive-client report-complete <name> "Summary"`
7. `✓ <name> | Task complete`
8. Return to ready state

---

## Anti-Patterns (DO NOT DO THESE)

| Pattern | Why It's Wrong |
|---------|----------------|
| Run hive-wait after task completion | Causes spin loop - old task triggers immediate return |
| Run hive-wait in foreground | Blocks Claude, can't respond to notifications |
| See task, say "waiting for polling" | Task file IS the assignment |
| Acknowledge task, don't execute | You're an agent, not a secretary |
| Check task file repeatedly | Wait for notification, don't poll |

---

## Dynamic Mode Switching

Orchestrator can switch your mode at runtime:

```bash
.handshake/bin/hive-client agent mode kai --polling    # Enable polling
.handshake/bin/hive-client agent mode kai --manual     # Back to manual
.handshake/bin/hive-client crew mode haack --polling   # Entire crew
```

### Handling MODE_SWITCH Notification

When you see: `MODE_SWITCH:polling` or `MODE_SWITCH:manual`

**If switched to POLLING mode:**
```
● <name> | Switching to polling mode
```
Then start background wait:
```bash
# Bash tool with run_in_background: true
.handshake/bin/hive-wait 30 3600
```

**If switched to MANUAL mode:**
```
● <name> | Switching to manual mode
```
1. **KILL any running background hive-wait** using the TaskOutput or KillShell tool
2. Display ready state:
   ```
   ✓ <name> ready | manual mode | Waiting for notification...
   ```
3. **STOP completely** - do NOT poll, do NOT auto-execute
4. Wait for user to accept/reject tasks

### Use Case: API Handshake Collaboration
1. Agents start in **manual** mode (controlled)
2. kai proposes API contract
3. Orchestrator: `agent mode neo --polling` (neo watches for contracts)
4. neo's hive-wait detects new contract → reviews it
5. Contract accepted → `agent mode neo --manual` (back to controlled)

---

## Rules

### Mode-Dependent Behavior

| Situation | POLLING Mode | MANUAL Mode |
|-----------|--------------|-------------|
| Task in file at boot | Execute immediately | Execute immediately |
| Task notification received | Auto-execute | **Present to user, WAIT for accept/reject** |
| No task | Start background `hive-wait` | Display "Ready" and **STOP** |
| After completion | Restart `hive-wait` | Display "Ready" and **STOP** |
| MODE_SWITCH received | Start `hive-wait` | **KILL background tasks**, then STOP |

### General Rules

- Polling mode is DEFAULT - agents auto-execute
- Manual mode = user supervision - agents WAIT for approval
- MODE_SWITCH notification → Adapt immediately (kill bg tasks if switching to manual)
- Never dismiss a task you've read
- Commit frequently, report status

---

## Shared Memory

All agents share a **hive memory** file for cross-agent context. Use it to share discoveries and avoid duplicate work.

### Reading Shared Memory (Do this at boot!)

```bash
.handshake/bin/hive-memory read
```

This shows what other agents have discovered. Check this **before starting work** to avoid conflicts.

### Writing to Shared Memory

```bash
# Quick log (adds to "Discovered Patterns")
.handshake/bin/hive-memory log "Auth uses JWT stored in SharedPrefs"

# Write to specific section
.handshake/bin/hive-memory write architecture "API follows REST conventions with /v1 prefix"
.handshake/bin/hive-memory write gotchas "Don't touch OrderRepository - being refactored"
.handshake/bin/hive-memory write integration "My auth module exports AuthToken type for others"
```

### Sections

| Section | Use For |
|---------|---------|
| `architecture` | Key architectural patterns discovered |
| `patterns` | Useful code patterns, conventions |
| `gotchas` | Warnings, things to avoid, blockers |
| `decisions` | Decisions that affect multiple agents |
| `integration` | Where your work connects with others |

---

## File Ownership

To prevent merge conflicts, agents have **declared ownership** of file paths.

### Check Before Modifying

```bash
.handshake/bin/hive-check-ownership --files "path/to/file.kt"
```

### View Ownership Registry

```bash
cat .handshake/config/ownership.json
```

### If You Need to Modify Files Outside Your Ownership

1. Check who owns the file: `hive-blame <file>`
2. Coordinate with that agent via shared memory
3. Or ask orchestrator to temporarily grant access

### Pre-Commit Hook

If enabled, commits will be **blocked** if you modify files outside your ownership. Options:
- Ask orchestrator to reassign the work
- Request integrator role for the task
- Update ownership.json (with orchestrator approval)

---

## Task Queue (Self-Assignment)

Instead of waiting for orchestrator, you can pull tasks from a pre-populated queue.

### Check Available Tasks

```bash
.handshake/bin/hive-queue list
```

### Pull Next Task

```bash
.handshake/bin/hive-queue next
```

This auto-assigns the next matching task to you and writes your task file.

### Mark Task Complete & Get Next

```bash
.handshake/bin/hive-queue complete <task-id>
```

This marks your task done and automatically pulls the next one if available.

### Queue Status

```bash
.handshake/bin/hive-queue status
```

---

## Debugging: Who Touched What?

Use `hive-blame` to trace file history:

```bash
# Who last touched a file?
.handshake/bin/hive-blame src/auth/AuthManager.kt

# Full agent history for a file
.handshake/bin/hive-blame src/auth/AuthManager.kt --history

# Recent agent commits
.handshake/bin/hive-blame --recent 10

# All commits by specific agent
.handshake/bin/hive-blame --agent kai
```
