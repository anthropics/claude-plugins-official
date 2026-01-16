# shipit

Quick commit and push for Claude Code - analyze changes, generate commit message, commit, and push in one command.

## Installation

```bash
/plugin install github:1-Martian-Way/shipit
```

## Usage

```bash
/shipit
```

That's it! Claude will:
1. Check for changes
2. Analyze the diff
3. Generate a commit message (conventional commits format)
4. Stage, commit with co-author attribution, and push

## Example Output

```
Committed and pushed to main:

  refactor: simplify PM2 restart by delegating to pm2.sh

  - Changed build-prod.sh to call ./pm2.sh instead of inline restart
```

## Why shipit?

- **One command** - No more `git add`, `git commit -m "..."`, `git push`
- **Smart messages** - AI-generated commit messages following conventional commits
- **Attribution** - Automatic co-author credit for Claude

## License

MIT
