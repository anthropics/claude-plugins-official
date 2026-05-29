---
name: organize-tabs
description: This skill should be used when the user says "organize my tabs", "clean up chrome", "sort my tabs", "single window", "one window", or "tab cleanup". Organizes Chrome tabs by closing duplicates, sorting into themed windows, clustering by domain, and creating native tab group labels.
version: 1.0.0
---

# Organize Chrome Tabs

Tame Chrome tab chaos using `organize-chrome-tabs.py`.

## Installation (first run on a new machine)

Before using this skill, ensure the script is installed:

```bash
# Install dependency
brew install chrome-cli

# Install script
mkdir -p ~/scripts
curl -fsSL https://raw.githubusercontent.com/th0mps0nty/organize-chrome-tabs/main/organize-chrome-tabs.py \
  -o ~/scripts/organize-chrome-tabs.py
chmod +x ~/scripts/organize-chrome-tabs.py
```

## Modes — pick based on what the user wants

| User says | Command |
|-----------|---------|
| "organize my tabs" | `python3 ~/scripts/organize-chrome-tabs.py` |
| "single window" / "one window" | `python3 ~/scripts/organize-chrome-tabs.py --single-window` |
| "combine then organize" | `python3 ~/scripts/organize-chrome-tabs.py --combine` |
| "just cluster domains" | `python3 ~/scripts/organize-chrome-tabs.py --cluster-only` |
| "create tab groups" | `python3 ~/scripts/organize-chrome-tabs.py --build-extension` |
| "set up my themes" | `python3 ~/scripts/organize-chrome-tabs.py --init` |

## Steps

1. Dry-run first to preview:
```bash
python3 ~/scripts/organize-chrome-tabs.py --dry-run [mode-flag]
```

2. Show the user the summary and confirm.

3. Run for real:
```bash
python3 ~/scripts/organize-chrome-tabs.py [mode-flag]
```

4. For native Chrome tab groups (colored labels in the tab bar):
```bash
python3 ~/scripts/organize-chrome-tabs.py --build-extension
```
Then tell the user: **chrome://extensions → Developer mode → Load unpacked → select `tab-groups-ext/`**

## All flags

```
--single-window     Merge all windows into one, cluster by domain
--combine           Merge first, then redistribute into themed windows
--cluster-only      Cluster by domain only, no window redistribution
--no-close-dupes    Skip duplicate removal
--build-extension   Write a native tab-groups Chrome extension to tab-groups-ext/
--init              Interactively create ~/scripts/chrome-themes.json
--config PATH       Load themes from a custom JSON file
--dry-run           Preview without changing anything
```

## Custom themes config format

```json
[
  { "name": "Work",     "patterns": ["github", "jira", "notion", "linear"] },
  { "name": "AI",       "patterns": ["chatgpt", "claude", "openai"] },
  { "name": "Personal", "patterns": ["gmail", "linkedin", "youtube"] }
]
```

Generate one interactively with `--init`, or pass any JSON file with `--config`.

## Requirements

- macOS (uses AppleScript + chrome-cli)
- `brew install chrome-cli`
- Google Chrome
