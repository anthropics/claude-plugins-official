# security-guidance

Security review for Claude-generated code. Three layers:

1. **Pattern warnings** — instant regex-based reminders on `Edit`/`Write` for ~25 known-dangerous patterns (`yaml.load`, `torch.load(weights_only=False)`, `pickle.load` on untrusted data, raw `innerHTML`, hardcoded secrets, etc.).
2. **LLM diff review** — when Claude finishes a turn, the plugin sends the diff to a fast LLM call (the newest Opus by default) and feeds high-severity findings back to Claude so it can fix them before you see the response.
3. **Agentic commit review** — on `git commit`, an SDK-driven reviewer reads related files (`Read`/`Grep`/`Glob`) to trace data flow across the codebase, catching multi-file vulnerabilities pattern matching misses (IDOR, auth bypass, cross-file SSRF).

Findings cover common web-vulnerability classes — injection, XSS, SSRF, hardcoded secrets, IDOR, auth bypass, unsafe deserialization, and path traversal among others.

## Install

```
/plugin install security-guidance@claude-plugins-official
```

Marketplace ships enabled by default in Claude Code — no setup beyond having the CLI itself.

## Prerequisites

- Claude Code CLI ≥ v2.1.144
- Python 3.8+ on `PATH` (`python3`, `python`, or `py -3` — the plugin picks the first that works)
- Credentials for the LLM reviews: your Claude Code sign-in (a Claude apps gateway sign-in needs Claude Code 2.1.195 or later), an API key, or 3P provider config (see [Credentials](#credentials))

## Configuration

All configuration is via environment variables. None are required for default behavior.

### Selecting a model

By default both reviews run on the newest Claude Opus, and move to the next one when it is released — there is no model version to bump:

- The LLM diff review asks your API endpoint (`GET /v1/models`) which Opus models it serves and uses the newest. The answer is cached for a day in the plugin's state directory. If the endpoint can't answer, the review uses `claude-opus-5-5`.
- The agentic commit reviewer, and every review in a session signed in to a Claude apps gateway with `/login`, run through your installed Claude Code. Other reviews on Bedrock, Vertex, and Foundry run through the copy of Claude Code bundled with the Agent SDK, or `SG_AGENTIC_CLI_PATH` if set. All of them use Claude Code's `opus` alias: the model `/model opus` selects, including any `ANTHROPIC_DEFAULT_OPUS_MODEL` you have set. On a gateway that alias may name an older Opus than the newest one.

To pin a model, or to use a cheaper one:

```bash
# 1P / gateway: a canonical model id
SECURITY_REVIEW_MODEL=claude-opus-5-5

# Bedrock: use the inference-profile id
SECURITY_REVIEW_MODEL=us.anthropic.claude-opus-5-5

# Vertex / Foundry: the provider's model id
SECURITY_REVIEW_MODEL=claude-opus-5-5
```

`SECURITY_REVIEW_MODEL` controls the LLM diff review. `SG_AGENTIC_MODEL` (same syntax) controls the agentic commit reviewer.

### Credentials

The pattern warnings need no credentials. The LLM reviews (the diff review on Stop and the commit/push reviewer) use the first of these that applies:

- **A cloud provider (Bedrock, Vertex, Foundry)** — if Claude Code is configured for one, reviews run through Claude Code with that provider config.
- **`ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the environment** — used as is, against `ANTHROPIC_BASE_URL` if you set one.
- **Signed in to Claude Code (`/login`)** — Claude Code passes your sign-in to the plugin's hooks, and reviews use that account.
- **Signed in to a Claude apps gateway (`/login`)** — Claude Code passes no sign-in to plugins on a gateway, so reviews run through your installed Claude Code, which uses its own stored sign-in. The plugin never reads it. The plugin looks for Claude Code at `~/.local/bin/claude`, where the native installer puts it on macOS and Linux; on Windows, or for any other install, set `SG_AGENTIC_CLI_PATH` to its full path.

Claude Code does not pass your sign-in to plugins in a session started with `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY`, or `DO_NOT_TRACK` set. If no credentials reach the plugin, for that or any other reason, and the plugin cannot review through a Claude apps gateway sign-in, the LLM reviews are skipped and only the pattern warnings run. The plugin tells you so when Claude edits a file in a git repo, at most once a week. Set `ENABLE_CODE_SECURITY_REVIEW=0` if that is what you want; it also hides the notice.

### Enabling/disabling layers

| Variable | Default | What it does |
|---|---|---|
| `SECURITY_GUIDANCE_DISABLE=1` | unset | Kill switch — disables the entire plugin |
| `ENABLE_PATTERN_RULES=0` | on | Disable layer 1 (regex pattern warnings) |
| `ENABLE_CODE_SECURITY_REVIEW=0` | on | Disable all LLM reviews (Stop hook + commit/push) |
| `ENABLE_STOP_REVIEW=0` | on | Disable only the Stop-hook diff review, keeping commit/push reviews. Useful for multi-agent / shared-worktree setups where another agent can move HEAD between a worker's turns |
| `ENABLE_COMMIT_REVIEW=0` | on | Disable layer 3 (agentic commit review) |

### Hook output for other hosts

```bash
SECURITY_GUIDANCE_PORTABLE_OUTPUT=1   # default: detected
```

The hooks' JSON output carries two fields that only Claude Code reads (`metrics` and `rewakeSummary`), and the SessionStart hook prints a separate `{"async": ...}` line first. A host that validates hook output against a closed schema rejects them. In portable mode they are left out, so every hook prints one JSON object with only the standard fields (`decision`, `reason`, `systemMessage`, `hookSpecificOutput`), and the SessionStart hook runs to completion before the host continues. It turns on by itself when the host passes `PLUGIN_ROOT` and does not identify itself as Claude Code; set the variable to `1` or `0` to force it either way.

### Higher-recall mode

```bash
SG_DUAL_OR=on   # default off
```

Runs two parallel review calls and unions the findings. Catches a few percentage points more vulnerabilities in our testing, at roughly 2× the API cost per review. Most users don't need it.

## Org-specific policies

Drop a `claude-security-guidance.md` in any of:

- `~/.claude/claude-security-guidance.md` — user-wide rules (when `CLAUDE_CONFIG_DIR` is set, the same file in that directory is read too)
- `<project>/.claude/claude-security-guidance.md` — project rules, intended to be committed
- `<project>/.claude/claude-security-guidance.local.md` — local overrides, intended to be `.gitignore`'d

All three are loaded and concatenated into the LLM diff review's prompt in the order user → project → project-local. If the combined size exceeds the 8 KB prompt budget, the tail is truncated, so user-wide rules are kept and project-local rules are dropped first. The agentic commit reviewer (layer 3) does not currently read this file. Example:

```markdown
# Acme security rules

- All SELECTs against the `customers` or `orders` tables MUST go through `db.replica`,
  never `db.primary`. Primary is for writes only.
- Background jobs must not use the user-context auth token; they get
  service-account creds from `jobs.get_service_account()`.
- Calls to `requests.get(url)` with a user-controlled `url` need
  the SSRF-allowlist wrapper at `acme.net.safe_request`.
```

Built-in rules cover common web-vulnerability classes without it — `claude-security-guidance.md` is for things specific to your codebase that the model can't infer.

## Privacy and data handling

The plugin sends data to a model endpoint to perform its reviews. Specifically, each Stop-hook diff review transmits the changed file paths, the diff hunks, and the relevant file contents in the diff; each agentic commit review additionally transmits any files the reviewer pulls in via `Read`/`Grep`/`Glob` while tracing data flow. Your `claude-security-guidance.md` contents (user, project, and local) are appended to the prompt on every review, so don't put secrets in it.

Where that data goes depends on your Claude Code configuration:
- **Default (Anthropic API / subscription):** sent to `api.anthropic.com` and handled under Anthropic's [Commercial Terms](https://www.anthropic.com/legal/commercial-terms) and [Privacy Policy](https://www.anthropic.com/legal/privacy).
- **LLM gateway** (`ANTHROPIC_BASE_URL` set to a URL): sent to your gateway URL instead, with the headers in `ANTHROPIC_CUSTOM_HEADERS` (except `anthropic-beta`). The gateway operator's terms apply.
- **Claude apps gateway, signed in with `/login`:** your installed Claude Code sends the reviews to the gateway, using its own stored sign-in. The plugin never reads the sign-in. The gateway operator's terms apply.
- **3rd-party providers** (Bedrock / Vertex / Foundry / Mantle): sent to your configured provider endpoint. The provider's data-handling terms apply (e.g., AWS / GCP / Azure).

The plugin writes its own debug log to `~/.claude/security/log.txt` (override with `SECURITY_GUIDANCE_DEBUG_LOG`). The log contains diffstate metadata, finding categories, the Agent SDK's own warnings and errors, and up to 20 lines of stderr from each Claude Code run the plugin starts for a review (20 in all for each agentic commit review, which starts several runs) — no full file contents or model prompts — and rotates at 1 MB. Nothing is uploaded.

### Review usage and cost

The LLM reviews use your API path, so they cost tokens (or subscription usage) on top of your own session. The default reviewer is the newest Opus model. On the Anthropic API path the diff review on Stop calls the API directly, so it does not appear in Claude Code's own cost figures or transcripts. After each review the plugin writes one line to its debug log:

```
Review usage: review=stop session=<session id> model=claude-opus-5-5 calls=1 in=31994 out=3250 cache_read=0 cache_write=0 est_cost_usd=0.1930
```

- `review` is `stop`, `commit` or `push`; `session` is the Claude Code session that triggered it.
- `calls` counts API requests for the diff review and reviewer runs for the agentic commit/push review, where `model` is the model that was asked for (`opus` by default).
- `est_cost_usd` is an estimate at list prices, not a bill: on a subscription the review counts against your usage limits instead. A trailing `~` means the model had no entry in the plugin's price table and a default rate was used. A review cut short (timeout, session exit) may not be counted.
- The log rotates at 1 MB, so copy these lines out if you need a longer history.

To spend less, set `SECURITY_REVIEW_MODEL` (diff review) and `SG_AGENTIC_MODEL` (commit/push review) to a cheaper model, or turn reviews off (see [Enabling/disabling layers](#enablingdisabling-layers)).

## Limitations

This is a best-effort assistive tool, not a guarantee. Treat findings as suggestions, not as a substitute for human code review, SAST/DAST, dependency scanning, or pen-testing. The reviewer can miss vulnerabilities, produce false positives, and may behave differently across codebases, languages, and model versions. **No warranty is provided** — use is subject to Anthropic's [Commercial Terms](https://www.anthropic.com/legal/commercial-terms).

## Troubleshooting

**Plugin doesn't seem to fire** — check that `~/.claude/claude-security-guidance.md` (or hook activity) shows in debug logs. Run Claude Code with `--debug-file /tmp/claude/debug.txt` and grep for `security_reminder_hook`. The plugin also writes its own log to `~/.claude/security/log.txt`.

**Review never finds anything** — verify your API path works, and that credentials reach the plugin (see [Credentials](#credentials)): `~/.claude/security/log.txt` says `no API credentials` when they don't. When a commit or push review gets no usable answer from the model, Claude is told once per session for each kind of review and failure (for example "Commit security review did not complete: …"), and the reason is logged. If a commit whose review failed is pushed later from Claude Code, the push review checks it. On 3P providers, if you set `SECURITY_REVIEW_MODEL`, check it is a provider-specific id your account can invoke. On LLM gateways, check the gateway's logs for `POST /v1/messages` traffic from the plugin. In a session signed in to a Claude apps gateway with `/login`, reviews run only when `claude auth status` shows the gateway and that you are logged in. They run through the Claude Code at `~/.local/bin/claude`, where the native installer puts it on macOS and Linux. On Windows, or for any other install, set `SG_AGENTIC_CLI_PATH` to its full path.

**Too many false positives** — set `SECURITY_REVIEW_MODEL` to a cheaper model (`claude-sonnet-5-5`) and re-evaluate; if precision is the priority, stay on the default.

**Want to silence a specific finding** — add a comment to the line explaining why it's safe; the LLM reviewer treats inline justifications as exclusions. For systemic exclusions, document them in your `claude-security-guidance.md`.

## Reporting issues

Open an issue on the [security-guidance plugin repo](https://github.com/anthropics/claude-code/issues) with:
- The Claude Code CLI version (`claude --version`)
- Provider setup (1P / Bedrock / Vertex / LLM gateway / etc.)
- A minimal repro diff
- The relevant section of `~/.claude/security/log.txt`
