Create a pull request for the current branch — following the project's git conventions.

## PR title rules
Format: `[TYPE] Description` or `[TYPE][TASK-ID] Description`
- Type tag: `[FEAT]`, `[FIX]`, `[CHORE]`, `[REFACTOR]`, `[DELETE]`
- Task tag (optional): `[TASK-123]`
- Example: `[FEAT][TASK-444] Create submit button`

## Steps to follow

1. Run `git status`, `git diff`, and `git log` (commits since the main branch diverged) to understand all changes included in this PR.
   - If there are **no uncommitted changes** and **no commits made by Claude in this session**, warn the user: "No changes were made in this session. Creating a PR now may not be useful. Do you still want to proceed?" and wait for confirmation before continuing.
2. Determine the base branch:
   - Run `git branch -r` to list remote branches.
   - Filter to known "integration" branches: `main`, `master`, `dev`, `develop`, `staging`, `release`, `production` — excluding the current branch.
   - If only one candidate exists (e.g. just `main` or `master`), use it automatically.
   - If multiple candidates exist, present a numbered selection list in the terminal:
     ```
     Select base branch:
       1) master
       2) dev
       3) staging
     Enter number:
     ```
     Wait for the user to enter a number and use the selected branch as the base.
3. If there are uncommitted changes, ask the user whether to commit them first or proceed as-is. If committing:
   - If Biome is configured in the project (check for `biome.json` or `biome.jsonc`), run it to format modified files before staging.
   - Analyze all changes and determine whether they should be split into multiple logical commits. Split when changes span unrelated features, components, or concerns — keep related file changes together, separate refactoring from feature additions, and ensure each commit is independently understandable.
   - Stage and commit each logical group separately with a clear message.
4. If the branch hasn't been pushed yet, push it with `git push -u origin <branch>`.
5. Derive the PR type from the branch name prefix (`feat/` → `[FEAT]`, `fix/` → `[FIX]`, etc.) or ask the user if unclear.
6. Extract a task ID from the branch name if present (e.g. `feat/TASK-123-foo` → `[TASK-123]`).
7. Create the PR using `gh pr create` with:
   - Title following the `[TYPE][TASK-ID] Description` format
   - Body with a ## Summary section (bullet points covering all commits) and a ## Test plan section (checklist)
   - Footer: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
8. Return the PR URL.
