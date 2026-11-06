# Champion Kit plugin for Claude Code

Commands and routines for Claude Code champions. Claude does the prep on your real repo, and you stay in charge of what gets used.

It builds on the public [Claude Code champion kit](https://code.claude.com/docs/en/champion-kit) and adds this kit's own steps of AI adoption and plays, which aren't part of the Claude Code docs. Run any command below, or ask in your own words and Claude picks the right one.

## Install

This plugin is listed in the `claude-plugins-official` marketplace.

### Claude desktop app

1. In the desktop app, open the **Code** tab and start a local session.
2. Click **+** next to the prompt box and select **Add plugins**. If the menu shows **Plugins**, select it, then **Browse plugins**.
3. Find `champion-kit`, select it, and choose a scope. Your user account is the usual choice.
4. Type `/champion-kit:` in the prompt box to see the commands.

### Terminal

```bash
claude plugin install champion-kit@claude-plugins-official
```

Or run `/plugin install champion-kit@claude-plugins-official` in a session, or browse for it in `/plugin > Discover`. Start a new session, then type `/champion-kit:`. To try a local copy without installing, run `claude --plugin-dir ./champion-kit`.

## Commands

Type a command with nothing after it, such as `/champion-kit:hackathon`. It says in one line what it will make, looks at your repo for sensible defaults, and then asks a few questions one at a time. Where there are a few clear choices, you pick from a short list. Say "go" to take the defaults. Reading your git history, issues, chat, or session transcripts, creating a calendar event, and writing any file still wait for your own yes. If you already know some answers, you can add them after the command, and it asks only for what's missing.

### Run a play

| Command | What it does |
| - | - |
| `/champion-kit:hackathon` | Plans a hack day from your real backlog, or as open-ended creative play with starter ideas |
| `/champion-kit:office-hours` | Sets up office hours, puts them on your calendar if your connector allows and you approve, builds the agenda, and writes up the answers |
| `/champion-kit:patterns` | Finds repeats worth turning into rules or skills, and good practices worth spreading |

### Bring people along

| Command | What it does |
| - | - |
| `/champion-kit:climb` | Works out which step a teammate, you, or your team is on, and what to try next |
| `/champion-kit:faq` | Turns repeat questions into an answer the team can find |

### Measure

| Command | What it does |
| - | - |
| `/champion-kit:maturity` | Scores your org on the steps of AI adoption with evidence, and writes a polished, shareable HTML report |

### Routines

`/champion-kit:routines` gives you ready-to-paste `/schedule` lines for a weekly patterns digest, a monthly stale guidance check, a weekly question digest, a quarterly maturity check, and a monthly lead update draft. Scheduled tasks are in research preview.

### Agent

`repo-scout` is a helper that `maturity`, `patterns`, `hackathon`, and `climb` hand the reading to. It can only read files: it has no shell and no file-editing tools. It reads only the repo and the files you approved, such as a git history export or transcripts you chose to share, and reports only counts, citations, and words from fixed lists. The command drops a whole report if any value isn't in a safe form, never runs those values as commands, and shows you each finding to confirm before it's used.

## What it will and won't do

- It reads your repo and asks you questions. It adds no hooks and no MCP servers. Some commands can read through tools you already have, such as `git`, the `gh` CLI, or your connectors, and they're written to ask first. Exports go to a new temp folder outside the repo, and the command deletes the files it made when it's done.
- Its instructions say never to send a message to anyone. Notes and invites are drafts for you to edit and send. The one exception is the office hours calendar event: it's created only with your own calendar connector, only after you approve the exact event, and only with the people you name. Scheduled tasks run unattended in the cloud, so each line limits what it reports, makes no edits, and tells the session not to call connectors. Keep that wording, and remove every connector you can when you paste.
- Its instructions say to ask before writing a file, such as a `CLAUDE.md` line, a skill, or `ai-maturity-report.html`. In auto mode or accept-edits mode, Claude Code itself won't stop that write, so use Manual mode if you want a prompt for every write.
- It never ranks people. The maturity report covers teams. `/champion-kit:climb` helps one person pick a next step, and that stays between the two of you.
- Security and data questions go to whoever owns them on your side.

## Learn more

- [Champion kit](https://code.claude.com/docs/en/champion-kit)
- [Communications kit](https://code.claude.com/docs/en/communications-kit), for admins and leads
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Scheduled tasks](https://code.claude.com/docs/en/routines)
