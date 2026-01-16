---
name: shipit
description: Commit all changes with an AI-generated message and push to remote
---

# Shipit: Quick Commit and Push

Analyze the current changes, generate a relevant commit message, commit, and push.

## Steps

1. **Check for changes** - Run `git status` to see what's changed. If nothing to commit, inform the user and stop.

2. **Analyze the diff** - Run `git diff` (for unstaged) and `git diff --cached` (for staged) to understand what changed.

3. **Generate commit message** - Based on the changes, write a concise commit message:
   - Use conventional commit format: `type: description`
   - Types: feat, fix, refactor, docs, style, test, chore
   - Keep the first line under 72 characters
   - Focus on WHAT changed and WHY, not HOW

4. **Stage all changes** - Run `git add -A` to stage everything.

5. **Commit** - Run `git commit -m "message"` with the generated message. Include co-author:
   ```bash
   git commit -m "$(cat <<'EOF'
   type: description

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

6. **Push** - Run `git push`. If upstream isn't set, use `git push -u origin <current-branch>`.

7. **Confirm** - Show the user what was committed and pushed.

## Commit Message Guidelines

- `feat:` new feature or functionality
- `fix:` bug fix
- `refactor:` code restructuring without behavior change
- `docs:` documentation changes
- `style:` formatting, whitespace (no code change)
- `test:` adding or updating tests
- `chore:` maintenance, dependencies, build scripts

## Example Output

```
Committed and pushed to main:

  refactor: simplify PM2 restart by delegating to pm2.sh

  - Changed build-prod.sh to call ./pm2.sh instead of inline restart
  - Removes code duplication between deployment scripts
```
