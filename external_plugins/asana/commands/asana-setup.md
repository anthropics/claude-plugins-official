---
description: Set up the Asana V2 MCP server connection (one-time OAuth app + claude mcp add)
argument-hint: "[client_id]"
---

The user wants to connect Claude Code to Asana's V2 MCP server. Guide them through the one-time setup below. Do NOT run `claude mcp add` yourself — the `--client-secret` prompt needs a real terminal (a hidden TTY prompt), so the user must run it in their own terminal.

Their Asana OAuth Client ID (if provided): `$1`

Print these steps clearly, substituting the Client ID into the command if `$1` is non-empty (otherwise leave the `YOUR_CLIENT_ID` placeholder):

## Step 1 — Create an Asana OAuth app (one time)

1. Open the Asana developer console: https://app.asana.com/0/my-apps
2. Create a new app.
3. Under **OAuth**, add this exact **Redirect URL**:
   ```
   http://localhost:8080/callback
   ```
4. Copy the **Client ID** and **Client Secret**.

Note: `localhost` is correct — Claude Code is a local client and catches the OAuth callback on your own machine. Asana's V2 server does not support Dynamic Client Registration, so you must bring your own client_id + client_secret.

## Step 2 — Add the server (run this in YOUR terminal)

```bash
claude mcp add --transport http \
  --client-id YOUR_CLIENT_ID --client-secret \
  --callback-port 8080 \
  asana https://mcp.asana.com/v2/mcp
```

- `--client-secret` (no value) triggers a hidden prompt; paste the Client Secret there. It is stored in your OS keychain.
- The port in `--callback-port` must match the `http://localhost:8080/callback` redirect you registered.

## Step 3 — Authenticate & verify

1. On first use, Claude Code opens your browser for Asana consent — approve it.
2. Run `/mcp` and confirm `asana` shows as **connected**.
3. Test it: ask "list my Asana workspaces".

After printing the steps, offer to help troubleshoot if they hit `invalid_redirect_uri` (redirect/port mismatch) or `invalid_client` (wrong id/secret).
