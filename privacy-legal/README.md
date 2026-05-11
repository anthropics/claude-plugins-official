# Privacy Counsel Plugin

In-house privacy counsel workflows: DPA review, DSAR response drafting, PIA generation, and regulation-to-policy gap analysis. Built around a team practice profile learned from your actual privacy policy, DPA template, and a reference PIA.

**Every output is a draft for attorney review — cited, flagged, and gated — not a legal conclusion.** The plugin does the work: reads the documents, applies your playbook, finds the issues, drafts the memo. A lawyer reviews, verifies, and decides. Citations are tagged by source so you know which ones came from a research tool and which ones need checking. Privilege markers are applied conservatively so nothing waives by accident. Consequential actions — filing, sending, executing — are gated behind explicit confirmation.

## Who this is for

| Role | Primary workflows |
|---|---|
| **Privacy counsel** | DPA review, PIA sign-off, reg gap analysis |
| **Privacy program manager** | DSAR handling, PIA intake, vendor privacy review |
| **Product counsel** | PIA generation for launches |
| **Support / CS** | DSAR first-line response (with escalation) |

## First run: the cold-start interview

The plugin interviews you to learn: are you a controller or processor, which regulations actually apply, what you will and won't agree to in a DPA. Then it reads three seed documents — your privacy policy, your DPA template, one PIA you're happy with — and learns your real positions and house style.

Your configuration is stored at `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` and survives plugin updates.

```
/privacy-legal:cold-start-interview
```

## Commands

| Command | Does |
|---|---|
| `/privacy-legal:cold-start-interview` | Cold-start interview |
| `/privacy-legal:use-case-triage [activity]` | Does this need a PIA? Quick classification + conditions |
| `/privacy-legal:dpa-review [file]` | Review a DPA against your playbook (auto-detects direction) |
| `/privacy-legal:dsar-response` | Walk through a DSAR and draft the response |
| `/privacy-legal:pia-generation [feature]` | Generate a PIA in your house style |
| `/privacy-legal:reg-gap-analysis [regulation]` | Diff a new reg against current policy/practice |
| `/privacy-legal:policy-monitor` | Weekly sweep for policy drift, or direct query for a proposed new practice |
| `/privacy-legal:matter-workspace` | Manage matter workspaces (multi-client private practice only) — new, list, switch, close, none |

## Skills

| Skill | Purpose |
|---|---|
| **cold-start-interview** | Writes CLAUDE.md from interview + seed docs |
| **use-case-triage** | Does this need a PIA / DPIA / can it proceed? Policy conflict check + handoffs |
| **dpa-review** | Bi-directional (processor/controller) DPA term-by-term review |
| **dsar-response** | Identity verification → system walk → exemptions → response draft |
| **pia-generation** | PIA in house format, with policy consistency check |
| **reg-gap-analysis** | New reg vs. current state, remediation plan |
| **policy-monitor** | Crawls outputs for practice drift; drafts policy language updates |
| **matter-workspace** | Create, list, switch, and close matter workspaces for multi-client practices; isolates each client/matter so context does not leak across them |

## Quick start

### 1. Setup

```
/privacy-legal:cold-start-interview
```

Have ready: your public privacy policy URL, your standard DPA, one reference PIA.

### 2. Triage a new feature or processing activity

```
/privacy-legal:use-case-triage "Marketing wants to use behavioral data for ad personalization"
```

Output: PROCEED / PIA REQUIRED / DPIA MANDATORY / STOP — with conditions table, lawful basis
question, and offer to kick off the PIA in the same conversation.

### 3. Review a customer DPA

```
/privacy-legal:dpa-review customer-dpa.pdf
```

Output: direction auto-detected, term-by-term vs. playbook, proposed redlines, policy consistency check.

### 4. Handle a DSAR

```
/privacy-legal:dsar-response
```

Walks you through: classify → verify → locate → exemptions → draft. Uses your systems list from the config CLAUDE.md.

### 5. PIA a new feature

```
/privacy-legal:pia-generation "Location sharing feature"
```

Intake questions → PIA in your house format → policy diff → conditions list.

## How it learns

Your practice profile at `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` isn't static — it improves as you use the plugin. Skills tell you when an output used a default you should tune. The `policy-monitor` skill watches for drift between your policy and your practice and proposes updates. You can re-run setup, edit the file directly, or tell a skill to record a new position.

## File structure

```
privacy-legal/
├── .claude-plugin/plugin.json
├── .mcp.json
├── CLAUDE.md
├── README.md
├── skills/
│   ├── cold-start-interview/
│   ├── use-case-triage/
│   ├── dpa-review/
│   ├── dsar-response/
│   ├── pia-generation/
│   ├── reg-gap-analysis/
│   ├── policy-monitor/
│   └── matter-workspace/
└── hooks/hooks.json
```

## Notes

- DPA review is bi-directional: same skill handles customer DPAs (defend operational flex) and vendor DPAs (protect data). Direction auto-detected, or ask.
- PIA format comes from your seed PIA. If you didn't provide one during setup, it uses a generic structure — re-run setup with a reference PIA to fix.
- Gap analysis (`reg-gap-analysis`) handles incoming regulations. Policy monitor handles internal practice drift. Different tools for different directions of change.
- Policy monitor requires an outputs folder to be configured (set during setup) for the sweep to work. Direct-query mode works without it.
