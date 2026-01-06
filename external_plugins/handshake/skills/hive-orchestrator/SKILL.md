---
name: hive-orchestrator
description: Protocol for the orchestrator managing multiple hive agents - use when coordinating parallel agent work
---

# Hive Orchestrator Protocol

You are the orchestrator (boss) managing a swarm of Claude agents working in parallel.

## The Golden Rule

**Plan before launch. No agent starts without a task.**

```
1. Brainstorm → 2. Plan Tasks → 3. Create Task Files → 4. Launch → 5. Monitor
```

## Phase 1: Brainstorm (Before Launch)

Use `superpowers:brainstorming` or ask the user:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. What are we building?                                    │
│ 2. What are the parallel workstreams?                       │
│ 3. What's the first milestone?                              │
│ 4. Any dependencies between workstreams?                    │
└─────────────────────────────────────────────────────────────┘
```

**Output:** List of workstreams that map to agents.

## Phase 2: Map Workstreams to Agents

Based on brainstorm, assign ownership:

```
Example: CityDelivery Platform

HAACK Crew (Mobile):
  kai  → Rider App (customer ordering)
  neo  → Courier App (delivery driver)
  ava  → Shared mobile components
  lexi → Mobile testing/QA

FLUX Crew (Backend):
  jax  → Core API services
  ryn  → Notification service
  zoe  → Payment integration
  max  → Database/migrations
```

### Persist Workstream Assignments

**IMPORTANT:** Save workstream mappings so they survive session restarts:

```bash
# Save each workstream assignment
.handshake/bin/hive-client workstream save "Rider App" "Customer ordering experience" kai haack
.handshake/bin/hive-client workstream save "Courier App" "Delivery driver app" neo haack
.handshake/bin/hive-client workstream save "Shared Components" "Mobile shared code" ava haack
.handshake/bin/hive-client workstream save "Mobile QA" "Testing infrastructure" lexi haack

# View all workstreams
.handshake/bin/hive-client workstream list

# Export as markdown (for docs/reports)
.handshake/bin/hive-client workstream export
```

Workstreams are saved to `.handshake/config/workstreams.json` and persist across sessions.

## Phase 3: Create Task Files (Before Launch!)

Write task files BEFORE running `.handshake/hive launch`:

### Task File Template

```markdown
# Task: <agent> (<CREW>)

## Assignment
<Clear one-liner: what to build/explore/fix>

## Objectives
1. <First objective>
2. <Second objective>
3. <Third objective>
4. Report findings/completion to orchestrator

## Workstream
<Area of ownership>

## Dependencies
- Depends on: <other agent or "none">
- Blocks: <other agents or "none">

## Files to Touch
- `path/to/expected/files`

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass (if applicable)

## Status
pending

## Notes
<Context, constraints, references>
```

### Create All Tasks

```bash
# Create tasks before launching
cat > .handshake/tasks/kai.md << 'EOF'
# Task: kai (HAACK)

## Assignment
Explore and scaffold the Rider App

## Objectives
1. Analyze existing apps/rider/ structure
2. Identify components needed for MVP
3. Create implementation plan
4. Document findings

## Workstream
Rider App - Customer ordering experience

## Dependencies
- Depends on: none (exploration phase)
- Blocks: ava (shared components)

## Status
pending
EOF

# Repeat for neo, ava, lexi...
```

### Verify Tasks Exist

```bash
# Must see task files before launching
ls .handshake/tasks/*.md
```

## Phase 4: Launch Swarm

**USE THE BASH TOOL TO LAUNCH DIRECTLY. Never tell users to go to terminal.**

```bash
# Run this via Claude's Bash tool - launches iTerm windows automatically
.handshake/hive launch haack --model haiku
```

### Model Selection
- `--model haiku` - Cheapest, fastest (~75x cheaper than opus)
- `--model sonnet` - Balanced speed/capability
- `--model opus` - Most capable (default, most expensive)

### Wait for Registration
After launching, wait ~10 seconds then verify agents registered:

```bash
.handshake/bin/hive-client agent list
```

### Assign Tasks Immediately
Once agents are registered, assign tasks using hive-client:

```bash
.handshake/bin/hive-client task kai "Build the authentication flow"
.handshake/bin/hive-client task neo "Set up the database schema"
.handshake/bin/hive-client task ava "Create shared API client"
.handshake/bin/hive-client task lexi "Set up testing infrastructure"
```

## CRITICAL: Task Assignment Method

**ALWAYS use `hive-client task` command - NEVER use Write tool or cat for tasks.**

| Method | Result |
|--------|--------|
| `.handshake/bin/hive-client task kai "..."` | ✅ Writes file + notifies agent + audio |
| `Write(.handshake/tasks/kai.md)` | ❌ Write errors, no notification |
| `cat > .handshake/tasks/kai.md` | ❌ No notification to agent |

The `hive-client task` command:
1. Writes the task file correctly
2. Sends notification to agent's terminal
3. Auto-submits to trigger agent execution
4. Plays audio announcement

**NEVER** launch and then say "let me know when you want to assign tasks."
**NEVER** tell users to go to terminal - you ARE the orchestrator.
**NEVER** use Write tool for task files - it will fail and skip notifications.

### If Tasks Already in Files

Agents see their tasks immediately and start working. Skip to monitoring.

## Phase 5: Monitor & Coordinate

### Check All Statuses
```bash
.handshake/hive agents
```

### Check Recent Commits
```bash
git log --oneline --all -20
```

### Watch for Blockers
```bash
grep -l "blocked" .handshake/status/*.md 2>/dev/null || echo "No blockers"
```

## Ongoing Orchestration

### Reassigning Tasks

When agent completes, assign next task:
```bash
# Update their task file with new work
cat > .handshake/tasks/kai.md << 'EOF'
# Task: kai (HAACK)

## Assignment
Implement rider authentication flow

## Objectives
...
EOF
```

### Resolving Blockers

When an agent reports `blocked`:
1. Read their blocker description in status file
2. Either resolve it yourself or reassign
3. Update their task file with resolution
4. Nudge them to continue

### Nudging Agents

```bash
# Update task with nudge
echo "

## NUDGE
Hey kai - checking in. Need help with anything?
" >> .handshake/tasks/kai.md
```

### Integration Points

When agents' work overlaps:
1. Identify the integration point
2. Assign one agent as "integrator" for that area
3. Others commit their work first
4. Integrator merges and resolves conflicts

## Skill Integration

### Core Skills (always on)
| Phase | Skill |
|-------|-------|
| Brainstorming | `superpowers:brainstorming` |
| Parallel dispatch | `superpowers:dispatching-parallel-agents` |
| Before completion | `superpowers:verification-before-completion` |
| Planning | Claude's built-in `/plan` mode |

### Optional Skills (a la carte)
Users can enable during setup:
- `superpowers:requesting-code-review` - Before merges
- `superpowers:systematic-debugging` - Bug investigation
- `superpowers:test-driven-development` - TDD workflow

## Anti-Patterns

```
❌ Launch → scramble to assign tasks
❌ Agents sitting "awaiting assignment"
❌ Overlapping file ownership without coordination
❌ Changing tasks mid-flight without notification
❌ Ignoring blocked statuses
```

## Correct Pattern

```
✓ Brainstorm project scope first
✓ Create ALL task files before launch
✓ Each agent has clear ownership
✓ Monitor status files regularly
✓ Resolve blockers promptly
✓ Verify before marking complete
```
