---
description: Security vulnerability scan with a reviewable remediation patch — OWASP, CWE, CVE, secrets, injection
argument-hint: <system-dir>
---

Run a **security hardening pass** on `legacy/$1`: find vulnerabilities, rank
them, and produce a reviewable patch for the critical ones.

This command never edits `legacy/` — it writes findings and a proposed patch
to `analysis/$1/`. The user reviews and applies (or not).

## Scan

Spawn the **security-auditor** subagent:

"Adversarially audit legacy/$1 for security vulnerabilities. Cover what's
relevant to the stack: injection (SQL/NoSQL/OS command/template), broken
auth, sensitive data exposure, access control gaps, insecure deserialization,
hardcoded secrets, vulnerable dependency versions, missing input validation,
path traversal. For each finding return: CWE ID, severity
(Critical/High/Med/Low), file:line, one-sentence exploit scenario, and
recommended fix. Run any available SAST tooling (npm audit, pip-audit,
OWASP dependency-check) and include its raw output."

## Triage

Write `analysis/$1/SECURITY_FINDINGS.md`:
- Summary scorecard (count by severity, top CWE categories)
- Findings table sorted by severity
- Dependency CVE table (package, installed version, CVE, fixed version)

## Remediate

For each **Critical** and **High** finding, draft a minimal, targeted fix.
Do **not** edit `legacy/` — write all fixes as a single unified diff to
`analysis/$1/security_remediation.patch`, with a comment line above each
hunk citing the finding ID it addresses (`# SEC-001: parameterize the query`).

Add a **Remediation Log** section to SECURITY_FINDINGS.md mapping each
finding ID → one-line summary of the proposed fix and the patch hunk that
implements it.

## Verify

Spawn the **security-auditor** again to **review the patch** against the
original code:

"Review analysis/$1/security_remediation.patch against legacy/$1. For each
hunk: does it fully remediate the cited finding? Does it introduce new
vulnerabilities or change behavior beyond the fix? Return one verdict per
hunk: RESOLVES / PARTIAL / INTRODUCES-RISK, with a one-line reason."

Add a **Patch Review** section to SECURITY_FINDINGS.md with the verdicts.
If any hunk is PARTIAL or INTRODUCES-RISK, revise the patch and re-review.

## Present

Tell the user the artifacts are ready:
- `analysis/$1/SECURITY_FINDINGS.md` — findings, remediation log, patch review
- `analysis/$1/security_remediation.patch` — review, then apply if appropriate
  with `git -C legacy/$1 apply ../../analysis/$1/security_remediation.patch`
- Re-run `/modernize-harden $1` after applying to confirm resolution

Suggest: `glow -p analysis/$1/SECURITY_FINDINGS.md`
