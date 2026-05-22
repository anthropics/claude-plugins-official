---
name: crabbox
description: This skill should be used when the user asks to "run it on Crabbox", "use crabbox", "remote validation", "run the full suite remotely", "warm a box", "reuse a remote runner", "inspect crabbox logs", "publish remote proof", or needs cloud-backed test execution, cross-OS validation, Actions hydration, secret-safe smoke tests, durable logs/results, captures, cache inspection, or lease cleanup with the Crabbox CLI.
version: 0.1.0
---

# Crabbox

Use Crabbox when a repository needs proof that is too broad, slow, environment-dependent, or secret-dependent for the local edit loop. Crabbox syncs the current checkout to a remote runner, executes the requested command, streams output, records run evidence, and manages lease cleanup.

Prefer local targeted checks for fast iteration. Move to Crabbox for full suites, Docker or E2E lanes, package install proof, cross-OS behavior, hosted services, live-provider smoke tests, warmed reusable state, or cases where the laptop is not representative of CI.

## First Checks

Run from the repository root. Crabbox mirrors the current checkout, so inspect local state before remote proof:

```sh
git status --short
command -v crabbox
crabbox --version
crabbox doctor
```

Read `crabbox.yaml` or `.crabbox.yaml` before adding provider, class, sync, hydration, or job flags. Repository config is the source of truth for default backends, named jobs, sync exclusions, and environment policy.

If the CLI is missing, install it from the Crabbox docs or ask the user before installing software. On macOS with Homebrew:

```sh
brew install openclaw/tap/crabbox
```

Brokered operation requires auth. Use `crabbox login` for an interactive user login. Use token-based login only when the user or trusted automation has provided a coordinator token; never ask for cloud provider credentials unless the user explicitly wants direct-provider operation.

## Choose The Run Shape

Use a one-shot run for a single proof:

```sh
crabbox run --timing-json --preflight -- pnpm test
```

Use a reusable lease when several commands need the same warmed machine:

```sh
crabbox warmup --idle-timeout 90m
crabbox run --id <lease-id-or-slug> -- pnpm test:changed
crabbox stop <lease-id-or-slug>
```

Use named jobs when the repository defines them:

```sh
crabbox job run full-ci
```

Use manual Actions hydration for a reused lease when repository setup should happen before multiple commands:

```sh
crabbox actions hydrate --id <lease-id-or-slug>
crabbox run --id <lease-id-or-slug> -- pnpm test:changed
```

Use `--github-runner` hydration only when the workflow needs full GitHub Actions behavior such as repository secrets, OIDC, service containers, or unsupported `uses:` steps.

## Scripts, Secrets, And Sync

Prefer uploaded scripts for multi-line proof commands:

```sh
crabbox run --script ./scripts/e2e-smoke.sh --timing-json
```

Forward secrets only through explicit allowlists and never print values:

```sh
crabbox run \
  --env-from-profile ~/.project-live.profile \
  --allow-env API_TOKEN \
  --preflight \
  --script ./scripts/live-smoke.sh
```

Treat captured logs and downloads as potentially secret-bearing until reviewed.

Use fresh PR checkout when dirty local state would confuse the result:

```sh
crabbox run --fresh-pr owner/repo#123 --script ./scripts/e2e-smoke.sh
crabbox run --fresh-pr 123 --apply-local-patch -- pnpm test
```

Use `--full-resync` when a warm lease has stale files, suspicious sync fingerprints, or SSH/rsync watchdog output recommends it.

## Observability

Add `--preflight` before unfamiliar runs to capture the remote user, working directory, target OS, and important tool availability. Add `--timing-json` for broad runs, flaky latency, provider comparison, or sync debugging.

Print phase markers inside long commands:

```sh
echo CRABBOX_PHASE:install
pnpm install --frozen-lockfile
echo CRABBOX_PHASE:test
pnpm test
```

Coordinator-backed runs print a `run_...` handle. Keep it in status updates and use the CLI for inspection:

```sh
crabbox attach <run-id>
crabbox events <run-id> --json
crabbox logs <run-id>
crabbox results <run-id>
```

For desktop or browser proof, prefer Crabbox's built-in desktop and artifact commands over ad hoc screenshot scripts:

```sh
crabbox webvnc --id <lease-id-or-slug> --open
crabbox desktop doctor --id <lease-id-or-slug>
crabbox artifacts collect --id <lease-id-or-slug> --all --output artifacts/
```

## Failure Triage

Classify failures before retrying: missing CLI, auth/config, provider capacity, hydration/setup, sync, command failure, or cleanup uncertainty.

Use these checks before changing providers or asking for credentials:

```sh
crabbox config show
crabbox whoami
crabbox sync-plan
crabbox run --debug --timing-json -- <focused-command>
```

If the command fails, rerun the focused failing shard or entrypoint first. Avoid repeating a full suite until the narrower failure is understood.

If cleanup is unclear, list or inspect leases and stop only resources created for the current task:

```sh
crabbox list
crabbox inspect --id <lease-id-or-slug> --json
crabbox stop <lease-id-or-slug>
```

## Boundaries

Keep project-specific setup in the repository's hydration workflow, devcontainer, Nix/mise/asdf config, package scripts, or `.crabbox.yaml`. Use Crabbox for lease management, sync, command execution, logs/results, timing, artifacts, and cleanup.

Do not sync credentials as repository files. Do not rely on inherited shell environment as permission to forward secrets. Do not leave intentionally reusable leases running without telling the user the lease ID, command history, and cleanup plan.
