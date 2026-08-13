# Asana

[Asana](https://asana.com) is a work management platform for tasks, projects, and goals. This plugin connects Claude Code to Asana's **V2 MCP server** so you can create and manage tasks, search projects, update assignments, and track progress directly from your terminal.

> **Migrating from V1?** The V1 beta server (`https://mcp.asana.com/sse`) is deprecated and shuts down on **Wed 5 Aug 2026**. The V2 server requires each user to bring their own Asana OAuth app — Dynamic Client Registration is **not** supported on V2, so there is no zero-config connect. Follow the setup below (or run `/asana-setup`).

## Setup

You only need to do this once. The fastest path is to run **`/asana-setup`** inside Claude Code and follow the printed steps, or do it manually:

### 1. Create an Asana OAuth app

1. Go to the [Asana developer console](https://app.asana.com/0/my-apps).
2. Create a new app.
3. Under **OAuth**, add this exact **Redirect URL**:

   ```
   http://localhost:8080/callback
   ```

   (This is Claude Code's local OAuth callback. It is `localhost` by design — Claude Code runs on your machine and catches the authorization code on a local listener. It must match the `--callback-port` you use below.)
4. Copy your **Client ID** and **Client Secret**.

### 2. Add the Asana V2 server to Claude Code

Run this in your terminal (not inside a Claude prompt — the secret is entered at a hidden prompt):

```bash
claude mcp add --transport http \
  --client-id YOUR_CLIENT_ID --client-secret \
  --callback-port 8080 \
  asana https://mcp.asana.com/v2/mcp
```

- Replace `YOUR_CLIENT_ID` with the Client ID from step 1.
- `--client-secret` with no value makes Claude Code prompt for the secret and store it securely in your OS keychain (never on disk).
- `--callback-port 8080` must match the port in the redirect URL you registered.

### 3. Authenticate and verify

1. The next time the `asana` server is used, Claude Code opens your browser for Asana consent. Approve it.
2. Confirm the connection:

   ```
   /mcp
   ```

   You should see `asana` listed as **connected**.
3. Try it: ask Claude Code to "list my Asana workspaces" or "show my assigned tasks."

## Example usage

Ask Claude Code to:

- "Create an Asana task in the Backend project titled 'Fix login bug' assigned to me."
- "What are my Asana tasks due this week?"
- "Search Asana for projects about onboarding."

## Troubleshooting

- **`invalid_redirect_uri`** — the redirect URL in your Asana app must be exactly `http://localhost:8080/callback`, and the `--callback-port` must be `8080`. If you use a different port, register `http://localhost:<PORT>/callback` to match.
- **`invalid_client`** — double-check the Client ID and re-enter the Client Secret (`claude mcp remove asana`, then re-run the add command).
- **Auth server / DCR errors** — V2 does not support Dynamic Client Registration; you must supply a pre-registered `--client-id` and `--client-secret` as shown above.

## Documentation

- [Integrating with Asana's MCP server](https://developers.asana.com/docs/integrating-with-asanas-mcp-server)
- [Connecting MCP clients to Asana's V2 server (Claude Code)](https://developers.asana.com/docs/connecting-mcp-clients-to-asanas-v2-server)
