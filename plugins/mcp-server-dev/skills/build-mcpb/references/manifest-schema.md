# MCPB Manifest Schema (v0.4)

Validated against `github.com/anthropics/mcpb/schemas/mcpb-manifest-v0.4.schema.json`. The schema uses `additionalProperties: false` — unknown keys are rejected. Add `"$schema"` to your manifest for editor validation.

---

## Top-level fields

| Field | Required | Description |
|---|---|---|
| `manifest_version` | ✅ | Schema version. Use `"0.4"`. |
| `name` | ✅ | Package identifier (lowercase, hyphens). Must be unique. |
| `version` | ✅ | Semver version of YOUR package. |
| `description` | ✅ | One-line summary. Shown in marketplace. |
| `author` | ✅ | `{name, email?, url?}` |
| `server` | ✅ | Entry point and launch config. See below. |
| `display_name` | | Human-friendly name. Falls back to `name`. |
| `long_description` | | Markdown. Shown on detail page. |
| `icon` / `icons` | | Path(s) to icon file(s) in the bundle. |
| `homepage` / `repository` / `documentation` / `support` | | URLs. |
| `license` | | SPDX identifier. |
| `keywords` | | String array for search. |
| `user_config` | | Install-time config fields. See below. |
| `compatibility` | | Host/platform/runtime requirements. See below. |
| `tools` / `prompts` | | Optional declarative list for marketplace display. Not enforced at runtime. |
| `tools_generated` / `prompts_generated` | | `true` if tools/prompts are dynamic (can't list statically). |
| `screenshots` | | Array of image paths. |
| `localization` | | i18n bundles. |
| `privacy_policies` | | URLs. |

---

## `server` — launch configuration

```json
"server": {
  "type": "node",
  "entry_point": "server/index.js",
  "mcp_config": {
    "command": "node",
    "args": ["${__dirname}/server/index.js"],
    "env": {
      "API_KEY": "${user_config.apiKey}",
      "ROOT_DIR": "${user_config.rootDir}"
    }
  }
}
```

| Field | Description |
|---|---|
| `type` | `"node"`, `"python"`, or `"binary"` |
| `entry_point` | Relative path to main file. Informational. |
| `mcp_config.command` | Executable to launch. |
| `mcp_config.args` | Argv array. Use `${__dirname}` for bundle-relative paths. |
| `mcp_config.env` | Environment variables. Use `${user_config.KEY}` to substitute user config. |

**Substitution variables** (in `args` and `env` only):
- `${__dirname}` — absolute path to the unpacked bundle directory
- `${user_config.<key>}` — value the user entered at install time
- `${HOME}` — user's home directory

**There are no auto-prefixed env vars.** The env var names your server reads are exactly what you declare in `mcp_config.env`. If you write `"ROOT_DIR": "${user_config.rootDir}"`, your server reads `process.env.ROOT_DIR`.

---

## `user_config` — install-time settings

```json
"user_config": {
  "apiKey": {
    "type": "string",
    "title": "API Key",
    "description": "Your service API key. Stored encrypted.",
    "sensitive": true,
    "required": true
  },
  "rootDir": {
    "type": "directory",
    "title": "Root directory",
    "description": "Directory to expose to the server.",
    "default": "${HOME}/Documents"
  },
  "maxResults": {
    "type": "number",
    "title": "Max results",
    "description": "Maximum items returned per query.",
    "default": 50,
    "min": 1,
    "max": 500
  }
}
```

| Field | Required | Description |
|---|---|---|
| `type` | ✅ | `"string"`, `"number"`, `"boolean"`, `"directory"`, `"file"` |
| `title` | ✅ | Form label. |
| `description` | ✅ | Help text under the input. |
| `default` | | Pre-filled value. Supports `${HOME}`. |
| `required` | | If `true`, install blocks until filled. |
| `sensitive` | | If `true`, stored in OS keychain + masked in UI. **NOT `secret`** — that field doesn't exist. |
| `multiple` | | If `true`, user can enter multiple values (array). |
| `min` / `max` | | Numeric bounds (for `type: "number"`). |

`directory` and `file` types render native OS pickers — prefer these over free-text paths for UX and validation.

---

## `compatibility` — gate installs

```json
"compatibility": {
  "claude_desktop": ">=1.0.0",
  "platforms": ["darwin", "win32", "linux"],
  "runtimes": { "node": ">=20" }
}
```

| Field | Description |
|---|---|
| `claude_desktop` | Semver range. Install blocked if host is older. |
| `platforms` | OS allowlist. Subset of `["darwin", "win32", "linux"]`. |
| `runtimes` | Required runtime versions, e.g. `{"node": ">=20"}` or `{"python": ">=3.11"}`. |

---

## Minimal valid manifest

```json
{
  "$schema": "https://raw.githubusercontent.com/anthropics/mcpb/main/schemas/mcpb-manifest-v0.4.schema.json",
  "manifest_version": "0.4",
  "name": "hello",
  "version": "0.1.0",
  "description": "Minimal MCPB server.",
  "author": { "name": "Your Name" },
  "server": {
    "type": "node",
    "entry_point": "server/index.js",
    "mcp_config": {
      "command": "node",
      "args": ["${__dirname}/server/index.js"]
    }
  }
}
```

---

## What MCPB does NOT have

- **No `permissions` block.** There is no manifest-level filesystem/network/process scoping. The server runs with full user privileges. Enforce boundaries in your tool handlers — see `local-security.md`.
- **No auto env var prefix.** No `MCPB_CONFIG_*` convention. You wire config → env explicitly in `server.mcp_config.env`.
- **No `entry` field.** It's `server` with `entry_point` inside.
- **No `minHostVersion`.** It's `compatibility.claude_desktop`.
