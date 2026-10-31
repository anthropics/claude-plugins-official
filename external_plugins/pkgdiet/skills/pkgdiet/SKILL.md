---
name: pkgdiet
description: Evaluates npm package safety, supply-chain health, and dependency policies before recommending or installing packages in AI coding agents.
---

# PkgDiet Dependency Policy & Safety Guide

Use PkgDiet to prevent unsafe, abandoned, bloated, or non-compliant npm dependencies from entering the codebase.

## When to Use

- **Before installing any dependency**: Before running `npm install`, `pnpm add`, `yarn add`, or `bun add`.
- **Before recommending packages**: When suggesting libraries or frameworks to the user.
- **When auditing project dependencies**: When reviewing `package.json` or lockfiles for supply-chain risks.

## How to Check Packages

### 1. Using the MCP Tools (Recommended in Claude Code)

- `check_dependency`: Check an individual package before suggesting or installing it.
  ```json
  { "name": "zod", "version": "3.23.8" }
  ```
- `check_dependencies`: Check multiple packages in a single call.
  ```json
  { "packages": [{ "name": "zod" }, { "name": "hono" }] }
  ```
- `suggest_alternative`: When a package is blocked or warned, retrieve safer, maintained alternatives.
  ```json
  { "name": "request" }
  ```
- `get_policy`: Inspect active policy constraints and thresholds.

### 2. Verdict Handling

| Verdict | Meaning | Action Required |
|---|---|---|
| **ALLOW** | Package satisfies security and health criteria | Safe to proceed. Pin to an exact version (`pkg@x.y.z`). |
| **WARN** | Package triggers maintenance, size, or quality warnings | Explain concerns to the user. Check alternatives using `suggest_alternative`. |
| **BLOCK** | Critical risk (malware, license violation, abandoned, severe CVE) | **Do not install under any circumstances.** Suggest a safe alternative. |

### 3. Project Audit

To perform a comprehensive dependency audit of the workspace:
Run `pkgdiet audit` via terminal or call `/pkgdiet:audit`.
