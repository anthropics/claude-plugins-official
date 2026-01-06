---
description: "Explain Ralph Wiggum technique and available commands"
---

# Ralph Wiggum Plugin Help

Please explain the following to the user:

## What is the Ralph Wiggum Technique?

The Ralph Wiggum technique is an iterative development methodology based on continuous AI loops, pioneered by Geoffrey Huntley.

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

The technique is described as "deterministically bad in an undeterministic world" - failures are predictable, enabling systematic improvement through prompt tuning.

## Available Commands

### /ralph-loop <PROMPT> [OPTIONS]

Start a Ralph loop in your current session.

**Usage:**

```
/ralph-loop "Refactor the cache layer" --max-iterations 20
/ralph-loop "Add tests" --completion-promise "TESTS COMPLETE"
```

**Options:**

- `--max-iterations <n>` - Max iterations before auto-stop
- `--completion-promise <text>` - Promise phrase to signal completion
- `--fresh-context <n>` - Spawn fresh session every N iterations (clears context)

**How it works:**

1. Creates `.claude/.ralph-loop.local.md` state file
2. You work on the task
3. When you try to exit, stop hook intercepts
4. Same prompt fed back
5. You see your previous work
6. Continues until promise detected or max iterations

---

### /cancel-ralph

Cancel an active Ralph loop (removes the loop state file).

**Usage:**

```
/cancel-ralph
```

**How it works:**

- Checks for active loop state file
- Removes `.claude/.ralph-loop.local.md`
- Reports cancellation with iteration count

---

## Key Concepts

### Completion Promises

To signal completion, Claude must output a `<promise>` tag:

```
<promise>TASK COMPLETE</promise>
```

The stop hook looks for this specific tag. Without it (or `--max-iterations`), Ralph runs infinitely.

### Self-Reference Mechanism

The "loop" doesn't mean Claude talks to itself. It means:

- Same prompt repeated
- Claude's work persists in files
- Each iteration sees previous attempts
- Builds incrementally toward goal

### Context Management

By default, the context window accumulates across iterations. For long-running loops, this can lead to context overflow. Use `--fresh-context` to spawn a fresh session periodically:

```
/ralph-loop "Build API" --max-iterations 100 --fresh-context 20
# Context clears at iterations 20, 40, 60, 80
```

**How it works:**

- At specified intervals, the current session ends
- A new Claude session spawns with fresh context
- Previous work persists in files (not lost!)
- The new session continues the loop

## Example

### Interactive Bug Fix

```
/ralph-loop "Fix the token refresh logic in auth.ts. Output <promise>FIXED</promise> when all tests pass." --completion-promise "FIXED" --max-iterations 10
```

You'll see Ralph:

- Attempt fixes
- Run tests
- See failures
- Iterate on solution
- In your current session

## When to Use Ralph

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

- Original technique: https://ghuntley.com/ralph/
- Ralph Orchestrator: https://github.com/mikeyobrien/ralph-orchestrator
