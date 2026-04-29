# Addness

Addness connects Claude Code to your goal tree, tasks, comments, deliverables, notifications, members, and activity history through the official Addness MCP server.

## What It Does

- Read today's goals and goal trees from Addness.
- Inspect goal details, assignments, history, comments, and deliverables.
- Create and update goals, comments, assignments, deliverables, recurring goals, and invitations where the signed-in user has permission.
- Keep Claude Code grounded in the Addness workspace as the source of truth for goals and execution context.
- Guide Claude Code to respect Addness goal semantics: current state, desired state, and subgoals as execution steps.

## Requirements

- An Addness account.
- Access to an Addness workspace.

## Authentication

This plugin uses the official Addness remote MCP endpoint:

```text
https://vt.api.addness.com/mcp
```

Claude Code uses the MCP OAuth flow exposed by Addness. When prompted, sign in with your Addness account and authorize access to the workspace.

No API keys or secrets are included in this plugin.

## Security Notes

- Authentication is handled through Addness OAuth.
- The plugin does not bundle credentials.
- Claude Code receives only the permissions granted by the signed-in Addness user.

## Links

- Product: https://www.addness.com
