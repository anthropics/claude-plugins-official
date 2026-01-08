---
description: "Start Ralph Loop in current session"
argument-hint: "PROMPT [--max-iterations N] [--completion-promise TEXT]"
allowed-tools: ["Bash", "Write"]
hide-from-slash-command-tool: "true"
---

# Start Ralph Loop

Parse these arguments: `$ARGUMENTS`

Extract:
- `--max-iterations N` (default: 0 = unlimited)
- `--completion-promise TEXT` (default: null)
- Everything else is the PROMPT

First run: `mkdir -p .claude`

Then create `.claude/ralph-loop.local.md` with this format:

```
---
active: true
iteration: 1
max_iterations: [N or 0]
completion_promise: [TEXT in quotes, or null]
started_at: "[current UTC timestamp]"
---

[THE PROMPT TEXT]
```

After creating the file, output:
```
🔄 Ralph loop activated!

Iteration: 1
Max iterations: [N or unlimited]
Completion promise: [TEXT or none]

When you try to exit, the SAME PROMPT feeds back. To complete (if promise set), output: <promise>TEXT</promise>
```

Then begin working on the prompt task.
