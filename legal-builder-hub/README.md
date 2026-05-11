# Legal Builder Hub Plugin

Community legal skills discovery and installation. Browses GitHub registries (lpm-skills, [additional registries — add via /legal-builder-hub:registry-browser], and others), installs and auto-updates, surfaces related community skills inside your other legal plugins. The cold-start interview IS the starter pack recommender — asks your practice type, recommends what to install.

**Every community skill is surfaced raw before install, scanned for prompt-injection patterns, and evaluated against the Legal Skill Design Framework. The plugin helps you find and evaluate; you decide what to trust.**

## Who this is for

Everyone using the other legal plugins. This is the app store.

## First run: cold-start

Asks your practice type, industry, team size, tooling comfort. Recommends a starter pack of community skills that match. Installs the ones you pick.

```
/legal-builder-hub:cold-start-interview
```

Your configuration is stored at `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` and survives plugin updates.

## Security posture

Installed community skills run with your access to client data, matter files, and your team's playbook. The hub treats every install and every update as a trust decision. Four layers of defense, none of which is sufficient on its own:

- **Allowlist (admin-controlled):** `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/allowlist.yaml` declares which registries, publishers, and MCP connectors community skills may use. `permissive` mode (default) warns on anything off-list; `restrictive` mode (recommended for firm / enterprise deployments) refuses it. The allowlist is checked before the installer reads any third-party content. See `skills/skill-installer/references/allowlist.md` for the schema.
- **Raw source, not summary:** the installer shows you the full raw `SKILL.md` — not an AI summary — before anything is written. A summary is a convenience; a skill that does something dodgy has to do it in text the raw display will show.
- **Heuristic scans:** both the installer and `skills-qa` scan the skill for prompt-injection patterns (override/authority claims, out-of-scope reads and writes, external URLs, hidden unicode, shell execution, credential asks). These are AI-heuristic scans, explicitly labeled as such — a clean scan is not a security audit, it is a prompt to read the text yourself.
- **Human approval, every time:** nothing is written to disk without a fresh typed `yes`. Approval is not inferred from earlier messages. For defense in depth, the installer recommends running the fetch / analysis in a read-only subagent so Write capabilities only become available after approval.

Updates use the same posture: the auto-updater pins to commit SHAs (not mutable tags), shows the full diff including hooks and MCP changes, and requires explicit approval per update. There is no auto-apply mode.

If a skill goes wrong after install: `/legal-builder-hub:disable [skill]` quiets it without removing files; `/legal-builder-hub:uninstall [skill]` removes it entirely. Both are restricted to community skills installed through this hub — they refuse to touch first-party plugin skills.

## Prerequisites

- Slack notifications from the registry-sync agent require a Slack MCP server configured in your environment. Without one, the agent writes its digest to a file.
- The default registry list in `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` ships empty except for `lpm-skills`. Add registries you trust via `/legal-builder-hub:registry-browser` or by editing `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md`.

## Commands

| Command | Does |
|---|---|
| `/legal-builder-hub:cold-start-interview` | Practice profile + starter pack recommendation |
| `/legal-builder-hub:registry-browser [query]` | Search watched registries for skills |
| `/legal-builder-hub:skill-installer [skill]` | Install a community skill |
| `/legal-builder-hub:auto-updater` | Check for updates to installed skills |
| `/legal-builder-hub:related-skills-surfacer` | Suggest skills based on what you've been doing |
| `/legal-builder-hub:skills-qa [skill]` | Evaluate a skill against the Legal Skill Design Framework before installing |
| `/legal-builder-hub:disable [skill]` | Disable an installed community skill without removing files |
| `/legal-builder-hub:uninstall [skill]` | Uninstall a community skill installed through the hub |

## Skills

| Skill | Purpose |
|---|---|
| **cold-start-interview** | Practice profile → starter pack |
| **registry-browser** | Search across watched registries |
| **skill-installer** | Allowlist-gate, fetch, show raw SKILL.md, trust-check, QA, install community skills |
| **uninstall** | Uninstall a community skill installed through the hub (first-party plugin skills are off-limits) |
| **disable** | Disable a community skill without removing its files; re-enable later |
| **skill-manager** | Reference: detailed uninstall/disable/re-enable workflows used by the `uninstall` and `disable` skills |
| **skills-qa** | Evaluate a skill against the Legal Skill Design Framework — design, failure modes, trust surface, and a prompt-injection heuristic scan |
| **auto-updater** | Check for updates; show diff and trust review; apply only on explicit approval |
| **related-skills-surfacer** | Surface related community skills after a task (direct or via hook) |

## Interactive commands vs. scheduled agents

The commands above run when you invoke them — for when you're working a matter. The agents below run on a schedule — for what moves while you're not looking:

| Agent | What it watches | Default cadence |
|---|---|---|
| **registry-sync** | Watched registries for new and updated skills; posts notifications per update preferences | Weekly |

## Watched registries (default)

The default allowlist ships with the community registries we've reviewed pre-configured. Edit `references/allowlist-default.yaml` in the repo, or your per-install allowlist at `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/allowlist.yaml`, to add, remove, or switch between restrictive and permissive modes.

- **lpm-skills** — Legal project management (Scott Margetts / LegalOps Consulting) — `github.com/legalopsconsulting/lpm-skills`
- **Lawvable / awesome-legal-skills** — Curated list of AI agent skills for legal work — `github.com/lawvable/awesome-legal-skills`
- **Lawvable / agent-skills** — Curated collection of agent skills for legal work — `github.com/lawvable/agent-skills`
- Add your own via `/legal-builder-hub:registry-browser` or by editing the allowlist

## How it learns

Your practice profile at `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` isn't static — it improves as you use the plugin. The hub re-reads it on every `/legal-builder-hub:registry-browser` and `/legal-builder-hub:related-skills-surfacer`, so adjusting your practice type, industry, or watched registries sharpens future recommendations. Edit the file directly or re-run `/legal-builder-hub:cold-start-interview --redo` when your work shifts.

## Notes

- Community skills are read before install. You see the **raw** SKILL.md — not a summary — before you accept.
- Auto-update is off by default. Turn it on per-skill if you trust the source.
- The related-skills-surfacer runs inside other plugins: when you're doing a task, it checks if the community has something relevant.
- Enterprise / firm deployments: set `mode: restrictive` in `allowlist.yaml` and populate the `registries`, `publishers`, and `connectors` lists. In restrictive mode the installer refuses to fetch, analyze, or install anything from an unlisted source.
