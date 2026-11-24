# Run a scan in a full-screen view

`claude-security --tui` starts a scan of your repository with the Claude Security plugin, and shows its progress full screen. When the scan ends, you read the findings in the same view.

## What you need

- The `claude-security` command, on Linux or Windows, as [README.md](README.md#scan-from-your-shell) describes. It does not run on macOS, and WSL 2 is not supported.
- Node.js 18 or newer on your `PATH`. Use version 22.13 or newer if you can: its permission model is more complete.
- A window of at least 30 columns and 8 rows. At 94 columns or more, the map and the panels show side by side.

## Start

**Warning:** On Windows, the scan has no sandbox. Its agents run commands with your access. Read the [trust model](SECURITY.md#trust-model) first.

1. Open a terminal in the repository.
2. Run `claude-security --tui`. On Ubuntu 24.04 and newer, add `--sudo`. On Windows, add `--no-sandbox`.
3. Type `y` to accept the time and the token cost. Type `n` to cancel.

To scan only this branch's changes, add `--changes`.

## What you see

A possible flaw moves through three steps:

1. **Lead:** a researcher agent reports a place in the code.
2. **Candidate:** two or three verifier agents vote on it in the Panel stage.
3. **Finding:** the verifiers confirm it, and the report lists it. Findings show when the scan ends.

| Part | What it shows |
| --- | --- |
| Top | The repository, the branch, the sandbox state and the time since the start |
| Stages | Setup, Inventory, Sweep, Research, Panel and Report. The view highlights the stage that runs. |
| Map | Your code as dots. Each file is a tile, and a longer file has a larger tile. In a very large repository, a tile is a folder. |
| Panels | Agents, components, verifier votes, the scan target and the narration. At the end, the findings show first. |
| Counts | Files and lines read, agents, tokens, leads and candidates, as many as fit |
| Bottom | The status, the last line of the narration and the keys that work now |

| Mark on the map | Meaning |
| --- | --- |
| Faint dots | Code that no agent has read |
| Orange dots | Lines that an agent reads now |
| Strong dots | Lines that an agent has read |
| Blue dots | Files that an agent searches now |
| `✻` | An agent |
| `◆` | A lead |
| A ring or a label with an ID | A candidate |
| A colored label | With a `C` number, orange is a confirmed candidate. With an `F` number, it is a finding: red is critical, orange is high, yellow is medium, blue is low. |

## Keys

| Key | Action |
| --- | --- |
| `↑` `↓` or `k` `j` | Choose a finding, or scroll |
| `Page Up`, `Page Down` | Move up or down one page. `Space` moves down. |
| `Home`, `End` | Go to the first or the last row |
| `Enter` | Read the chosen finding, after the scan ends |
| `Tab`, `Shift+Tab` | Show the next or the previous panel (`Shift+Tab`: Linux only) |
| `l` | Show the narration: a log of what the scan does |
| `m` | Show only the map |
| `?` | Show the keys and the map legend |
| `Esc` | Close the finding, the log, the map or the help. Press it again to see the first panel. |
| `Ctrl+L` | Draw the screen again |
| `Ctrl+Z` | Go to the shell (Linux only). The scan can pause until you type `fg`. |
| `q`, `Ctrl+C` | Quit |

## Quit

**Warning:** You cannot continue a stopped scan, and it usually has no report. If you press `Ctrl+C` two times, the scan stops.

- **While the scan runs:** press `q`. The view asks you to confirm. Press `y` to stop the scan, or `n` to continue.
- **After the scan ends:** press `q` to close the view.

The command then prints a summary and the paths of the report files.

- **Exit code 0:** the scan is complete, or it had nothing to scan. Findings do not change this code.
- **Exit code 1:** the scan is not complete.
- **Exit code 2:** no scan started.

## Options

The view uses dark colors. If your terminal has a light background, add `--light`.

| Option or variable | Effect |
| --- | --- |
| `--light`, `--dark` | Uses light or dark colors. With neither, the view is light only if `COLORFGBG` names a light background. |
| `--nerd-fonts` | Shows icons. Your terminal must use a Nerd Font. |
| `CLAUDE_SECURITY_REDUCED_MOTION=1` | Shows less motion |
| `NO_COLOR=1` | Shows no color |
| `FORCE_COLOR=1`, `2` or `3` | Uses 16 colors, 256 colors or full color |
| `LC_ALL=C` | Uses only ASCII characters |

With 16 colors or no color, the view uses the colors of your terminal, and `--light` and `--dark` do nothing.

## If something looks wrong

| Sign | Cause | What to do |
| --- | --- | --- |
| "The full-screen view is off", then lines of text | Node.js is missing or too old, the plugin's path has a `*`, or the view stopped on an error | The scan continues, and one `Ctrl+C` now stops it. Before the next scan, check `node --version` and the plugin's path. |
| Lines of text, with no message | Output is a pipe or a file, input is one (with `--yes`), or `TERM` is `dumb` or, on Linux, not set | Use no pipe and no redirect. On Linux, run `export TERM=xterm-256color`. |
| A dark view in a light terminal | Dark is the default | Add `--light`. |
| No map | The window is small, or the link is slow ("slow link: less motion") | Press `m`. |
| Boxes or question marks in place of icons | The font has no such icons | Remove `--nerd-fonts`, or set `LC_ALL=C`. |
| A finding's title is "Not shown: the report can still hold credential values" | The step that removes credentials did not complete | Do not share the report files. Remove each password, key and token first. |
| Other text shows on top of the view | Another program wrote to the terminal | Press `Ctrl+L`. |
