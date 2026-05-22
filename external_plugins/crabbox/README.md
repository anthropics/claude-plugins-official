# Crabbox

Crabbox is a remote workspace control plane for maintainers and agents. It syncs the current checkout to a leased or user-provided runner, runs commands there, streams output, records logs/results, and releases the runner when work is complete.

This plugin adds a Claude Code skill that teaches Claude when and how to use the Crabbox CLI for remote validation. It does not bundle the Crabbox binary, start a background service, register hooks, or configure credentials.

## Requirements

- Crabbox CLI installed. See <https://crabbox.sh>.
- Local prerequisites used by Crabbox such as `git`, `ssh`, `ssh-keygen`, `rsync`, and `curl`.
- Crabbox authentication or provider configuration for the selected backend.
- A repository-level `crabbox.yaml` or `.crabbox.yaml` when the project has preferred providers, sync exclusions, jobs, or hydration settings.

## Typical Use

Install the Crabbox CLI, authenticate once, then ask Claude to run remote proof:

```sh
brew install openclaw/tap/crabbox
crabbox login
crabbox doctor
```

The skill prefers local targeted checks for tight edit loops and Crabbox for broader validation, cross-OS proof, Docker or E2E lanes, live-secret smoke tests, warmed reusable boxes, and durable run logs.

## Safety Notes

Crabbox may make external network calls, sync tracked and nonignored files from the current checkout to a remote runner, and run commands on cloud or user-provided infrastructure. Review repository config and command intent before using it with secrets or private code. Forward secrets only through explicit allowlists and stop leases created for the task when they are no longer needed.
