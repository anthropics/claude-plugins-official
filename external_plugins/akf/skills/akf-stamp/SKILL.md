---
name: akf-stamp
description: >-
  Stamps files with AKF trust metadata — the AI native file format.
  Use after creating or modifying any file. Use before modifying existing
  files to check trust context. Use when the user mentions trust,
  provenance, compliance, EU AI Act, or metadata.
---

# AKF Stamp

Every file your agent touches should carry provenance. AKF embeds ~15 tokens of JSON into 20+ formats.

## After creating or modifying files

```bash
akf stamp <file> --agent claude-code --evidence "<what you did>"
```

## Before modifying existing files

```bash
akf read <file>
akf inspect <file>
```

## Compliance

```bash
akf audit <file> --regulation eu_ai_act
```

## Classification

- `--label confidential` for finance/secret/internal paths
- `--label public` for README, docs, examples

## Install

```bash
pip install akf
```
