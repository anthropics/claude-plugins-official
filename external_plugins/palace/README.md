# Palace - Multi-Agent Decision System (三省六部)

A structured decision-making plugin inspired by the Tang Dynasty's **Three Departments & Six Ministries** (三省六部) system. Nine AI agents collaborate to analyze decisions from multiple perspectives, producing structured reports with execution plans.

## How It Works

You act as the **Emperor (皇上)** with final approval authority. Claude plays 9 specialized agents in sequence:

**Phase 1 — Three Departments (Decision):**
1. **中书省** (Zhongshu) — Drafts ≥2 decision options
2. **门下省** (Menxia) — Reviews draft, identifies ≥3 risks
3. **尚书省** (Shangshu) — Produces final decision with recommended choice
4. **Emperor Review** — You approve, reject, or modify the decision

**Phase 2 — Six Ministries (Execution):**
5. **吏部** (Personnel) — Role/task assignments
6. **户部** (Finance) — Budget & resource estimates
7. **礼部** (Protocol) — Process & communication plan
8. **兵部** (Military) — Execution steps & milestones
9. **刑部** (Justice) — Risk mitigation strategies
10. **工部** (Works) — Tools, templates & deliverables

## Usage

```
/palace Should I switch from React to Vue for our frontend?
/palace 要不要辞职创业？
```

## Output

Each run produces a structured output directory:
```
outputs/{domain}/decision_{timestamp}/
├── 00_issue.json              # Structured issue
├── 01_zhongshu_draft.json     # Draft options
├── 02_menxia_review.json      # Review & risks
├── 03_shangshu_final.json     # Final decision
├── 04-09_*.json               # Six ministry outputs
├── exec_plan.json             # Execution summary
└── decision.md                # Final report
```

## Features

- Bilingual support (中文/English) — follows your language
- Built-in review & rejection mechanism between departments
- Emperor approval checkpoint before execution phase
- MCP tool integration (Notion, GitHub, etc.) during execution
- No external dependencies — runs entirely within Claude Code

## License

Apache-2.0
