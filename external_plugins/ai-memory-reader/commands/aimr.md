---
description: Open the project's CLAUDE.md (or a specified memory file) in AI Memory Reader — the native macOS/iOS viewer for AI agent memory files
allowed-tools: Bash, Read, Glob
---

Open a memory file in **AI Memory Reader** — the free, open-source native macOS & iOS app that renders CLAUDE.md and other AI agent memory files with GitHub-style markdown, sidebar tree, in-page find (⌘F), and edit mode (⌘E).

**Argument:** `$ARGUMENTS` — optional. Can be:
- A file path (absolute or relative)
- A heading to jump to (use after the path, separated by `#` — e.g. `CLAUDE.md#Conventions`)
- Empty — find and open the closest `CLAUDE.md` to current working directory

## Step 1: Resolve target file

If `$ARGUMENTS` was provided:
- If it looks like a path, use it directly (resolve relative to cwd)
- If it includes `#`, split into `path` and `heading`

If empty, search in this order:
1. `./CLAUDE.md` in the cwd
2. `./CLAUDE.md` in the git repo root if different
3. `~/.claude/CLAUDE.md` (global user memory)

Use `Glob` or `Bash` (e.g. `find . -maxdepth 3 -name "CLAUDE.md" 2>/dev/null | head -1`) if needed.

## Step 2: Check AI Memory Reader is installed

```bash
if [ ! -d "/Applications/AI Memory Reader.app" ] && [ ! -d "$HOME/Applications/AI Memory Reader.app" ]; then
    cat <<'EOF'
AI Memory Reader is not installed on this Mac.

Download (universal binary, free, GPL-3.0):
  https://github.com/nvwalj/ai-memory-reader/releases/latest

After downloading, drag AI Memory Reader.app into /Applications, then run:
  xattr -dr com.apple.quarantine "/Applications/AI Memory Reader.app"
to clear Gatekeeper's "unidentified developer" warning (the build is ad-hoc signed; notarization coming).

Or build from source:
  https://github.com/nvwalj/ai-memory-reader
EOF
    exit 0
fi
```

## Step 3: Open via URL scheme

Construct the URL:
- Base: `aimemoryreader://open?path=<ENCODED_ABSOLUTE_PATH>`
- If `heading` was provided: append `&heading=<ENCODED_HEADING>`

URL-encode the path/heading (`%20` for spaces, etc.). Then:

```bash
open "<URL>"
```

If the app is not running, macOS will launch it. If already running, it will switch to that file and (if heading given) scroll to the heading.

## Step 4: Confirm to user

State which file was opened and whether a heading was used. Do not summarize the file's contents — the user is going to read it in the native viewer.

## Note

Only macOS supports the `aimemoryreader://` URL scheme right now. On Linux / Windows / non-AIR Mac users, suggest viewing the file in their default markdown previewer instead.
