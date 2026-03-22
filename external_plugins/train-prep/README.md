# Train_Prep — Claude Code Plugin

A Claude Code plugin that encapsulates a complete **AI consulting training material preparation workflow** — from industry pain point research to delivering a Word report and interactive HTML presentation, all orchestrated with multi-agent parallelism.

## What It Does

Given a client and industry context (+ optional reference PDFs), the `Train_Prep` skill will:

1. **Research** (parallel agents) — Analyze industry pain points across 3 business phases, map them to AI solutions
2. **Word Report** — Assemble a structured `.docx` solution proposal via pandoc
3. **HTML Slides** — Generate an interactive, full-screen HTML presentation with keyboard/touch navigation

## Demo Output

The skill was originally created to prepare training materials for Pearl River Delta intercity rail executives. It produced:
- A 40-pain-point solution proposal Word report
- A 34-slide interactive HTML training presentation

## Installation

### Option 1: Install from GitHub (recommended)

```bash
# Coming soon — marketplace listing
```

### Option 2: Manual Install

```bash
# Clone the repo
git clone https://github.com/leeon/claude-train-prep.git ~/.claude/plugins/local/train-prep

# Register in ~/.claude/plugins/installed_plugins.json
# Add to "plugins" object:
# "train-prep@local": [{ "scope": "user", "installPath": "~/.claude/plugins/local/train-prep", "version": "local" }]

# Enable in ~/.claude/settings.json
# Add to "enabledPlugins": { "train-prep@local": true }
```

## Usage

Once installed, trigger the skill by saying:

- `Train_Prep`
- `给 [客户名] 准备 AI 赋能培训材料`
- `Prepare training materials for [industry] client`
- `制作培训方案，客户是 [X]，业务场景是 [Y]`

Claude will ask for:
1. Client/industry context
2. Reference PDFs (your capability deck + case studies)
3. Output directory

## Prerequisites

```bash
brew install poppler pandoc   # macOS
# or
sudo apt-get install poppler-utils pandoc   # Linux
```

## Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Train_Prep Workflow                │
├─────────────────────────────────────────────────────┤
│  Phase 1: Research (3 parallel agents)               │
│    Agent A ──► Phase 1 pain points + solutions       │
│    Agent B ──► Phase 2 pain points + solutions       │
│    Agent C ──► Phase 3 pain points + impl. plan      │
├─────────────────────────────────────────────────────┤
│  Phase 2: Word Report                                │
│    Assemble Markdown ──► pandoc ──► .docx            │
├─────────────────────────────────────────────────────┤
│  Phase 3: HTML Slides (4 parallel agents)            │
│    Agent A ──► HTML framework + CSS + JS + cover     │
│    Agent B ──► Phase 1 slides                        │
│    Agent C ──► Phase 2 slides                        │
│    Agent D ──► Phase 3 + impl. plan + closing        │
│    Main ────► macOS-compatible assembly script       │
└─────────────────────────────────────────────────────┘
```

## Plugin Structure

```
claude-train-prep/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── Train_Prep/
        ├── SKILL.md                    # Core skill (triggers + workflow)
        └── references/
            └── workflow-guide.md       # Detailed code templates & checklist
```

## Key Technical Notes

- **PDF extraction**: Uses `pdftotext` (more reliable than Claude's built-in PDF reader for text extraction)
- **macOS compatibility**: `head -n -N` (negative line count) is not supported on macOS — the skill uses `lines=$(wc -l < file); head -n $((lines-N)) file` instead
- **HTML assembly**: Multi-agent HTML parts use a strict interface contract (Part 1 leaves `slide-container` unclosed; Part 4 closes it with `</body></html>`)
- **Dynamic slide counting**: Uses `MutationObserver` instead of hardcoded totals, enabling agents to work independently without coordination

## License

MIT License — see [LICENSE](LICENSE)

## Contributing

PRs welcome! Especially:
- Additional industry examples in `references/`
- Improved HTML slide templates
- Better ROI calculation frameworks
