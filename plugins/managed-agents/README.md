# Claude Managed Agents Development Plugin

A plugin for building applications on [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview), Anthropic's hosted agent runtime.

## What's included

### `/new-managed-agent` slash command

Scaffolds a new Managed Agents application in Python or TypeScript. Walks through language and tooling choices, fetches the current documentation, and generates a two-file starter:

- a **setup** script that creates the agent and environment once and persists their IDs
- a **run** script that creates a session, sends a user message, and drives the event loop

The command emphasizes the agent/session split (agent is a one-time versioned config; sessions are per-run) and steers toward the SDK's `client.beta.*` resources rather than raw HTTP.

### Verifier subagents

- `managed-agent-verifier-py`
- `managed-agent-verifier-ts`

Invoked after scaffolding (or on an existing project) to check SDK version, agent/session split, event handling, secrets hygiene, and an optional end-to-end run.

## Installation

```
/plugin install managed-agents
```

## Usage

```
/new-managed-agent my-support-bot
```

## Documentation

- [Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [Quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [Sessions API reference](https://platform.claude.com/docs/en/managed-agents/sessions)
