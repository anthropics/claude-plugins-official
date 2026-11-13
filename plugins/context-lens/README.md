# context-lens

A Claude Code mod that shows exactly what is in the context window, request by request.

Every time Claude Code is about to send a model request, context-lens snapshots what that request carries: the system prompt sections, the tools offered, and every message block (your prompts, the reminders Claude Code injects, replies, thinking, tool calls and tool results). You can browse it, search it, and step back through earlier requests.

## Use

- **Band above the prompt.** After each request it shows the window's fill and what the request added, for example `context 44.7k/200k · request 3 added 2 items (≈162 tok), last: result Grep parseDuration → 11 lines`. Focus the band with ctrl+x tab, then press `o` to open the lens or `h` to hide the band.
- **`/context-lens`** opens the lens pane. `/context-lens <text>` opens it with a search already typed. `/context-lens export` writes the request on screen to `context-lens-request-<n>.md` in the project. `/context-lens band` brings a hidden band back.
- **In the pane** (click, or focus it and use the keys):
  - `p` / `n` / `l`: previous request, next request, latest. The pane follows the newest request until you step back.
  - `1`–`7`: filter to All, System, Tools, Reminders, Chat, Tool I/O, or New (only what this request added compared with the one before).
  - Search: Tab to the field and type. Matches are counted per item and highlighted.
  - Click a row to open the reader. `b` back, `j` / `k` next or previous item, `u` / `d` page, `m` next match, `y` copy the text.

## Install

It needs Claude Code 2.1.287 or newer, the first release with mods (function hooks).

```
/plugin install context-lens@claude-plugins-official
```

In the terminal the pane docks beside the transcript in the fullscreen layout. It also works in the desktop app's Code tab.

## Privacy

context-lens only reads. It doesn't change the prompt, the tools or any tool call, and it sends nothing over the network.
Snapshots live in the session's mod state on your machine.
The one write is `/context-lens export`, which saves the request on screen as a Markdown file in the project, so check that file before you share it: it holds your conversation as sent to the model.

## What the numbers mean

- The bar and its categories are Claude Code's own estimate, the same one `/context` shows.
- Item sizes are about four characters per token. They are for comparing items, not billing.
- Tools show their descriptions. Input schemas are sent too, but mods can't read them, so `/context`'s System tools row is the full count.

## Limits

- It captures the main conversation. Subagents' requests are not shown.
- Snapshots start when the mod loads. A resumed session's history shows up in the first new request.
- It keeps the last 60 requests, and up to 400k characters of any one block.
- Some sessions don't report their system prompt sections to mods (the desktop app's Code tab, in testing). The lens then shows one System prompt row with its size and says the text wasn't reported.

## Develop

Load a local copy with `claude --plugin-dir /path/to/context-lens`, or in the desktop app set `CLAUDE_CODE_PLUGIN_DIRS=/path/to/context-lens` in the environment it starts Claude Code with.
Check it with `claude plugin validate .` and `claude plugin test .` (tests in `tests/`).
