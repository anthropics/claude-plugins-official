---
description: "Explain Lisa technique and available commands"
---

# Lisa Plugin Help

Please explain the following to the user:

## What is Lisa?

Lisa is an evolution of the [Ralph Wiggum technique](https://ghuntley.com/ralph/), an iterative development methodology pioneered by Geoffrey Huntley.

**Core concept:**
```bash
while :; do
  cat PROMPT.md | claude-code --continue
done
```

The same prompt is fed to Claude repeatedly. The "self-referential" aspect comes from Claude seeing its own previous work in the files and git history, not from feeding output back as input.

**Each iteration:**
1. Claude receives the SAME prompt
2. Works on the task, modifying files
3. Tries to exit
4. Stop hook intercepts and feeds the same prompt again
5. Claude sees its previous work in the files
6. Iteratively improves until completion

Lisa adds observability, safety limits, and progress tracking to the original technique.

## Available Commands

### /lisa-loop <PROMPT> [OPTIONS]

Start a Lisa loop in your current session.

**Usage:**
```
/lisa-loop "Refactor the cache layer" --max-iterations 20
/lisa-loop "Add tests" --completion-promise "TESTS COMPLETE"
```

**Options:**
- `--max-iterations <n>` - Max iterations before auto-stop
- `--completion-promise <text>` - Promise phrase to signal completion

**How it works:**
1. Creates `.claude/lisa-loop.local.md` state file
2. You work on the task
3. When you try to exit, stop hook intercepts
4. Same prompt fed back
5. You see your previous work
6. Continues until promise detected or max iterations

---

### /cancel-lisa

Cancel an active Lisa loop (removes the loop state file).

**Usage:**
```
/cancel-lisa
```

**How it works:**
- Checks for active loop state file
- Removes `.claude/lisa-loop.local.md`
- Reports cancellation with iteration count

---

### /lisa-status

Check the current state of a running Lisa loop.

---

### /lisa-clean

Clean up orphaned files from completed or crashed loops.

---

### /lisa-prep

Prepare prompt files for a Lisa loop (creates PROMPT.md, specs/).

---

## Key Concepts

### Completion Promises

To signal completion, Claude must output a `<promise>` tag:

```
<promise>TASK COMPLETE</promise>
```

The stop hook looks for this specific tag. Without it (or `--max-iterations`), Lisa runs infinitely.

### Self-Reference Mechanism

The "loop" doesn't mean Claude talks to itself. It means:
- Same prompt repeated
- Claude's work persists in files
- Each iteration sees previous attempts
- Builds incrementally toward goal

### Progress Tracking

If an `IMPLEMENTATION_PLAN.md` exists, Lisa will:
- Count `[x]` (completed) and `[ ]` (pending) items
- Show progress in the system message: `Progress: 15/48`
- Log progress to `.claude/lisa-loop.log`

### Iteration Logging

All iterations are logged to `.claude/lisa-loop.log` with:
- Timestamps
- Duration
- Progress
- Summary on completion

## Example

### Interactive Bug Fix

```
/lisa-loop "Fix the token refresh logic in auth.ts. Output <promise>FIXED</promise> when all tests pass." --completion-promise "FIXED" --max-iterations 10
```

You'll see Lisa:
- Attempt fixes
- Run tests
- See failures
- Iterate on solution
- In your current session

## When to Use Lisa

**Good for:**
- Well-defined tasks with clear success criteria
- Tasks requiring iteration and refinement
- Iterative development with self-correction
- Greenfield projects

**Not good for:**
- Tasks requiring human judgment or design decisions
- One-shot operations
- Tasks with unclear success criteria
- Debugging production issues (use targeted debugging instead)

## Learn More

- Original Ralph technique: https://ghuntley.com/ralph/
- Ralph Orchestrator: https://github.com/mikeyobrien/ralph-orchestrator
