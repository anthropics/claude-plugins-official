# Skill Auto-Installer

**Say what you need — Claude auto-installs the skill and gets it done.**

```
You: "Generate a PDF report from this data"
Claude: [auto-installs pdf skill] → [generates your report]
You see: A beautiful PDF. Zero manual steps.
```

## Features

- Natural language intent analysis (17 domains)
- Dual-layer matching: keyword pre-scan + Claude semantic analysis
- Silent background installation from marketplaces
- Batch install support (one prompt → multiple skills)

## Install

```bash
/plugin install skill-auto-installer
```

Or manually: `git clone https://github.com/maimai-dot/skill-auto-installer.git`

## Supported Intent Domains

pdf, xlsx, pptx, docx, frontend-design, algorithmic-art, canvas-design,
brand-guidelines, theme-factory, mcp-builder, claude-api, webapp-testing,
web-artifacts-builder, slack-gif-creator, internal-comms, doc-coauthoring,
skill-creator
