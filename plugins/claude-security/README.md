# Claude Security Plugin for Claude Code

Put a team of agents to work as security researchers on your codebase: map the architecture, hunt across every component, and independently verify every finding before it reaches the report. Then, if you want, turn the confirmed findings into suggested fixes delivered as targeted patch files you review and apply when you choose.

This is the in-your-session version of [Claude Security](https://claude.com/product/claude-security), Anthropic’s hosted product for vulnerability detection and patching. It runs inside your Claude Code session, or from your shell with the `claude-security` command.

## Recommended models

We recommend Claude Opus 5.5 or Fable 5.2 for best performance. Pick a model using Claude Code's `/model` command.

In Opus 5.5 or Fable 5.2, portions of a scan may occasionally be downgraded to Opus 4.8. The rest of the scan will complete on your chosen model. Please share feedback with `/feedback` so we can keep improving our cybersecurity safeguards.

## Where it runs

A scan or a fix that you start in your Claude Code session runs under your permissions. There the plugin reads the repository you have open the same way you would, and a scan adds no isolation of its own: the directory's `.git/config` and its `.claude/` settings and hooks apply.

That makes it a natural fit for code you control — your own repositories, where the question is which bugs are in the code rather than whether the code is trying something. Scan only code that you own or have permission to test. If you are scanning a repository that you do not trust, sandbox the whole session first ([trust model](SECURITY.md#trust-model)), or, on Linux (not WSL 2), use [the plugin's sandbox](#running-in-a-sandbox).

The plugin pre-approves only file reads and its own questions. Claude Code's own permission rules decide on each other call that Claude makes:

- **In auto mode** Claude Code asks once whether to allow the workflow, the first time. After that its check judges each script call and workflow start. File writes in your project pass, as in any auto mode session.
- **In Manual mode** Claude Code asks you about most calls, many times in one scan. If you pick "Yes, and don't ask again", read the rule that Claude Code offers before you accept it: it can be wider than this plugin's scripts. For a write it holds until the session ends, and covers your own source files too.

If a call of your session is refused, that step does not run. The plugin's instructions have Claude tell you what is missing, for example the report, or the cleaning of credential values from it. A refused call of one of a scan's agents may go unreported.

In Claude Code 2.1.271 or newer, the scan's agents start without your `CLAUDE.md` and `AGENTS.md` files; your own session still loads them. To scan without the repository's Claude Code configuration, start Claude Code with `--setting-sources user` (with the plugin installed at user scope).

A `Read` deny rule [does not keep a file from every shell command](https://code.claude.com/docs/en/permissions#what-read-and-edit-rules-cover) that a scan runs, so keep secrets out of the whole repository and its git history.

## Installation

Install from the official Anthropic marketplace, then reload plugins in the same session:

    /plugin install claude-security@claude-plugins-official
    /reload-plugins

If Claude Code reports that the marketplace is not found, run `/plugin marketplace add anthropics/claude-plugins-official` first, then retry.

## Updating

Claude Code [updates plugins by itself](https://code.claude.com/docs/en/plugins/loading#when-auto-update-runs) from a marketplace that has auto-update on. To update the plugin yourself, run these in your shell, not in a Claude Code session:

    claude plugin marketplace update claude-plugins-official
    claude plugin update claude-security@claude-plugins-official

The new version loads in your next session. `claude plugin list` shows the installed version.

## Getting started

Run `/claude-security` for the menu. It offers four jobs:

| Job | What it scans |
| --- | --- |
| **Scan codebase** | The whole repository, or a scoped part of it |
| **Scan changes** | This branch's committed diff, a pull request's diff (with its branch checked out), or the commit you have checked out |
| **Vulnerability Triage** | A list of findings that you already have |
| **Suggest patches** | A report's findings, turned into patch files |

You can skip the menu. Type the job after the command (`/claude-security scan my branch at high`) or ask in plain words ("run a Claude Security scan on the whole repo at medium"). A scan asks you once to confirm its time and token cost, unless your request already accepts it.

In your session, a scan reports each stage as it starts, with the detail available by running `/workflows`, then assembles the report when the agents are done.

If a scan stops before its report, type `/claude-security continue the scan` in the same session, with the checkout and the scan's `CLAUDE-SECURITY-<timestamp>/` directory unchanged; open a closed session again with `claude --resume` first. The scan goes on from the answers of the agents that had finished, though it may run many of them again. A scan that failed after safeguards stopped an agent does not continue.

## Watch a scan in Claude Code

In Claude Code 2.1.292 and newer, the plugin's [mod](https://code.claude.com/docs/en/plugins/mods/overview) shows a live map of the code in the terminal while a scan runs: in a pane, or in a band above the prompt where the terminal is narrow. Press ctrl+x, then x, to close the pane, and again to hide the band. Type `/claude-security-view` to bring it back. To turn the view off, type `/plugin configure claude-security` and change **Live scan view**.

## Scan from your shell

The `claude-security` command starts Claude Code inside [the plugin's sandbox](#running-in-a-sandbox), runs a scan, and writes the same report. It ships with the plugin: run `<plugin>/claude-security` in the repository (on Windows, `python -IS <plugin>\scripts\cli.py`), where `<plugin>` is the `installPath` that `claude plugin list --json` shows. An update moves that folder, so to type just `claude-security`, as below, run it once with `--install`, or type `/claude-security:install-cli` in Claude Code.

    claude-security                  # scan the codebase
    claude-security --changes        # scan this branch's changes
    claude-security --tui            # watch the scan in your terminal

`claude-security --help` lists the options. The command's sandbox needs Linux 5.19 or newer and a user other than root; on Ubuntu 24.04 and newer, add `--sudo`. The command does not run on macOS. On Windows, it stops unless you add `--no-sandbox`. It signs in with your Claude Code login, your provider's variables, `gcloud` or `--credential-command`. If `claude` is a link into a package in your home folder, add `--allow-read` with the folder that holds the package and `node`.

`--tui` needs Node.js 18 or newer. [TUI.md](TUI.md) explains the screen and the keys.

## Choosing scope and scan effort

Two things shape a scan: **scope**, how much of the tree it looks at, and **scan effort**, how much work it does there. Say what you want if you know; if you don't, the plugin works it out with you rather than making you guess.

It reads the repository before it asks — how large the tree is, which directories hold real code, what branch you are on, whether there is a diff to scan — so the choice you are offered is concrete.

From there the scan sizes itself to the target. A narrow scope gets a pass proportionate to it, verified to the same standard: a thorough scan covers more ground, but every finding a quick scan does report has cleared the same verification bar. A large repository is scanned with attention on the code an attacker can reach, treating tests, fixtures and generated code as background rather than targets, plus a dedicated secrets pass that still checks fixtures for real committed keys. Unless you point the scan at it, a codebase scan is told to ignore vendored and installed third-party code, such as `node_modules` or a virtual environment: to read there only to understand your own code, and to report no finding there. A scan of changes still reviews a change to such code.

| Scan effort | What a codebase scan runs |
| --- | --- |
| `low` | One researcher for the whole target. |
| `medium` | The scan picks up to 48 components past 10,000 files, and fewer in a smaller target, with one researcher each. A further pass looks at files outside them. |
| `high` | Up to twice as many components (48 at most), a second researcher on each, and another pass across the boundaries between components. |

- Scan a git clone with its full history: at `medium` and `high`, researchers can also follow up past security fixes in the git log.
- To find more, choose `high`, scan a second time, or do both.
- A later codebase scan checks the last verified report's findings again, where it can match them to unchanged code. So most findings do not drop out only because the new scan missed them. The report's Coverage section normally says how many were checked again.

Scan effort is separate from your session's `/effort`.

A scan of changes is a security review of the diff. It reports only flaws the change takes part in and leaves the rest to a scan of the codebase. For a feature-sized change, choose `high` scan effort.

For a stronger review, type `/claude-security scan my branch --change-scan-effort high`. More researchers read the change, and it costs several times as much as `high` scan effort. The report then also lists flaws older than the change. Everything else on this page describes scans without this option.

## Context for one scan

A scan can first read what you know about your system, such as who can reach it: your notes, and up to 10 files from the folder that you scan. Name them in your request ("scan this repository, and read docs/arch.md first"), or give them when Claude asks. To have Claude offer the same files whenever it asks, keep them in a `.claude-security/` folder at the top of that folder. [`/claude-security:threat-model`](#threat-model) drafts such a file, `.claude-security/threat-model.md`. The agent that reads them is told to leave out statements that a part is out of scope, or that a risk is accepted. A wrong statement can hide a flaw, so give only files that you trust and that are current.

## What a scan gives you

Every scan writes its results into a timestamped `CLAUDE-SECURITY-<timestamp>/` directory in the folder where you started Claude Code, or, from the `claude-security` command, in the folder it scanned or the one that `--output` names:

- **`CLAUDE-SECURITY-RESULTS.md`** — the human-readable report: each finding with its impact, exploit scenario, preconditions, severity (CRITICAL, HIGH, MEDIUM or LOW, assigned from exploitability and impact along the lines of the [CVSS v4.0](https://www.first.org/cvss/v4-0/specification-document) qualitative scale), confidence, and a recommendation. Findings that the scan judges to be one flaw are shown as one, with the others listed under "Also reached at".
- **`CLAUDE-SECURITY-RESULTS.jsonl`** — the same findings in machine-readable form, one JSON object per line. Each record carries a `claudeSecurityPluginFindingId`, designed to stay the same from scan to scan so tooling can tell a known finding from a new one. The SARIF log carries the same id. Neither this file nor the SARIF log quotes the source line of a hard-coded credential finding, since that line is the credential; file, line and symbol locate it.
- **`CLAUDE-SECURITY-RESULTS.sarif`** — the same findings as a [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) log for GitHub code scanning, IDE SARIF viewers, and other tooling that speaks the standard.
- **`CLAUDE-SECURITY-REVISION-<sha12>.json`** — the revision stamp: which commit was scanned, the kind of run, the plugin's version, the scan effort, the severity counts, and how thoroughly the run was verified.

Once these files are written, an agent replaces each credential value it finds in the report, the JSONL and the SARIF log with `[REDACTED]`. It is a model's best effort, not a guarantee, so look over the files before you share them; if the agent ends with an error or reports a file it could not clean, the scan says so.

That is the whole report — the run's working files are removed once it is written, so the directory holds only what you read. It carries its own `.gitignore`, so a stray `git add` never sweeps a report or a suggested patch into a commit. Some packaging and deploy tools do not read that file, so move the directory out while you package or deploy. If you want the report in history, delete that one `.gitignore` and commit it like any other file.

The report's Coverage section names the areas that a whole-repository scan set aside, and why. To scan one of them, point a scan at it (`/claude-security scan only the tools folder`).

## How a finding earns its place

However much effort a scan spends, a finding reaches the report only after surviving verification. Every candidate is handed to independent verifiers whose job is to disprove it, working from the code rather than from the report of it. Each verifier also checks that an attacker can reach the flaw and gains something new from it. That is why the reports stay short. Verifiers take your README, SECURITY.md and other documents in the repository into account. They can still report a flaw that they judge serious, and then say which document they weighed, where they can.

A finding on its own also cannot claim more confidence than its verification earned, nor, once two of the verifiers who confirmed it have rated it, a higher severity than they support, and the record of how thoroughly a run was verified is computed in code rather than asserted by the model that produced the findings — so the report's own account of its rigor is one you can check.

Throughout, the scan is told to treat what the repository says as evidence, not instruction, and to note text addressed to it rather than obey it. Under the trusted-code model this keeps the work anchored to the evidence; it is not a defense against a hostile repository.

Scans are nondeterministic. Two scans of the same code can surface different findings, and a later scan can find more as models improve; running scans regularly builds coverage. Claude Security reasons about code the way a human security researcher does, which complements SAST, dependency scanning, and code review rather than replacing them.

## Triaging findings you already have

`/claude-security triage <path>` checks a list that another scanner or an earlier scan made: a SARIF file, or the folder of a scan's report. Run it in the folder that the list's paths start from. Three agents check each finding, so a long list takes time and tokens. `FINDINGS-TRIAGE.md` has the valid findings in the order to fix, and the plugin can then [suggest patches](#addressing-vulnerabilities). `FINDINGS-TRIAGE.sarif` is the list with the verdicts added, and marks the findings that were not validated as suppressed, except cases that the triage's closing message states; GitHub code scanning ignores the mark. A triage can reject a real finding, so read what it rejected.

## Addressing vulnerabilities

"Suggest patches" from the menu turns a report's findings into patch files you apply when you choose — from an existing report you pick, or from a fresh scan it runs first. The commit that the report scanned has to be in your current history. The plugin will not draft a fix against code the scan never saw, and it will tell you when a report has gone stale rather than patch from it. The agents can run your project's tests on your machine.

Each fix is developed in a scratch copy of the repository, and then reviewed by agents independent of the one that wrote it, including a fresh look at the diff on its own terms for anything new it might introduce.

A patch is written only when that review can vouch for three things: the change addresses that one finding, it introduces no new vulnerability, and it leaves the code's behaviour otherwise unchanged — and a change to which inputs the code accepts counts as a behaviour change. When it cannot vouch for all three, you get a short note explaining why instead of a patch. When the review marks the patched code as run by none of your project's tests, the patch notes that no project test of it was run, and its behaviour claim then rests on review rather than on a test run.

The patches land in the report's `patches/` folder: one `F<n>.patch` per finding, a short note beside each explaining the change and whether and how to apply it, and an index. Nothing is applied for you — the job does not apply, commit, or push anything. If you want a patch applied or turned into a pull request, ask, and Claude does that as a separate request you can watch.

## Threat model

    /claude-security:threat-model

Claude reads your code, and asks who can reach the system, whom it trusts, what matters most to protect, and what else it may read: folders of deployment files, your connectors, and what you paste. Claude is told to write `.claude-security/threat-model.md` only on your yes. If there is a scan's report, Claude is also told to ask, and on your yes to write `CLAUDE-SECURITY-PRECONDITIONS.md` in the report's folder, even if you say no to the threat model: it says whether each finding's preconditions hold in your deployment. The command needs Claude Code 2.1.196 or newer.

## Running in CI

The Claude Security plugin can also run as a GitHub Actions job that reviews each pull request and can block the merge. The other sections of this page speak of a session of your own. [CI.md](CI.md) says how the job runs, has the workflows to copy, and says whom the job trusts.

## Attack surface analysis

A scan finds bugs. An attack surface analysis finds code that an attacker can reach and nobody needs. Close that code off, and every bug in it, found or not, is out of reach. The analysis follows the method in Anthropic's research post [Using Claude to reduce the attack surface of code](https://www.anthropic.com/research/attack-surface-reduction), and complements a scan rather than replacing it. Type `/claude-security:attack-surface-analysis`, or ask in plain words, in a session opened at the repository's root. It runs three stages:

- **Default attack surface reduction:** code that the default configuration reaches but default functionality never uses.
- **Early reachability audit:** sensitive code that an attacker can reach before login, or without the victim doing anything.
- **Configuration interaction audit:** combinations of options that silently switch off a security feature.

It can take one to two and a half hours and uses many tokens, so it asks you to confirm before it starts. Leave the session open and the checkout unchanged until it finishes. The agents are told to read your code and run none of it. You get the same report files as from a scan, with proposed fixes as untested patch files. See [ATTACK-SURFACE.md](ATTACK-SURFACE.md) for details.

## Findings from hosted Claude Security

If your organization uses [Claude Security](https://claude.com/product/claude-security), the hosted product, you can read its findings in your session. Ask in plain words ("what does hosted Claude Security have open for this repo?"), paste a finding's link, or start with the command:

    /claude-security:hosted what is open for this repository?

It lists what is open, shows one finding, reports on a project, or says how to add this repository. To change a finding or a project there, use [claude.ai/security](https://claude.ai/security). You can ask Claude to fix a finding in your checkout. See [SECURITY.md](SECURITY.md#findings-from-hosted-claude-security) for the risk and best practices.

**Requirements.** The Claude Security connector. Claude Code [loads it from claude.ai](https://code.claude.com/docs/en/mcp#use-mcp-servers-from-claude-ai) when you are signed in with your claude.ai account, and `/mcp` lists it. If it is missing, ask your organization's admin.

## Running in a sandbox

On Linux 5.19 or newer (x86-64 or arm64), `scripts/sandbox.py` runs a headless session with nothing to install. WSL 2 is not supported, here or in the `claude-security` command. The session writes only to memory and reaches only the model, and your credential stays outside. Claude Code's environment variables, not its settings files, select the provider: the Claude API, Bedrock, Vertex or Foundry. The credential comes from them, `gcloud` or `--credential-command`, not from a `/login` sign-in. The report files are copied out at the end, into the scanned folder; for code you do not trust, add `--out` with a folder outside it. `<plugin>` is the plugin's folder. `--sudo` is needed on Ubuntu 24.04 and newer, `--check` tries files, network and processes from inside, and `--help` lists the options.

```bash
python3 -IS <plugin>/scripts/sandbox.py --sudo . -- claude -p "/claude-security:claude-security scan this whole repository at medium effort; I understand it may take a while and use a significant number of tokens" --plugin-dir <plugin> --permission-mode auto
```

Auto mode needs a model that supports it. With another model, Claude Code refuses each call that needs approval and gives no error. The sandbox covers only this session: "Suggest patches" in another session runs your project's tests with no sandbox. Only the command's own process reaches the model, so a wrapper must start `claude` with `exec`. Do not remove a disk while the scan runs: an unmount may not free it. Your global and system git settings do not apply inside, so a file that only they ignore makes the tree count as changed. If `claude` is a link into a package in your home folder, add `--read` with the folder that holds the package and `node`.

## Requirements

- Claude Code with this plugin installed
- Python 3.9 or newer on `PATH`; 3.10 or newer for the sandbox, also in the `claude-security` command
- A git checkout for scanning changes and suggesting patches — a whole-repository scan and a triage work without one

## Telemetry

The plugin reports usage counts (scans, triages and attack surface analyses started and finished, findings by severity and verdict, patches offered and drafted, which step failed when one does, and how often a scan is suggested after a push or a new pull request) and its Python minor version through Claude Code's built-in telemetry. To turn this off, use Claude Code's own settings: set `DISABLE_TELEMETRY=1` (or `DO_NOT_TRACK=1`, or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`) and these counts are not sent to Anthropic. See [Claude Code's data usage documentation](https://code.claude.com/docs/en/data-usage#telemetry-services). To stop the scan suggestion itself, set `CLAUDE_SECURITY_SCAN_TIP=off`.

## Security

The trust model and how to report a vulnerability in the plugin itself are in [SECURITY.md](SECURITY.md).
