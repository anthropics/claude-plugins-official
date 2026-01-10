---
description: Perform end-of-session cleanup and documentation synchronization
---
# PACT Wrap-Up Protocol

You are now entering the **Wrap-Up Phase**. Your goal is to ensure the workspace is clean and documentation is synchronized before the session ends or code is committed.

> **Reference Skill**: For structured session summarization techniques, invoke `context-compression` skill.
> Key pattern: Use "Anchored Iterative Summarization" with explicit sections for files modified, decisions made, and next steps.

## 1. Documentation Synchronization
- **Scan** the workspace for recent code changes.
- **Update** `docs/CHANGELOG.md` with a new entry for this session:
    - **Date/Time**: Current timestamp.
    - **Focus**: The main task or feature worked on.
    - **Changes**: List modified files and brief descriptions.
    - **Result**: The outcome (e.g., "Completed auth flow", "Fixed login bug").
- **Verify** that `CLAUDE.md` reflects the current system state (architecture, patterns, components).
- **Verify** that `docs/<feature>/preparation/` and `docs/<feature>/architecture/` are up-to-date with the implementation.
- **Update** any outdated documentation.
- **Archive** any obsolete documentation to `docs/archive/`.

## 2. Workspace Cleanup
- **Identify** any temporary files created during the session (e.g., `temp_test.py`, `debug.log`, `foo.txt`, `test_output.json`).
- **Delete** these files to leave the workspace clean.

## 3. Final Status Report
- **Report** a summary of actions taken:
    - Docs updated: [List files]
    - Files archived: [List files]
    - Temp files deleted: [List files]
    - Status: READY FOR COMMIT / REVIEW

If no actions were needed, state "Workspace is clean and docs are in sync."
