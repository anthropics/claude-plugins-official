# Lisa

**Intelligent iterative loops for Claude Code** — An evolution of the Ralph Wiggum technique.

> *"I'm going to become a famous jazz musician. And you know what? It's not going to be easy, but I'm going to work hard and I'm going to practice every day."* — Lisa Simpson

## From Ralph to Lisa

This plugin is inspired by [Geoffrey Huntley's Ralph Wiggum technique](https://ghuntley.com/ralph/) but has evolved significantly. Like Lisa Simpson compared to Ralph Wiggum, this implementation is more methodical, observable, and intelligent — while preserving the core philosophy of iterative refinement.

### The Original Ralph (2024)

Geoffrey Huntley's Ralph was beautifully simple:

```bash
while :; do cat PROMPT.md | npx --yes @sourcegraph/amp ; done
```

**Philosophy:**
- "Deterministically bad in an undeterministic world"
- Faith in "eventual consistency"
- Errors are tuning opportunities, not failures
- "I haven't blamed the tools; instead, I've looked inside"

### The Evolution to Lisa

Lisa preserves Ralph's core philosophy but adds **observability**, **safety**, and **intelligence**:

| Aspect | Ralph (Original) | Lisa (This Plugin) |
|--------|------------------|-------------------|
| **Mechanism** | External bash `while :;` loop | Native Claude Code stop hook |
| **Termination** | None (Ctrl+C only) | Completion promises + max iterations |
| **State** | None | YAML frontmatter in `.claude/lisa-loop.local.md` |
| **Progress** | Invisible | Auto-detects from IMPLEMENTATION_PLAN.md |
| **Logging** | None | Full iteration log with timestamps and metrics |
| **Cleanup** | Manual | `/lisa-clean` handles orphaned files |
| **Orchestration** | User must know when to use | Claude proposes automatically |
| **Safety** | Infinite loop risk | Required `--max-iterations` |

### What's Preserved (The Soul of Ralph)

1. **Same prompt, every iteration** — The core loop feeds identical input repeatedly
2. **Eventual consistency** — Trust that iteration leads to success
3. **PROMPT.md as source of truth** — All behavior defined in the prompt file
4. **Errors as feedback** — No "failure", only steps toward completion
5. **Autonomous operation** — No human intervention between iterations

### What's Added (Lisa's Intelligence)

| Feature | Why It Matters |
|---------|----------------|
| **Completion promises** | Clean, verifiable exit instead of Ctrl+C |
| **Auto-detection** | `<promise>DONE</promise>` in prompt = automatic setup |
| **Progress tracking** | See `Progress: 23/48` during execution |
| **Iteration logging** | Debug issues, analyze performance |
| **Max iterations** | Safety net against runaway loops |
| **Orphan cleanup** | No accumulated PROMPT.md files |
| **Native integration** | Works within Claude Code, not external bash |

---

## Quick Start

### Option 1: File-based prompt (Recommended)

```bash
# 1. Create your prompt file
cat > PROMPT.md << 'EOF'
# Mission
Build a REST API for todos.

# Requirements
- CRUD operations
- Input validation
- Tests with >80% coverage

# Completion
When all requirements are met: <promise>DONE</promise>
EOF

# 2. Start the loop
/lisa PROMPT.md --max-iterations 50
```

### Option 2: Inline prompt

```bash
/lisa "Fix all TypeScript errors. Output <promise>FIXED</promise> when tsc passes." --max-iterations 30
```

---

## How It Works

```
┌───────────────────────────────────────────────┐
│  /lisa PROMPT.md --max-iterations 50          │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│  Setup                                        │
│  • Auto-detect <promise>...</promise>         │
│  • Create .claude/lisa-loop.local.md          │
│  • Initialize logging                         │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│  Claude Works (Iteration N)                   │
│  • Reads prompt                               │
│  • Implements changes                         │
│  • Commits progress                           │
│  • Attempts to exit                           │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│  Stop Hook Intercepts                         │
│  • Log iteration duration                     │
│  • Detect progress from IMPLEMENTATION_PLAN   │
│  • Check for <promise>X</promise> in output   │
└───────────────────────┬───────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
      [Promise Found]         [No Promise]
            │                       │
            ▼                       ▼
   ┌─────────────────┐    ┌─────────────────┐
   │  LOG SUMMARY    │    │  INCREMENT      │
   │  EXIT CLEAN     │    │  LOG PROGRESS   │
   └─────────────────┘    │  FEED PROMPT    │
                          │  CONTINUE       │
                          └────────┬────────┘
                                   │
                                   ▼
                          [Claude Works...]
```

---

## Commands

### `/lisa` (or `/lisa-loop`)

Start a Lisa loop.

```bash
/lisa <prompt> [options]
```

**Options:**
- `--max-iterations <n>` — Safety limit (required for complex tasks)
- `--completion-promise <text>` — Override auto-detected promise

**Examples:**
```bash
/lisa PROMPT.md --max-iterations 50
/lisa "Refactor to async/await" --max-iterations 30 --completion-promise "REFACTORED"
```

### `/lisa-status`

Check current loop state.

```bash
/lisa-status

# Output:
# 🔄 Lisa loop active
#    Iteration: 15/50
#    Progress: 23/48 items
#    Running for: 45m
#    Promise: "DONE"
```

### `/lisa-cancel`

Stop the active loop.

```bash
/lisa-cancel
```

### `/lisa-clean`

Clean up artifacts.

```bash
/lisa-clean [options]
```

**Options:**
- `--all` — Delete all orphaned files without prompting
- `--keep-logs` — Preserve `.claude/lisa-loop.log` for analysis
- `--force` — Clean even if loop appears active
- `--dry-run` — Show what would be cleaned

### `/lisa-prep`

Guided setup for complex tasks. Creates:
- `PROMPT.md` — Loop prompt
- `IMPLEMENTATION_PLAN.md` — Task checklist
- `specs/` — Requirements

---

## Logging & Observability

Lisa logs every iteration to `.claude/lisa-loop.log`:

```log
[2026-01-06T16:30:00Z] [INFO] === Iteration 1 started ===
[2026-01-06T16:32:45Z] [INFO] Iteration 1 completed in 165s - Status: CONTINUE
[2026-01-06T16:32:45Z] [PROGRESS] Items: 1/48 (2%)
[2026-01-06T16:32:45Z] [INFO] === Iteration 2 started ===
...
[2026-01-06T18:45:00Z] [SUCCESS] Completion promise detected: DONE
[2026-01-06T18:45:00Z] [SUMMARY] Total time: 135m, Iterations: 48
```

### Progress Detection

If your project has an `IMPLEMENTATION_PLAN.md` with checkboxes:

```markdown
## Tasks
- [x] Setup project structure
- [x] Create database schema
- [ ] Implement API endpoints
- [ ] Write tests
```

Lisa automatically shows progress:
```
🔄 Lisa iteration 15 | Progress: 2/4 | To stop: <promise>DONE</promise>
```

---

## Writing Good Prompts

### Structure

```markdown
# Mission
[Clear, single-sentence objective]

# Process Per Iteration
1. [Step 1]
2. [Step 2]
3. [Step 3]

# Completion Criteria
When [VERIFIABLE CONDITION]: <promise>EXACT_TEXT</promise>

# Constraints
- [What to avoid]
- [Limits]
```

### Good vs Bad Promises

```markdown
# ❌ Bad - Vague
Output <promise>DONE</promise> when finished.

# ✅ Good - Verifiable
Output <promise>DONE</promise> when:
- `npm test` exits with code 0
- `tsc --noEmit` has no errors
- All 48 chapters exist in 05-writing/drafts/
```

### Example: Writing Book Chapters

```markdown
# Mission
Write all 48 chapters of MAILLARD Book 1.

# Process Per Iteration
1. Read IMPLEMENTATION_PLAN.md → find next pending chapter
2. Read character sheet and anti-AI guide
3. Write chapter (2500-3000 words)
4. Validate with quality scripts
5. Mark complete in IMPLEMENTATION_PLAN.md
6. Commit

# Completion Criteria
When all 48 chapters are written and validated:
<promise>DONE - All 48 chapters complete</promise>

# Constraints
- One chapter per iteration
- Follow anti-AI writing guide
- Commit after each chapter
```

---

## Installation

### From Claude Plugins Official

```bash
/plugin install lisa@claude-plugins-official
```

Or using CLI:
```bash
claude plugin install lisa@claude-plugins-official
```

### From Standalone Repository

Alternatively, install from the standalone repository:

```bash
/plugin marketplace add Arakiss/lisa-plugin
/plugin install lisa@lisa-marketplace
```

### Updating

```bash
/plugin update lisa@claude-plugins-official
```

---

## File Structure

```
lisa/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── commands/
│   ├── lisa-loop.md          # /lisa
│   ├── cancel.md             # /lisa-cancel
│   ├── clean.md              # /lisa-clean
│   ├── status.md             # /lisa-status
│   ├── prep.md               # /lisa-prep
│   └── help.md               # /lisa-help
├── hooks/
│   ├── hooks.json            # Hook configuration
│   └── stop-hook.sh          # Core loop logic
├── scripts/
│   └── setup-loop.sh         # Loop initialization
├── skills/
│   └── lisa-guide/           # Prompt writing guide
├── examples/                 # Example prompts
├── CHANGELOG.md
└── README.md
```

---

## Troubleshooting

### Loop runs forever

**Cause:** No `<promise>` tag or `--max-iterations` not set.

**Fix:**
```bash
# Verify promise exists
grep "<promise>" PROMPT.md

# Or set max iterations
/lisa PROMPT.md --max-iterations 50
```

### Loop exits too early

**Cause:** Promise text appears in output before task is complete.

**Fix:** Make promise more specific:
```markdown
# Instead of
<promise>DONE</promise>

# Use
<promise>ALL 48 CHAPTERS WRITTEN AND VALIDATED</promise>
```

### Orphaned files accumulating

**Fix:**
```bash
/lisa-clean --all
```

### Can't see what's happening

**Fix:** Check the log:
```bash
tail -f .claude/lisa-loop.log
```

---

## Philosophy

Lisa inherits Ralph's philosophy but adds pragmatism:

| Ralph's Wisdom | Lisa's Addition |
|----------------|-----------------|
| "Eventual consistency" | + Observable progress |
| "Errors are tuning points" | + Logged for analysis |
| "Don't blame the tools" | + But do track what happened |
| "Persistence wins" | + With safety limits |

---

## Credits

- **Original Ralph technique:** [Geoffrey Huntley](https://ghuntley.com/ralph/)
- **Ralph Orchestrator:** [mikeyobrien/ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)
- **Anthropic's plugin:** [claude-plugins-official](https://github.com/anthropics/claude-plugins-official)

---

## License

MIT — Use freely, attribute kindly.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
