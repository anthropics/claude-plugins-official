---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(python -m py_compile:*), Bash(python3 -m py_compile:*), Bash(bash -n:*), Bash(node --check:*)
description: Code review a pull request
disable-model-invocation: false
---

Provide a code review for the given pull request.

To do this, follow these steps precisely:

1. Use a Haiku agent to check if the pull request (a) is closed, (b) is a draft, (c) does not need a code review (eg. because it is an automated pull request, or is very simple and obviously ok), or (d) already has a code review from you from earlier. If so, do not proceed.
2. Use another Haiku agent to give you a list of file paths to (but not the contents of) any relevant guideline files from the codebase. Look for, in order: (a) the root CLAUDE.md, (b) CLAUDE.md files in the directories whose files the pull request modified, (c) any SOUL.md, AGENTS.md, or similar persona/identity files that encode behavioral rules (these often live separately from coding rules and are still normative for review), (d) SKILL.md or agent-definition files for any skill/subagent the PR modifies. Treat all of these as normative when reviewing — many projects split rules across several markdown files
3. Use a Haiku agent to view the pull request, and ask the agent to return a summary of the change
4. Then, launch 8 parallel reviewer agents (Sonnet for #1–6 — semantic review; Haiku for #7–8 — mechanical / pattern-based). The agents should do the following, then return a list of issues and the reason each issue was flagged (eg. CLAUDE.md adherence, bug, historical git context, diff coherence, cross-device, smoke, etc.):
   a. Agent #1: Audit the changes to make sure they compily with the CLAUDE.md and any related guideline files (SOUL.md, AGENTS.md, SKILL.md) found in step 2. Note that these files are guidance for Claude as it writes code, so not all instructions will be applicable during code review.
   b. Agent #2: Read the file changes in the pull request, then do a shallow scan for obvious bugs. Avoid reading extra context beyond the changes, focusing just on the changes themselves. Focus on large bugs, and avoid small issues and nitpicks. Ignore likely false positives.
   c. Agent #3: Read the git blame and history of the code modified, to identify any bugs in light of that historical context
   d. Agent #4: Read previous pull requests that touched these files, and check for any comments on those pull requests that may also apply to the current pull request.
   e. Agent #5: Read code comments in the modified files, and make sure the changes in the pull request comply with any guidance in the comments.
   f. Agent #6 (diff-coherence): Read the PR title, body, and commit messages (`gh pr view <n> --json title,body,commits`). Extract every concrete claim about what changed — files added/modified/deleted, behaviors implemented, tests added, configs touched. Then run `gh pr diff` and verify each claim against the actual diff. Flag two mismatch classes: (1) **claimed-missing** — the PR or commit asserts a change was made but the diff shows no corresponding edit (a common subagent-fabrication signature, where the agent reports completion but the work didn't land); (2) **silent-scope-creep** — substantive edits in the diff that aren't acknowledged anywhere in the PR/commit narrative. Do NOT flag normal restatements, files renamed mid-cycle (claim points to old path, diff to new path), or claims about outcomes ("CI passes") that are not file-level. Cite both the claim source (PR body line / commit SHA) and the diff evidence.
   g. Agent #7 (cross-device integrity, Haiku): Read the diff via `gh pr diff` and scan ONLY the added or modified lines for portability hazards that will break on a teammate's machine: (a) **hardcoded absolute paths** that include a specific user or device — `/home/<name>/`, `/Users/<name>/`, `C:\Users\<name>\`, `/mnt/c/Users/<name>/`, `/opt/<custom>/`; (b) **hardcoded usernames** appearing as bare identifiers in code or config (e.g., a literal `petrk`, `ubuntu`, `azureuser` outside of an example/comment); (c) **OS-specific assumptions** that aren't guarded — bare `\r\n` literals, `os.path.join` mixed with literal `\\`, calls to `cmd.exe` / `powershell` / `/bin/bash` without a platform check, hardcoded drive letters; (d) **ports / hostnames / network paths** like `localhost:5432` or `\\server\share` that look like the author's local setup. Skip example files, fixtures, docs, and clearly-labeled test data. Cite line + the suspect substring.
   h. Agent #8 (smoke / static-check, Haiku): For every script-like file changed in the PR (`.py`, `.sh`, `.bash`, `.js`, `.mjs`, `.cjs`, `.ts` ONLY when standalone — skip lib/source modules of large apps), run a syntax-only static check via the appropriate Bash command and report failures: Python — `python -m py_compile <file>` (or `python3` fallback); shell — `bash -n <file>`; JavaScript — `node --check <file>`. Do NOT execute scripts. Do NOT install dependencies. Do NOT run TypeScript compilation (compile passes elsewhere in CI). For Python files, also flag obvious import errors visible from the diff alone (e.g., `from foo import bar` where `bar` was simultaneously deleted from `foo` in the same PR). Skip generated files, vendored code, and minified bundles. Cite the failing file + parser/compiler error message.
5. For each issue found in #4, launch a parallel Haiku agent that takes the PR, issue description, and list of CLAUDE.md files (from step 2), and returns a score to indicate the agent's level of confidence for whether the issue is real or false positive. To do that, the agent should score each issue on a scale from 0-100, indicating its level of confidence. For issues that were flagged due to CLAUDE.md instructions, the agent should double check that the CLAUDE.md actually calls out that issue specifically. The scale is (give this rubric to the agent verbatim):
   a. 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
   b. 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
   c. 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the PR, it's not very important.
   d. 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the PR is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
   e. 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.
6. Filter out any issues with a score less than 80. If there are no issues that meet this criteria, do not proceed.
7. Use a Haiku agent to repeat the eligibility check from #1, to make sure that the pull request is still eligible for code review.
8. Finally, use the gh bash command to comment back on the pull request with the result. When writing your comment, keep in mind to:
   a. Keep your output brief
   b. Avoid emojis
   c. Link and cite relevant code, files, and URLs

Examples of false positives, for steps 4 and 5:

- Pre-existing issues
- Something that looks like a bug but is not actually a bug
- Pedantic nitpicks that a senior engineer wouldn't call out
- Issues that a linter, typechecker, or compiler would catch (eg. missing or incorrect imports, type errors, broken tests, formatting issues, pedantic style issues like newlines). No need to run these build steps yourself -- it is safe to assume that they will be run separately as part of CI.
- General code quality issues (eg. lack of test coverage, general security issues, poor documentation), unless explicitly required in CLAUDE.md
- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)
- Changes in functionality that are likely intentional or are directly related to the broader change
- Real issues, but on lines that the user did not modify in their pull request
- Diff-coherence false positives: a file renamed during the change (claim names old path, diff shows new path is the same edit), refactor-induced relocations of the same logic, or PR-body wording that is descriptive ("cleanup", "small fixes") rather than a concrete change-list — these are not fabrication. Only flag claimed-missing when a *specific* file/behavior/test is asserted and absent.
- Cross-device false positives: example values inside docs / fixtures / tests / `.example` files / commented-out illustration code, paths inside `if platform == "..."` branches that DO have a sibling fallback, deliberately-platform-specific scripts under a clearly-named directory (`scripts/windows/`, `tools/macos/`), and CI-runner-default usernames in workflow files (`runner`, `ubuntu` are GitHub-hosted defaults, not personal-machine leaks).
- Smoke / static-check false positives: parser errors caused by the file genuinely being a different language than its extension suggests (jinja2 with `.py` extension, ERB templates), files explicitly listed in lint-ignore configs, intentional partial scripts meant to be sourced (not run standalone). Only flag when the parser/compiler error message is concrete and specific to the diff.

Notes:

- Do not check build signal or attempt to build or typecheck the app. These will run separately, and are not relevant to your code review.
- Use `gh` to interact with Github (eg. to fetch a pull request, or to create inline comments), rather than web fetch
- Make a todo list first
- You must cite and link each bug (eg. if referring to a CLAUDE.md, you must link it)
- For your final comment, follow the following format precisely (assuming for this example that you found 3 issues):

---

### Code review

Found 3 issues:

1. <brief description of bug> (CLAUDE.md says "<...>")

<link to file and line with full sha1 + line range for context, note that you MUST provide the full sha and not use bash here, eg. https://github.com/anthropics/claude-code/blob/1d54823877c4de72b2316a64032a54afc404e619/README.md#L13-L17>

2. <brief description of bug> (some/other/CLAUDE.md says "<...>")

<link to file and line with full sha1 + line range for context>

3. <brief description of bug> (bug due to <file and code snippet>)

<link to file and line with full sha1 + line range for context>

🤖 Generated with [Claude Code](https://claude.ai/code)

<sub>- If this code review was useful, please react with 👍. Otherwise, react with 👎.</sub>

---

- Or, if you found no issues:

---

### Code review

No issues found. Checked for bugs and CLAUDE.md compliance.

🤖 Generated with [Claude Code](https://claude.ai/code)

- When linking to code, follow the following format precisely, otherwise the Markdown preview won't render correctly: https://github.com/anthropics/claude-cli-internal/blob/c21d3c10bc8e898b7ac1a2d745bdc9bc4e423afe/package.json#L10-L15
  - Requires full git sha
  - You must provide the full sha. Commands like `https://github.com/owner/repo/blob/$(git rev-parse HEAD)/foo/bar` will not work, since your comment will be directly rendered in Markdown.
  - Repo name must match the repo you're code reviewing
  - # sign after the file name
  - Line range format is L[start]-L[end]
  - Provide at least 1 line of context before and after, centered on the line you are commenting about (eg. if you are commenting about lines 5-6, you should link to `L4-7`)
