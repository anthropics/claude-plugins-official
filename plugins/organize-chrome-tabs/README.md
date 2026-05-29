# organize-chrome-tabs

Tame Chrome tab chaos from the command line.

- **Closes duplicates** — exact title matching across all windows
- **Sorts into themed windows** — pattern-matched by title + URL
- **Clusters by domain** — within each window, same-domain tabs group together
- **Native tab groups** — generates a one-shot Chrome extension for colored tab labels
- **Claude Code skill** — `/organize-tabs` slash command built in

macOS only (AppleScript + chrome-cli).

---

## Quick start

```bash
brew install chrome-cli
mkdir -p ~/scripts
curl -fsSL https://raw.githubusercontent.com/th0mps0nty/organize-chrome-tabs/main/organize-chrome-tabs.py \
  -o ~/scripts/organize-chrome-tabs.py
chmod +x ~/scripts/organize-chrome-tabs.py

# Preview what would change
python3 ~/scripts/organize-chrome-tabs.py --dry-run

# Run it
python3 ~/scripts/organize-chrome-tabs.py
```

---

## Usage

```
python3 organize-chrome-tabs.py [options]

  --single-window     Merge everything into one window, cluster by domain
  --combine           Merge first, then redistribute into themed windows
  --cluster-only      Cluster by domain within current windows (no redistribution)
  --no-close-dupes    Skip duplicate removal
  --build-extension   Write a Chrome extension for native tab group labels
  --init              Create a personal themes config interactively
  --config PATH       Load themes from a JSON file
  --dry-run           Preview all changes without applying them
```

### Common workflows

**Everything into one tidy window:**
```bash
python3 organize-chrome-tabs.py --single-window
```

**Sort into project windows, then add colored tab groups:**
```bash
python3 organize-chrome-tabs.py
python3 organize-chrome-tabs.py --build-extension
# chrome://extensions → Developer mode → Load unpacked → tab-groups-ext/
```

**First time setup — define your own themes:**
```bash
python3 organize-chrome-tabs.py --init
python3 organize-chrome-tabs.py --config ~/scripts/chrome-themes.json
```

---

## Themes

Built-in themes match tabs by title/URL substring:

| Window | Patterns |
|--------|----------|
| Dev & Cloud | github, netlify, vercel, render, cloudflare, supabase, localhost … |
| Productivity | notion, linear, jira, figma, slack, discord … |
| AI & Research | chatgpt, claude, openai, youtube, medium, reddit … |
| Email & Comms | gmail, calendar, linkedin, twitter … |

Override with `--init` (interactive) or `--config path/to/themes.json`:

```json
[
  { "name": "Work",     "patterns": ["github", "jira", "notion"] },
  { "name": "AI",       "patterns": ["chatgpt", "claude", "openai"] },
  { "name": "Personal", "patterns": ["gmail", "linkedin", "youtube"] }
]
```

---

## Claude Code skill

Install as a Claude Code plugin to get the `/organize-tabs` slash command:

```bash
# Add this repo as a marketplace in ~/.claude/settings.json:
# "extraKnownMarketplaces": {
#   "th0mps0nty": {
#     "source": { "source": "github", "repo": "th0mps0nty/organize-chrome-tabs" }
#   }
# }

claude plugin add organize-chrome-tabs@th0mps0nty
```

Then in any Claude Code session:
```
/organize-tabs
/organize-tabs --single-window
```

---

## Native tab groups

Tab group labels require Chrome extension APIs, which aren't available from the command line. The `--build-extension` flag writes a minimal one-shot Manifest V3 extension:

```bash
python3 organize-chrome-tabs.py --build-extension
```

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select `tab-groups-ext/`
4. Groups appear immediately
5. Remove the extension — groups persist

---

## Requirements

- macOS
- Google Chrome
- `brew install chrome-cli`

---

## License

MIT
