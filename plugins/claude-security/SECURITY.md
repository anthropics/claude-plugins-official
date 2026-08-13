# Security policy

This plugin is a security tool, so it is held to the standard it applies to other people's code. If you find a vulnerability in the plugin itself, report it.

## Reporting a vulnerability

Report security issues **privately** through Anthropic's responsible disclosure program. See <https://www.anthropic.com/responsible-disclosure-policy> for the current reporting channel and safe-harbor terms.

Do **not** open a public GitHub issue for a security report. Include what you can of: the plugin version from `.claude-plugin/plugin.json`, your platform and Claude Code version, reproduction steps, and the impact you believe it has.

In scope: a vulnerability in the plugin's own code — its scripts, workflow, skills, agent definitions, and hooks.

Out of scope: findings the scan produces about *your* code (best-effort by design, so a missed vulnerability there is a quality issue, not a plugin vulnerability); the behavior of Claude models themselves, such as jailbreaks or harmful content (the channel above routes those too); and anything downstream of a hostile repository, per the trust model below.

## Trust model

**The code you scan is trusted.** A scan and a fix run in your Claude Code session, under your permissions, with no isolation layer of the plugin's own — so the repository's `.git/config`, its `.claude/` settings and hooks, and everything else your session loads from that directory apply as usual. The plugin does not attempt to stop a hostile repository from influencing a scan.

To work with code you do not fully trust, sandbox the whole session first. We suggest [sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime), which enforces filesystem and network restrictions at the OS level without a container; its own README covers how to run Claude Code inside it.

## Supported versions

Security fixes land on the latest released version of the plugin. There are no long-lived support branches. Update to the newest version before reporting.
