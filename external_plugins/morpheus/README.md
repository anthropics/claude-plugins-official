# Morpheus

**"I'm trying to free your mind, Neo."**

Morpheus is a **development protocol** for [Claude Code](https://claude.ai/code) — not a tool, not a runtime, not a package. It's 5 markdown files that tell Claude *when* to check project intelligence, *how* to critique its own code, and *what* to save for next time.

It orchestrates the [EvoIntel MCP suite](https://github.com/evo-hydra) (Sentinel, Seraph, Niobe, Merovingian) into a coherent development cycle. But it works without them too — it just can't see as much.

By [Evolving Intelligence AI](https://evolvingintelligence.ai)

---

## What It Is (and Isn't)

**Morpheus is:** A Claude Code plugin. Markdown files. A protocol that Claude follows. Zero dependencies. Zero code. Zero runtime.

**Morpheus is not:** A sixth tool in the EvoIntel suite. There's nothing to compile, no database, no process to run.

Think of it this way:
- **Sentinel, Seraph, Niobe, Merovingian, Anno** = sensors (tools with runtimes, databases, APIs)
- **Morpheus** = the playbook that tells Claude when to use each sensor

This is the same category as Ralph Wiggum (a bash script + a hook) or CLAUDE.md instructions. The entire dev loop is just structured markdown that Claude follows autonomously.

That's what makes it free to try. `git clone` and you're running it.

---

## What It Does

For each task in a structured plan, Morpheus tells Claude to run these phases in order:

```
BOOTSTRAP (once)     Probe MCP servers, load project intelligence
    |
    v
  CHECK              Sentinel: pitfalls, co-changes, conventions
  CODE               FDMC pre-flight, then implement
  TEST               Run tests, self-heal on failure
  FDMC CRITIQUE      Self-review diff for structural violations
  GRADE              Seraph: mutation testing + quality gate
  COMMIT             Git commit + persist knowledge to Sentinel
  ADVANCE            Update plan, next task
    |
    v
CLOSE (once)         Feedback sweep to all MCP servers
```

No human input between tasks. It checks intelligence before coding, critiques its own work after coding, and saves what it learns for next time.

## What Makes It Different

| Capability | Aider | Cline | Kiro | Ralph Wiggum | Morpheus |
|-----------|-------|-------|------|-------------|----------|
| Pre-flight project intelligence | - | - | - | - | Sentinel |
| Mutation testing quality gate | - | - | - | - | Seraph |
| Runtime observation | - | - | - | - | Niobe |
| API contract verification | - | - | - | - | Merovingian |
| Structured self-critique (FDMC) | - | Verify step | - | - | Pre + post code |
| Cross-session knowledge persistence | - | - | - | - | solution_save |
| Persistent retry on failure | - | - | - | Core strength | Built in |
| Spec-first design | - | - | Core strength | - | Via /plan |
| Feedback loop closure | - | - | - | - | *_feedback tools |

Morpheus is the protocol. The MCP servers are the intelligence. Together they form a complete development cycle. Separately, each still works — Morpheus just becomes a structured plan executor, and the MCP servers become standalone tools you call manually.

---

## Install

**One command:**

```bash
git clone https://github.com/evo-hydra/morpheus ~/.claude/plugins/morpheus
```

That's it. Open Claude Code and `/morpheus` is available. No pip, no npm, no build step.

**Or via script:**

```bash
curl -sSL https://raw.githubusercontent.com/evo-hydra/morpheus/main/install.sh | bash
```

---

## Quick Start

### 1. Create a plan

```
/plan "Add user authentication with JWT tokens and refresh flow"
```

Morpheus generates a structured plan file at `plans/add-auth.md` with ordered tasks, target files, and acceptance criteria.

### 2. Run the loop

```
/morpheus plans/add-auth.md
```

Claude executes every task autonomously: check intelligence, write code, run tests, self-critique, grade, commit, advance. You watch. It ships.

### 3. (Optional) Install MCP servers for full intelligence

The protocol works without any MCP servers — it degrades gracefully. But with them, Claude sees what it otherwise can't:

```bash
pip install git-sentinel    # Project history: conventions, pitfalls, co-changes
pip install seraph-ai       # Quality gate: mutation testing, static analysis
pip install niobe            # Runtime: process metrics, log analysis, anomalies
pip install merovingian      # Contracts: API breaking changes, consumer mapping
```

Each server adds a layer of sight. Sentinel is the highest-value single install.

---

## The FDMC Quality Standard

Every task runs through four lenses — before and after coding:

- **Future-Proof** — Am I coupling to assumptions that will break?
- **Dynamic** — Am I hardcoding something that should be configurable?
- **Modular** — Does each unit have one clear responsibility?
- **Consistent** — Does this match how the codebase already works?

**Consistent is the most violated lens.** Before creating a new class, the protocol checks: where do siblings live? Who owns them? How are they wired in? Match the pattern.

Structural violations (parallel types, wrong ownership model) are fixed before grading. The FDMC result is recorded in every commit message.

---

## How the Protocol Uses MCP Servers

When MCP servers are available, the protocol calls them at specific phases:

### Phase 0: BOOTSTRAP
```
sentinel_project_context  →  Load conventions, pitfalls, decisions, hot files
seraph_history            →  Check for past assessments
```

### Phase 1: CHECK (per task)
```
sentinel_pitfalls(file)   →  What went wrong in this file before?
sentinel_co_changes(file) →  What else needs to change with it?
merovingian_breaking      →  Will this change break consumers?
```

### Phase 3: TEST
```
niobe_snapshot (before)   →  Capture baseline metrics
run tests
niobe_snapshot (after)    →  Capture post-change metrics
niobe_compare             →  Detect regressions
```

### Phase 4: GRADE
```
seraph_assess             →  Mutation testing + static analysis + risk scoring
```

### Phase 5: COMMIT
```
sentinel_solution_save    →  Persist any bugs discovered and their fixes
sentinel_solution_verify  →  Mark confirmed solutions
```

### Phase 7: CLOSE
```
sentinel_feedback         →  Rate the knowledge that was used
seraph_feedback           →  Rate the assessment quality
```

When a server isn't available, the protocol skips those calls and continues. No errors, no degradation beyond the missing intelligence.

---

## Plan File Format

```markdown
---
name: Add Authentication
project: /path/to/project
created: 2026-03-14
test_command: "npm test"
---

## 1. Create JWT Token Service
- **files**: src/auth/jwt.ts, src/auth/types.ts
- **do**: Implement JWT generation and verification with RS256
- **done-when**: Unit tests pass for token creation, validation, and expiry
- **status**: pending

## 2. Add Login Endpoint
- **files**: src/routes/auth.ts, src/middleware/auth.ts
- **do**: POST /auth/login returns access + refresh tokens
- **done-when**: Integration test passes with valid and invalid credentials
- **status**: pending
```

---

## Works With Other Approaches

Morpheus solves the intelligence layer. Other tools solve other layers. They compose:

- **Ralph Wiggum** (persistence) — Wrap stubborn Morpheus tasks in Ralph's retry loop for unlimited attempts with Sentinel intelligence on each iteration
- **Kiro** (specs) — Generate specs in Kiro, feed them into `/plan` for task decomposition, execute with `/morpheus`

The protocol doesn't compete with these. It fills a different gap.

---

## Commands

| Command | Description |
|---------|-------------|
| `/morpheus [plan-file]` | Execute the autonomous dev loop |
| `/plan [description]` | Create a structured plan from a description |
| `/plan [file-path]` | View plan status |

## What's in the Box

```
morpheus/
  .claude-plugin/plugin.json     # Plugin manifest
  commands/morpheus.md            # The dev loop protocol
  commands/plan.md                # Plan creation/viewing
  skills/dev-loop/SKILL.md        # Activation triggers
  skills/plan-create/SKILL.md     # Plan creation triggers
```

5 files. 0 code. The entire dev loop is structured instructions.

---

## The Five Blindnesses

Morpheus exists because AI coding agents are blind to five things no model improvement will fix:

1. **Project history** — Conventions, pitfalls, and decisions locked in git
2. **Runtime behavior** — CPU, memory, errors that require process observation
3. **Cross-service dependencies** — API contracts that span repositories
4. **Code quality beyond "tests pass"** — Mutations that survive mean tests verify nothing
5. **Web content** — 93% of HTML tokens are noise

Each MCP server in the EvoIntel suite gives the agent sight into one blindness. Morpheus is the protocol that tells Claude when to open its eyes.

Read the full thesis: [docs/whitepaper.md](docs/whitepaper.md)

---

## License

MIT

## Credits

Built by [Evolving Intelligence AI](https://evolvingintelligence.ai) | [GitHub](https://github.com/evo-hydra)

Morpheus guides Neo through the Matrix using intelligence from Sentinel, Niobe, Seraph, and Merovingian.
