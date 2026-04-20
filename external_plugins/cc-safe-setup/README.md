One command to make Claude Code safe for autonomous operation.
```bash
npx cc-safe-setup
```
Installs 8 essential safety hooks in under 30 seconds. No config needed.
- **Blocks `rm -rf`** — prevents recursive deletion of files and directories
- **Blocks `git push --force`** — prevents force pushes that destroy history
- **Blocks credential leaks** — prevents writing secrets to tracked files
- **Blocks `git reset --hard`** — prevents loss of uncommitted changes
- **Warns on large file reads** — catches accidental binary/log reads that waste tokens
- **Warns on broad file changes** — detects when Claude rewrites instead of editing
- **Token budget tracking** — monitors session cost with `/cost` integration
- **Syntax validation** — checks edited files for syntax errors before committing
- 703 example hooks covering every major risk pattern
- 9,200+ tests
- 30,000+ total installs
- 58-section Opus 4.7 Survival Guide tracking 73+ GitHub Issues and CVEs
- [Token Checkup](https://yurukusa.github.io/cc-safe-setup/token-checkup.html) — 5-question token waste diagnostic
- [Hook Selector](https://yurukusa.github.io/cc-safe-setup/hook-selector.html) — find the right hooks for your workflow
- [Safety Audit](https://yurukusa.github.io/cc-safe-setup/safety-audit.html) — score your setup out of 100
- [GitHub](https://github.com/yurukusa/cc-safe-setup)
- [Landing Page](https://yurukusa.github.io/cc-safe-setup/)
- [Opus 4.7 Survival Guide](https://yurukusa.github.io/cc-safe-setup/opus-47-survival-guide.html)
