---
description: Where am I? Progress, what is stale, and the exact next command to run — start here when unsure
argument-hint: <system>
arguments: system
---

Report where the modernization of `$system` stands, in one screen. This command inspects and never modifies,
except that it refreshes `analysis/$system/REPORT.html` (`python3
"${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py" $system`, a convenience: if it fails or `python3` is missing, say so in one line and carry on). If nothing
exists yet, the answer is `/code-modernization:modernize $system --source <path to the code>`, which asks what the person wants and starts preflight.

## 1 — Inventory

Check `analysis/$system/` and `modernized/$system*/` and build a table, one row per stage, with each artifact's
presence and modification time:

| Stage | Artifacts |
|---|---|
| intent | `INTENT.md` (what the person wants; written by `/code-modernization:modernize`) |
| preflight | `PREFLIGHT.md` (are the Check 0 human answers and the Check 6 scope-boundary finding there?), where `legacy/$system` points (does that directory exist?) |
| assess | `ASSESSMENT.md`, `ARCHITECTURE.mmd` |
| map | `topology.json`, `TOPOLOGY.html`, `*.mmd`, `extract_topology.*` |
| extract-rules | `BUSINESS_RULES.md`, `DATA_OBJECTS.md` |
| review | `RULE_REVIEWS.json`: how many flagged rules a person has decided (confirmed, wrong, needs discussion), and how many are still open |
| brief | `MODERNIZATION_BRIEF.md` (is the approval block signed?) |
| harden | `SECURITY_FINDINGS.md`, `security_remediation.patch` |
| uplift | `DELTA_CATALOG.md`, `BASELINE.md`, `PLAYBOOK.md` (no playbook means the pilot has not happened, so the fan-out must not), `modernized/$system-uplifted/UPLIFT_NOTES.md` (per unit: builds on target? baseline reproduced?) |
| transform | each `modernized/$system/<module>/`: tests present? `TRANSFORMATION_NOTES.md` present (its completion marker)? |
| reimagine | `modernized/$system-reimagined/`: per-service acceptance tests, and the `CLAUDE.md` handoff (its completion marker; it does not write `TRANSFORMATION_NOTES.md`) |
| equivalence | `EQUIVALENCE.json`: cases executed, same, differs (any differing or missing case, or zero executed, is a failure) |
| verify | `VERIFICATION.md` (written by `/code-modernization:modernize-verify`): the verdict per built module (PROVEN, PARTLY PROVEN or NOT PROVEN) and whether a person has signed it. A built module with no `VERIFICATION.md`, or one older than the module's code or tests, is **not proven yet** |

## 2 — Stale

Flag any artifact older than one it derives from: the brief older than `ASSESSMENT.md`, `topology.json` or
`BUSINESS_RULES.md` (no longer reflects discovery: rerun `brief`); an uplift's brief older than
`DELTA_CATALOG.md`, or with no catalog (phase order was decided without the version deltas: rerun `brief`);
`TOPOLOGY.html` older than `topology.json` (rerun the render step of `map`); a `TRANSFORMATION_NOTES.md` older
than `BUSINESS_RULES.md` (the module may not implement the latest rules: list which).

## 3 — Secrets hygiene

Does `analysis/.gitignore` exist and cover `SECRETS.local.md` and `*.local.patch` (`git check-ignore` in a git
repo)? If `SECRETS.local.md` exists, confirm it is NOT tracked (`git ls-files --error-unmatch` should fail) and
never committed (`git log --all --oneline -- <path>` should be empty). If either fails, say so prominently and
recommend rotation and history scrubbing.

## 4 — Verdict

End with three lines:

- **Where you are:** the furthest completed stage and how much it covers ("mapped 100%, 2 of 14 modules transformed, 1 proven").
- **What is stale:** or "nothing".
- **Next command:** the single most useful next step as the exact command line to paste, with a one-line reason.
  The order is preflight, assess, map, extract-rules, review (when rules are flagged for a person), brief (needs approval), then the brief's Phase 1 command
  (`transform`, `uplift` or `reimagine`), then `verify` for what was built, then `harden`. Never call a
  built module done until `verify` says PROVEN and a person has signed it: put `verify` ahead of building the next module.
