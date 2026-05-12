# Quick Start

**60 seconds.** This gets you to using your plugins.

## Install in Claude Cowork
1. [Install Claude Desktop](https://claude.com/download)
2. Get access to Claude Cowork
3. Follow the instructions in the video below:

https://github.com/user-attachments/assets/51394f0a-5277-4fe2-b81c-5c5e9ac876b5

## Install in Claude Code

1. **Open Claude Code** (in your terminal) or **Claude Cowork** (the desktop app). Not sure which you have? If you have a terminal window open with Claude in it, that's Claude Code.

2. **Add the marketplace.** In Claude Code, type `/plugin marketplace add ` (with a space at the end), then **drag the unzipped `claude-for-legal` folder onto the terminal window** — it'll fill in the path. Then press Enter.

   (Or type the full path: `/plugin marketplace add /Users/you/Desktop/claude-for-legal`)

3. **Install your plugin.** Pick the one that matches your work from the table below, then:
   ```
   /plugin install privacy-legal@claude-for-legal
   ```

4. **⚠️ Restart Claude Code.** Close and reopen. This step is not optional — the plugin isn't live until you restart.

5. **Run setup.** Takes 2 minutes (quick start) or 10-15 minutes (full).
   ```
   /privacy-legal:cold-start-interview
   ```

6. **Connect a research tool.** Citations are flagged unverified without one. In Cowork: Settings → Connectors → add CourtListener. In Claude Code: the plugin already lists the research MCP in its config; you'll be prompted to authorize it the first time a skill needs it.

## Install user-scoped, not project-scoped

When you run `/plugin install`, you may be asked whether to install for this project only or for all projects (user scope). **Pick user scope.**

It's counterintuitive: project scope feels safer. But project scope blocks the plugin from reading files outside the project folder — your outlines in Downloads, your contract in Documents, your client file in Dropbox. Most skills need to read your files. User scope doesn't give the plugin any extra access to your files — the plugin can only read files you explicitly point it at or that are in the current directory. It just means the plugin works from any folder instead of one.

If you already installed project-scoped and want to switch: `/plugin uninstall <plugin>`, then `/plugin install <plugin>@claude-for-legal` from your home directory.

## Which plugin is for me?

| You are a… | Install… | First command |
|---|---|---|
| Privacy lawyer / DPO | `privacy-legal` | `/privacy-legal:use-case-triage` |
| Commercial / contracts lawyer | `commercial-legal` | `/commercial-legal:review` |
| Corporate / M&A lawyer | `corporate-legal` | `/corporate-legal:diligence-issue-extraction` |
| Employment lawyer / HR counsel | `employment-legal` | `/employment-legal:wage-hour-qa` |
| Product counsel | `product-legal` | `/product-legal:is-this-a-problem` |
| IP lawyer / patent agent | `ip-legal` | `/ip-legal:clearance` |
| Litigator (in-house or firm) | `litigation-legal` | `/litigation-legal:matter-intake` |
| Regulatory / compliance counsel | `regulatory-legal` | `/regulatory-legal:reg-feed-watcher` |
| AI governance lead | `ai-governance-legal` | `/ai-governance-legal:use-case-triage` |
| Clinic supervisor (law school) | `legal-clinic` | `/legal-clinic:cold-start-interview` |
| Law student | `law-student` | `/law-student:cold-start-interview` |
| Legal ops / looking for skills | `legal-builder-hub` | `/legal-builder-hub:registry-browser` |

## What you're installing

Each plugin learns your playbook through a setup interview, writes it to a practice profile file (`~/.claude/plugins/config/claude-for-legal/<plugin>/CLAUDE.md`), and every skill reads from it. The profile is yours — edit it, re-run setup, or tell a skill to update it.

**Every output is a draft for attorney review.** The plugins flag what they're unsure about, mark citations by source, and gate anything irreversible. A lawyer reviews, verifies, and takes responsibility. They make that review faster; they don't replace it.

## What's in the box

12 practice-area plugins, 5 managed-agent cookbooks, 16+ connectors. The full reference is in [README.md](README.md).

## Stuck?

- **"Command not found"** after install → you forgot step 4. Restart Claude Code.
- **"Run setup first"** → run `/<plugin>:cold-start-interview` before any other command.
- **Citations flagged `[verify]`** → connect a research tool (step 6). Without one, every cite is from training data, not a current database.
- **"I can't read [file]"** → most often this means the plugin is project-scoped and the file is outside the project folder. See "Install user-scoped, not project-scoped" above — reinstall user-scoped or move the file into the project folder.
- **The plugin doesn't do X** → run `/legal-builder-hub:related-skills-surfacer` to find a better match, or check the plugin's README for "What this plugin does not do."
