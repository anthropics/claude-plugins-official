# IP Counsel Plugin

Intellectual property practice: trademark, copyright, patent, trade secret, and open source. Drafts and triages cease-and-desist letters and DMCA takedowns (sending and responding), runs first-pass trademark clearance and freedom-to-operate triage, reviews IP clauses in agreements, tracks registrations and renewal deadlines, and checks open source license compliance. Built around a practice profile that gets written by a cold-start interview — the plugin learns *your* enforcement posture, portfolio, and approval matrix, not a generic one.

**Every output is a draft for attorney review — cited, flagged, and gated — not a legal conclusion.** The plugin does the work: reads the documents, applies your playbook, finds the issues, drafts the memo. A lawyer reviews, verifies, and decides. Citations are tagged by source so you know which ones came from a research tool and which ones need checking. Privilege markers are applied conservatively so nothing waives by accident. Consequential actions — filing, sending, executing — are gated behind explicit confirmation.

## Who this is for

| Role | Primary workflows |
|---|---|
| **In-house IP counsel** | Enforcement decisions, clause review, portfolio oversight, FTO triage |
| **IP paralegal / specialist** | Portfolio and renewal tracking, clearance first passes, matter intake |
| **Brand protection manager** | Cease-and-desists, DMCA takedowns, watch-service follow-up |
| **IP prosecutor (TM / copyright)** | Clearance, clause review, portfolio maintenance — *not patent claim drafting* |
| **Law firm IP associate** | Matter workspaces per client, clearance and FTO triage, clause review |
| **Legal ops managing an IP portfolio** | Registration tracker, renewal deadlines, OSS compliance checks |

This plugin does **not** draft patent claims. Patent prosecution with claim strategy is a specialist craft that needs a patent agent or patent attorney and should not be outsourced to a generalist tool. Patent work here is limited to FTO triage (is this product blocked by someone else's patent?), IP clause review in agreements, portfolio renewal tracking, and infringement triage.

## First run: the cold-start interview

On first use, the plugin interviews you — ten to fifteen minutes, conversational — to learn how your practice actually works. It asks about your practice area mix, your jurisdiction footprint, your enforcement posture, your approval matrix, and your escalation triggers. Then it asks for your portfolio list, brand guidelines, C&D templates, enforcement playbook, and OSS policy — whatever you have — so it can extract rather than making you re-type.

It writes what it learns to `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` — a plain-English document about your practice that every other skill reads before doing anything. You edit the document, not a config file.

```
/ip-legal:cold-start-interview
```

**Practice area mix.** Early in setup, you'll be asked which IP areas you actually work in — trademark, patent, copyright, trade secret, open source, or all. The plugin skips questions in areas you don't practice. Your configuration can hold multiple areas in parallel, and each skill asks which area applies when it's not obvious from what you paste.

**Enforcement posture.** You'll be asked where you land on the aggressive / measured / conservative spectrum for sending assertion letters, and who approves sending each letter type. The posture flips the defaults of the cease-and-desist, takedown, and infringement-triage skills.

## Commands

| Command | Does |
|---|---|
| `/ip-legal:cold-start-interview` | Run (or re-run) the cold-start interview |
| `/ip-legal:cease-desist [context]` | Cease-and-desist — send, or triage an inbound one, with the approval routing your CLAUDE.md requires |
| `/ip-legal:takedown [context]` | DMCA takedown — send, respond to a received notice, or draft a counter-notice |
| `/ip-legal:clearance [mark]` | First-pass trademark clearance — knockout + confusion analysis, attorney still signs off |
| `/ip-legal:fto-triage [product / claim scope]` | Freedom-to-operate triage — surfaces blocking references for attorney review |
| `/ip-legal:invention-intake [disclosure]` | Invention disclosure first-pass screen — novelty, obviousness, §101, bar dates, detectability, strategic value |
| `/ip-legal:infringement-triage [context]` | Infringement triage — is this worth pursuing, and how |
| `/ip-legal:ip-clause-review [file]` | Review IP clauses in an agreement — assignment, license grant, IP indemnity, OSS reps |
| `/ip-legal:oss-review [repo / file list]` | Open source license compliance check — copyleft obligations, attribution, license compatibility |
| `/ip-legal:portfolio` | Registration and renewal tracker — what's due, what's filed, what needs action |
| `/ip-legal:matter-workspace` | Manage matter workspaces (multi-client private practice only) — new, list, switch, close, none |

## Skills

| Skill | Purpose |
|---|---|
| **cold-start-interview** | First-run interview that writes `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` |
| **cease-desist** | Draft or triage a C&D; routes through the approval matrix before sending |
| **takedown** | DMCA notice, response to a received takedown, or counter-notice |
| **clearance** | Knockout search + likelihood-of-confusion first pass for a proposed mark |
| **fto-triage** | FTO triage — flags references an attorney should read before launch |
| **invention-intake** | First-pass patentability screen for an invention disclosure — novelty, obviousness, §101, bar dates, detectability, strategic value |
| **infringement-triage** | Given an apparent infringement, decide: ignore / soft letter / C&D / file |
| **ip-clause-review** | Reviews IP clauses in MSAs, SOWs, licenses, contractor agreements |
| **oss-review** | Checks open source licenses in a repo against the OSS policy |
| **portfolio** | Registration register, renewal deadlines, status dashboard |
| **matter-workspace** | Create, list, switch, and close matter workspaces for multi-client practices; isolates each client/matter so context does not leak across them |

## Interactive commands vs. scheduled agents

The commands above run when you invoke them — for when you're working a matter. The agents below run on a schedule — for what moves while you're not looking:

| Agent | What it watches | Default cadence |
|---|---|---|
| **ip-renewal-watcher** | Portfolio register — computes what's due (renewals, affidavits, maintenance) in the next 90 days and posts a ranked deadline report | Weekly |

## Connectors and citation verification

**Connect a research tool first — the citation guardrails depend on it.** Without one, every cite is tagged `[verify]` and the reviewer note above each deliverable records that sources weren't verified. The plugin works either way; it just does more of the verification for you when a research tool is connected.

The legal research connectors in this plugin aren't just data sources — they're the difference between a verified citation and a citation you have to check. A citation retrieved through **CourtListener** (U.S. court opinions, PACER dockets, citation verification) or **Descrybe** (primary-law search, citation treatment, quoted-language verification) is tagged with its source and can be traced back. A citation from the model's knowledge or from web search is tagged `[verify]` or `[verify-pinpoint]` and should be checked against a primary source before anyone relies on it. The plugin tiers its citations so your verification time goes where it matters.

## Integrations

Ships with connectors configured in `.mcp.json`:

- **Solve Intelligence** — patent and non-patent literature search, SEP technical standards, prior art, claim analysis
- **CourtListener** — U.S. court opinions, PACER dockets, citation verification
- **Descrybe** — primary law research by concept or wording, citation treatment, quoted-language verification
- **Slack** — search messages, read channels, find discussions
- **Google Drive** — search, read, and fetch documents

With patent research connected: FTO and prior-art skills pull references automatically instead of relying on user-supplied lists.

With a case-law tool connected: clearance and infringement-triage skills verify precedent and check whether a cited case is still good law.

With Drive or Slack connected: portfolio exports, C&D templates, and enforcement-log updates route through the channel you pointed us at.

## Quick start

### 1. Get interviewed

```
/ip-legal:cold-start-interview
```

Ten to fifteen minutes. Have your portfolio list, brand guidelines (if any), a C&D template (if any), and your OSS policy (if any) ready to share.

Your configuration is stored at `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` and survives plugin updates.

### 2. Clear a mark

```
/ip-legal:clearance "APEXLEAF"
```

Output: knockout-hit list, likelihood-of-confusion factor analysis, flags for attorney review. Not a go/no-go.

### 3. See what's due

```
/ip-legal:portfolio
```

Output: registrations with renewal, affidavit, or maintenance deadlines in the next 90 days, grouped by urgency.

## File structure

```
ip-legal/
├── .claude-plugin/plugin.json
├── .mcp.json
├── CLAUDE.md                    # Your practice profile — written by cold-start, edited by you
├── README.md
├── agents/
│   └── ip-renewal-watcher.md
├── skills/
│   ├── cold-start-interview/
│   ├── cease-desist/
│   ├── takedown/
│   ├── clearance/
│   ├── fto-triage/
│   ├── invention-intake/
│   ├── infringement-triage/
│   ├── ip-clause-review/
│   ├── oss-review/
│   ├── portfolio/
│   └── matter-workspace/
└── hooks/hooks.json
```

## Configuration

The plugin reads user-specific configuration from:

```
~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md
```

This path survives plugin updates. The `CLAUDE.md` that ships with the plugin is a template — it is replaced every upgrade. The cold-start interview writes your populated version to the config path above; from then on, edit that file directly when something changes.

## How it learns

Your practice profile at `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` isn't static — it improves as you use the plugin. Skills tell you when an output used a default you should tune. The `ip-renewal-watcher` agent tracks the portfolio register and surfaces upcoming renewal deadlines at your cadence. You can re-run setup, edit the file directly, or tell a skill to record a new position.

## Notes

- Every skill reads the practice profile first. If it finds placeholders, it stops and tells you to run `/ip-legal:cold-start-interview`. There's no generic fallback — a generic IP posture is worse than no posture.
- Sending a C&D starts a fight. The `/ip-legal:cease-desist` skill will not send anything itself; it drafts, surfaces the approval matrix entry, and waits for the approver.
- `/ip-legal:clearance` and `/ip-legal:fto-triage` are **first-pass** triage. The output is a research package for an attorney, not a clearance opinion. The skill says so on every run.
- `/ip-legal:oss-review` flags license obligations and incompatibilities. It does not bless a commercial-use decision — engineering and legal decide that together.
- Patent claim drafting is intentionally out of scope. This plugin plays well alongside a patent prosecution specialist; it does not replace one.
