# Security policy

This plugin is a security tool, so it is held to the standard it applies to other people's code. If you find a vulnerability in the plugin itself, report it.

## Reporting a vulnerability

Report security issues **privately** through Anthropic's responsible disclosure program. See <https://www.anthropic.com/responsible-disclosure-policy> for the current reporting channel and safe-harbor terms.

Do **not** open a public GitHub issue for a security report. Include what you can of: the plugin version from `.claude-plugin/plugin.json`, your platform and Claude Code version, reproduction steps, and the impact you believe it has.

In scope: a vulnerability in the plugin's own code — its scripts, workflows, skills, agent definitions, hooks, and GitHub Action.

Out of scope: findings and verdicts about *your* code (best-effort by design, so a missed vulnerability or a wrong verdict there is a quality issue, not a plugin vulnerability); the behavior of Claude models themselves, such as jailbreaks or harmful content (the channel above routes those too); and anything downstream of a hostile repository or list of findings, per the trust model below. A way out of `scripts/sandbox.py`'s sandbox is in scope.

## Trust model

**The code you scan is trusted.** A scan or a fix that you start in your Claude Code session runs under your permissions, with no isolation layer of its own — so the repository's `.git/config` and its `.claude/` settings and hooks apply. The plugin does not attempt to stop a hostile repository from influencing a scan. The GitHub Action trusts everyone who can push in the same way: see [CI.md](CI.md). A hook refuses some shell commands of the plugin's agents; it guards against slips and is not a security boundary.

**Files and notes that you give a scan, and a list of findings that you name for a triage, are trusted like your code.**

Scan only code that you own or have permission to test. To work with code you do not fully trust, [sandbox the whole session](https://code.claude.com/docs/en/sandbox-environments) first. We suggest a disposable [virtual machine](https://code.claude.com/docs/en/sandbox-environments#virtual-machine) that shares no folders: copy the code in, scan, copy out only `CLAUDE-SECURITY-RESULTS.md`, delete the machine, then revoke its sign-in or API key. On Linux (not WSL 2), [`scripts/sandbox.py`](README.md#running-in-a-sandbox) sandboxes a headless session and keeps your credential outside it. It shares the host's kernel, and what lies in the scanned folder can still reach the model and the report. The report comes out into that folder, where a tool of the project, such as a docs build, can run text that the session wrote. To keep the report out, pass `--out` (`--output` in the `claude-security` command) with a folder outside it; a later scan does not check that report again.

The `claude-security` command runs a scan inside `scripts/sandbox.py`'s sandbox, unless you add `--no-sandbox`. The command is not supported on WSL 2. The scan can read the repository, the system's programs, what `--allow-read` names and a copy of your Claude Code settings. It writes only to memory and reaches only the model, and your credential stays outside. If another user can write a folder between the repository's top and the folder that you scan, the sandbox leaves the repository out: git fails there, and a scan of changes stops. The repository's `.claude/` settings and hooks do not apply to the command's scans, deny rules included. In the sandbox, neither do your organization's server-managed settings. The command's scans load no `CLAUDE.md` file, not even a managed one. The command itself runs outside the sandbox, where it reads the repository, runs read-only `git` commands and writes the report. It starts on the first Python on your `PATH`, so for code that you do not fully trust, deactivate a virtual environment that lies in the repository first.

The sandbox needs Python 3.10 or later.

The command's views run outside the sandbox, with your access, each in a Node.js process with two pipes and no credential in its environment. A view only draws what the command sends it. From Node.js 20 on, it runs under Node's permission model, which guards against a mistake and is no sandbox.

The live view loads into Claude Code's own process, with no sandbox, in every session that has the plugin. During a scan it sees the agents' prompts, calls and answers, and reads the scanned files, your Claude Code settings and the environment variables that tell your terminal's kind and colors. It changes no call, and uses no model, network or other process.

## The threat-model command

Claude is told to read only your code, folders that you name, a report in the folder where Claude Code started and, after you tick "Connectors", any connector that `/mcp` lists, unless you type which ones. Its search words, key words of findings among them, leave your machine, and a connector's page or a pasted text can mislead Claude. From Claude Code 2.1.196 on, the command blocks Claude Code's shell and web tools while it runs. If your message starts with the command, a hook also refuses Write and Edit on files not named like [the command's two](README.md#threat-model). If the hook fails, Claude Code's own checks decide, and you are not always told.

## Findings from hosted Claude Security

`/claude-security:hosted` reads findings through your session's Claude Security connector, with your sign-in and your permission settings. It pre-approves none of the connector's tools.

**The risk.** The trust model above does not cover a finding's text: it can describe code that is not in your checkout, and other people in your organization can write some of it. It can try to steer Claude to run a command, open or change a file, send data out, or change data in hosted Claude Security. The plugin tells Claude to treat it as data and, for a short time, can block some tools. That is not a security boundary, and in auto mode Claude Code may not ask you before a call.

**Best practices.**

- Work in default mode (Manual in the CLI). Read each call before you approve it, and each command that Claude gives you to run. Approve only what you asked for.
- Start a new session before other work, above all before another command of the plugin's.
- In auto mode, check every new and changed file before you run, test or commit it.
- If you allow the connector's tools by rule, allow only `list_projects`, `get_project`, `list_findings` and `get_finding`.
- For findings on code that you do not fully trust, sandbox the whole session. `scripts/sandbox.py` reaches no connector, so it does not serve here.

## Supported versions

Security fixes land on the latest released version of the plugin. There are no long-lived support branches. Update to the newest version before reporting.
