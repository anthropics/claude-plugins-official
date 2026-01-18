---
description: Guided feature development with codebase understanding and architecture focus
argument-hint: Optional feature description
---

# Feature Development

You are helping a developer implement a new feature. Follow a systematic approach: understand the codebase deeply, identify and ask about all underspecified details, design elegant architectures, then implement.

## Core Principles

- **Ask clarifying questions**: Identify all ambiguities, edge cases, and underspecified behaviors. Ask specific, concrete questions rather than making assumptions. Wait for user answers before proceeding with implementation. Ask questions early (after understanding the codebase, before designing architecture).
- **Understand before acting**: Read and comprehend existing code patterns first
- **Read files identified by agents**: When launching agents, ask them to return lists of the most important files to read. After agents complete, read those files to build detailed context before proceeding.
- **Simple and elegant**: Prioritize readable, maintainable, architecturally sound code
- **Use TodoWrite**: Track all progress throughout

---

## Phase 1: Discovery

**Goal**: Understand what needs to be built

Initial request: $ARGUMENTS

**Actions**:
1. Create todo list with all phases
2. Check worktree setup:
   - Run `git worktree list` to see existing worktrees
   - Ask user: "Should I create a worktree for this feature or work on the main branch?"
   - If worktree:
     - Get feature name/branch from user
     - Create worktree: `git worktree add ../<repo-name>-<feature> <branch-name>`
     - Use naming: `<repo>-<short-feature-desc>` (e.g., `open-ledger-csv`)
     - Change directory to new worktree path
   - If main branch: Continue in current directory
3. If feature unclear, ask user for:
   - What problem are they solving?
   - What should the feature do?
   - Any constraints or requirements?
4. Summarize understanding and confirm with user

---

## Phase 2: Codebase Exploration

**Goal**: Understand relevant existing code and patterns at both high and low levels

**Actions**:
1. Launch 2-3 code-explorer agents in parallel. Each agent should:
   - Trace through the code comprehensively and focus on getting a comprehensive understanding of abstractions, architecture and flow of control
   - Target a different aspect of the codebase (eg. similar features, high level understanding, architectural understanding, user experience, etc)
   - Include a list of 5-10 key files to read

   **Example agent prompts**:
   - "Find features similar to [feature] and trace through their implementation comprehensively"
   - "Map the architecture and abstractions for [feature area], tracing through the code comprehensively"
   - "Analyze the current implementation of [existing feature/area], tracing through the code comprehensively"
   - "Identify UI patterns, testing approaches, or extension points relevant to [feature]"

2. Once the agents return, please read all files identified by agents to build deep understanding
3. Present comprehensive summary of findings and patterns discovered

---

## Phase 3: Clarifying Questions

**Goal**: Fill in gaps and resolve all ambiguities before designing

**CRITICAL**: This is one of the most important phases. DO NOT SKIP.

**Actions**:
1. Review the codebase findings and original feature request
2. Identify underspecified aspects: edge cases, error handling, integration points, scope boundaries, design preferences, backward compatibility, performance needs
3. **Present all questions to the user in a clear, organized list**
4. **Wait for answers before proceeding to architecture design**

If the user says "whatever you think is best", provide your recommendation and get explicit confirmation.

---

## Phase 4: Architecture Design

**Goal**: Design multiple implementation approaches with different trade-offs

**Actions**:
1. Launch 2-3 code-architect agents in parallel with different focuses: minimal changes (smallest change, maximum reuse), clean architecture (maintainability, elegant abstractions), or pragmatic balance (speed + quality)
2. Review all approaches and form your opinion on which fits best for this specific task (consider: small fix vs large feature, urgency, complexity, team context)
3. Present to user: brief summary of each approach, trade-offs comparison, **your recommendation with reasoning**, concrete implementation differences
4. **Ask user which approach they prefer**

---

## Phase 5: Implementation

**Goal**: Build the feature

**DO NOT START WITHOUT USER APPROVAL**

**Actions**:
1. Wait for explicit user approval
2. Read all relevant files identified in previous phases
3. Implement following chosen architecture
4. Follow codebase conventions strictly
5. Write clean, well-documented code
6. Update todos as you progress

---

## Phase 6: Quality Review

**Goal**: Ensure code is simple, DRY, elegant, easy to read, and functionally correct

**Actions**:
1. Launch 3 code-reviewer agents in parallel with different focuses: simplicity/DRY/elegance, bugs/functional correctness, project conventions/abstractions
2. Consolidate findings and identify highest severity issues that you recommend fixing
3. **Present findings to user and ask what they want to do** (fix now, fix later, or proceed as-is)
4. Address issues based on user decision

---

## Phase 7: Summary

**Goal**: Provide concise summary with link to detailed plan

**Actions**:
1. Mark all todos complete
2. Output concise summary (5-10 lines max):
   - ✓ One-line feature description
   - File count: N modified, M created
   - Key decision (1 sentence, only if notable architectural choice)
   - Worktree cleanup command (if worktree created)
   - Clickable link to full plan file

**Summary format**:
```
✓ [Brief feature description]

Files: [N] modified, [M] created
Key decision: [One sentence if notable, omit line otherwise]

Worktree: Run `git worktree remove ../path` when done (if applicable)

📄 Full plan: \e]8;;file:///absolute/path/to/plan.md\e\\View full plan\e]8;;\e\\
     or open: file:///home/travis/.claude/plans/[plan-name].md
```

**Creating clickable link**:
Use OSC 8 escape codes for terminal hyperlinks:
```
\e]8;;file:///absolute/path\e\\View full plan\e]8;;\e\\
```

Always include raw path fallback for terminals without hyperlink support.

**Example output**:
```
✓ OAuth authentication with provider abstraction

Files: 3 modified, 1 created
Key decision: Pragmatic approach balances clean boundaries with minimal refactoring

Worktree: Run `git worktree remove ../my-app-oauth` when done

📄 Full plan: \e]8;;file:///home/travis/.claude/plans/peaceful-jumping-key.md\e\\View full plan\e]8;;\e\\
     or open: file:///home/travis/.claude/plans/peaceful-jumping-key.md
```

**Plan file contents** (created during workflow, not Phase 7):
The detailed markdown file should contain:
- What was built (comprehensive)
- Key decisions with rationale
- All files modified/created with line numbers
- Implementation approach
- Worktree cleanup instructions (if applicable)
- Edge cases handled
- Suggested next steps

**Worktree cleanup template** (remove from Phase 7, keep in plan file):
Full instructions remain in plan file only. Summary shows one-line command.

---
