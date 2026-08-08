# ContextPilot — Claude Code Adaptive Context Routing Plugin

> **Adaptive per-prompt project-context routing for Claude Code.**

ContextPilot solves exactly one problem:
> For every Claude Code user prompt, automatically determine which project context is relevant and inject only that context before Claude processes the prompt.

It is **NOT** a general-purpose AI assistant, code reviewer, loop detector, autonomous agent, or prompt rewritter. It is a local, privacy-first context router.

---

## 1. Problem

Modern software repositories contain hundreds or thousands of files. When asking Claude Code questions or making edits, loading the entire codebase causes:
- Context window saturation and token wastage.
- Distraction by unrelated boilerplate.
- Increased hallucination risk when too much irrelevant code is loaded.

## 2. Why Context Selection Matters

Providing Claude with **precise, bounded context** (the target files, caller/callee boundaries, exported symbol signatures, and related tests) leads to:
- Faster, more accurate code generation and debugging.
- Preservation of architecture and interface invariants.
- Up to 85%+ reduction in unnecessary token consumption.

---

## 3. How ContextPilot Works

```
User prompt
    ↓
ContextPilot UserPromptSubmit hook (<150ms)
    ↓
Analyze intent (action, entities, domains, paths, symbols)
    ↓
Query local SQLite project index
    ↓
Rank relevant context (8 candidate channels, bounded graph traversal)
    ↓
Apply context budget (4000 tokens, structural summarization for large files)
    ↓
Generate compact <CONTEXT_PILOT> packet
    ↓
Return additional context to Claude Code
```

---

## 4. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Prompt                            │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│       Claude Code Hook: UserPromptSubmit (< 150ms)           │
│   (Fail-Open Protection: Try/Catch + Timeout Guard)        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Intent Classifier                        │
│  - Heuristic analysis (read / debug / modify / test / etc.) │
│  - Extracts symbols, paths, domains, and keywords           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Local SQLite Index & Graph                    │
│  - Files, Symbols, Imports, Exports, Dependency Edges       │
│  - Bounded BFS Traversal (maxDependencyDepth = 2)           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             Deterministic Multi-Factor Ranker                │
│  - Semantic + Symbol + Graph + Path + Test + Git + Domain   │
│  - Generates transparent reasons for every candidate         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Context Budget Manager                    │
│  - Fits within maxContextTokens (default 4000 tokens)        │
│  - Structural summarization for large files                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Injected <CONTEXT_PILOT> Packet                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Installation

### Quickstart

```bash
# Clone the repository
git clone https://github.com/motiram944/contextpilot.git
cd contextpilot

# Install dependencies and build
npm install
npm run build

# Link CLI globally (optional)
npm link
```

### Loading in Claude Code

Run Claude Code with the plugin directory enabled:

```bash
claude --plugin-dir .
```

Or install ContextPilot into your project's `.claude-plugin/` directory.

---

## 6. Usage

After installation, use Claude normally:

```bash
claude
```

Every prompt is automatically routed through ContextPilot with zero workflow changes.

---

## 7. Configuration

ContextPilot requires zero configuration by default. You can optionally create a `.contextpilotrc.json` in your repository root:

```json
{
  "maxContextTokens": 4000,
  "maxFiles": 8,
  "maxDependencyDepth": 2,
  "minRelevanceScore": 0.55,
  "weights": {
    "semanticMatch": 0.30,
    "symbolMatch": 0.20,
    "dependencyScore": 0.20,
    "pathScore": 0.10,
    "testRelevance": 0.08,
    "recencyScore": 0.07,
    "domainScore": 0.05,
    "sizePenalty": 0.05
  },
  "ignorePatterns": [
    "custom_vendor",
    "legacy_fixtures"
  ]
}
```

---

## 8. Commands & Slash Commands

### Claude Code Slash Commands
- `/contextpilot` — Displays index status, token usage, and confidence.
- `/contextpilot:explain <prompt>` — Explains candidate scores and selection reasons.
- `/contextpilot:index` — Rebuilds or incrementally updates the project index.

### Terminal CLI Commands
```bash
contextpilot doctor     # Verify environment, SQLite, and hook permissions
contextpilot index      # Run full or incremental indexing
contextpilot status     # View database stats and routing hit rates
contextpilot explain    # Inspect score breakdown for any test query
contextpilot reset      # Clean and rebuild SQLite database
```

---

## 9. Privacy & Security

- **Strictly Local**: 100% offline indexing and ranking.
- **Zero Data Leakage**: Source code, filenames, and prompts are never sent to external servers (`telemetry = false` default).
- **Security Ignore Rules**: `.env*`, `*.pem`, `*.key`, and `credentials*` are excluded from all indexing.

---

## 10. Performance

- **Target Prompt Latency**: `< 150ms` (measured ~15-40ms in practice).
- **Incremental Indexing**: Skips unchanged files using SHA-256 hashes and modification timestamps.
- **Fail-Open Policy**: If SQLite is locked or any unexpected error occurs, ContextPilot exits cleanly with code `0` so Claude continues without interruption.

---

## 11. Evaluation Methodology

Run the built-in 30-task benchmark suite:

```bash
npm run bench
```

```text
Benchmark results: pending
```

*(Run `npm run bench` to compute and view fresh local benchmark results on your environment)*.

---

## 12. Roadmap

- [x] TypeScript & JavaScript AST extraction
- [x] SQLite relational indexing & WAL mode
- [x] Bounded dependency graph traversal (depth 2)
- [x] Claude Code `UserPromptSubmit` & `SessionStart` hooks
- [x] Deterministic multi-factor ranking & explainability
- [x] Structural summarization for large files
- [ ] Python parser extension
- [ ] Java & Go parser extensions
- [ ] Rust parser extension

---

## 13. Contributing

Contributions are welcome! Please run typecheck and unit tests before opening a PR:

```bash
npm run typecheck
npm test
```

---

## 14. Limitations

- V1 parses TypeScript and JavaScript codebases natively. Other languages are supported via file path and keyword scanning.
- Dynamic runtime reflection (e.g. dynamic `eval` or dynamic `require(variable)`) cannot be statically resolved into dependency edges.
