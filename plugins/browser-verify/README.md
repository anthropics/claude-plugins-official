# browser-verify — Claude Code Plugin

End-to-end browser flow validator powered by Playwright. Validates any product URL or flow and returns a structured audit report with blockers, next actions, owners, deadlines, fallback plans, and an exec-ready leadership summary.

## Install

```bash
/plugin install browser-verify@claude-plugins-official
```

Or from this repo:

```bash
/plugin marketplace add <your-org>/browser-verify-plugin
/plugin install browser-verify
```

## Usage

```bash
/browser-verify <url> [--flow <name>] [--env <staging|prod>] [--mobile]
```

## What It Checks

| Check | Criteria |
|---|---|
| Page load | HTTP 200, no redirect loops |
| Core UI | Hero, CTA, nav, footer render |
| Product flow | Target action completes |
| Console errors | Zero errors / unhandled rejections |
| Network | No 4xx/5xx on critical paths |
| Mobile | Works at 390×844 viewport |
| Performance | LCP < 2.5s, CLS < 0.1 |
| Screenshot | Saved to `/tmp/verify-screenshot.png` |

## Output

Returns 6-part structured report:

1. **Top Blockers** — P0 conversion-blocking issues
2. **Required Next Actions** — Ordered fix list
3. **Owners** — Module responsible per blocker
4. **Deadlines** — P0/P1/P2 severity windows
5. **Fallback Plan** — What to serve if fix misses deadline
6. **Leadership Summary** — 3-sentence exec brief

## Requirements

- Claude Code with Playwright MCP or Playwright installed locally
- Node.js 18+
