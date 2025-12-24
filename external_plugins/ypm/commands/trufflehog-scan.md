---
description: "Run TruffleHog security scan on all managed projects"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

# YPM - TruffleHog Security Scan

Run TruffleHog security scan on all YPM-managed projects.

## Overview

This command executes:
1. Run `python scripts/scan_projects.py` to get project list
2. Execute TruffleHog scan on each project
3. Display detected issues clearly

## Execution Steps

### STEP 1: Check TruffleHog Installation

```bash
which trufflehog
```

**If trufflehog is not installed**:
```
TruffleHog is not installed.

Installation:
brew install trufflehog

Please run this command again after installation.
```
-> **Abort process**

### STEP 2: Execute Project Scan

```bash
python scripts/scan_projects.py
```

Read scan results JSON and check `security_scan` info for each project.

### STEP 3: Display Scan Results

#### 3-1. Summary Display

```
## TruffleHog Security Scan Results

**Scan Date**: 2025-11-11 10:30

**Summary**:
- Total projects: 27
- Scanned: 27
- Issues found: 1
- Clean: 26
```

#### 3-2. Projects with Issues Detected

Prioritize display of projects with issues:

```
---

## Security Issues Detected

### project-name
- **Path**: /path/to/project
- **Branch**: main
- **Issues detected**: 6
- **Last updated**: 8 months ago
- **Recommended actions**:
  1. Check details in project directory: `cd /path/to/project`
  2. Detailed TruffleHog scan: `trufflehog git file://. --json | jq`
  3. Remove detected secrets or clean history with git-filter-repo

---
```

#### 3-3. Clean Projects (Optional)

```
## Clean Projects (26)

No issues detected:
- ProjectA
- ProjectB
- ...
```

### STEP 4: Suggest Next Actions

```
## Recommended Next Actions

### If issues detected
1. Run detailed scan in each project
2. Review detected secrets
3. Clean history or rotate secrets as needed

### Regular scanning
- Recommend running this command weekly or monthly
- Also run when adding new projects

### Individual project scan
Use `/trufflehog-scan` within each project for individual scanning
```

---

## Important Notes

### 1. Scan Time

- Scanning many projects may take time
- Maximum 30 second timeout per project

### 2. False Positives

TruffleHog performs pattern matching for secrets, which may produce false positives.
Always verify detected content.

### 3. History Scanning

TruffleHog scans entire Git history.
Even if current code has no secrets, past commits will be detected.

### 4. Privacy

Scan results include project names and paths.
Following YPM's "no external exposure of project info" policy,
DO NOT include these results in Git commits or PRs.

---

**Always display results to user after running this command.**
