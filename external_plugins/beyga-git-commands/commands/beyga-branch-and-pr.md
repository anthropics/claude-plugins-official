Create a new git branch for the current changes, commit them, and open a pull request — following the project's git conventions.

## Branch naming rules
Format: `<type>/<name>` or `<type>/<TASK-ID>-<name>`
- Allowed types: `feat`, `fix`, `chore`, `refactor`, `delete`
- Task ID (if provided): uppercase, before the name — e.g. `feat/TASK-123-add-button`
- Name: lowercase, hyphen-separated — e.g. `fix/icons-not-displaying`

## PR title rules
Format: `[TYPE] Description` or `[TYPE][TASK-ID] Description`
- Type tag: `[FEAT]`, `[FIX]`, `[CHORE]`, `[REFACTOR]`, `[DELETE]`
- Task tag (optional): `[TASK-123]`
- Example: `[FEAT][TASK-444] Create submit button`

## Steps to follow

1. Run `git status` and `git diff` to understand what has changed.
2. Ask the user (if not already provided via $ARGUMENTS):
   - Branch type (`feat`, `fix`, `chore`, `refactor`, `delete`)
   - Optional task ID (e.g. `TASK-123`)
   - Short branch name (lowercase, hyphen-separated)
3. Create and switch to the new branch using the naming convention above.
4. If there are changes to commit:
   - If Biome is configured in the project (check for `biome.json` or `biome.jsonc`), run it to format modified files before staging.
   - Analyze all changes and determine whether they should be split into multiple logical commits. Split when changes span unrelated features, components, or concerns — keep related file changes together, separate refactoring from feature additions, and ensure each commit is independently understandable.
   - Stage and commit each logical group separately with a clear message. Append `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` to each commit.
   - If there are **no changes to commit**, skip this step entirely — do not create an empty commit.
5. Push the branch with `-u origin`.
6. If there are **no commits ahead of the base branch** (nothing was committed in step 4 and no prior commits exist on this branch), skip PR creation — there is nothing to open a PR for. Inform the user the branch was created and pushed, but no PR was opened.
7. Determine the base branch for the PR:
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
8. Create the PR using `gh pr create` with:
   - Title following the `[TYPE][TASK-ID] Description` format
   - Body with a ## Summary section (bullet points) and a ## Test plan section (checklist)
   - Footer: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
9. Return the PR URL.
