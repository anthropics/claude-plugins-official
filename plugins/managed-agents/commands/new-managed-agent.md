---
description: Create and set up a new Claude Managed Agents application
argument-hint: [project-name]
---

You are tasked with helping the user create a new Claude Managed Agents application. Follow these steps carefully.

## Reference Documentation

Before starting, review the official documentation to ensure you provide accurate, up-to-date guidance. Use WebFetch to read these pages:

1. **Start with the overview**: https://platform.claude.com/docs/en/managed-agents/overview
2. **Then the quickstart**: https://platform.claude.com/docs/en/managed-agents/quickstart
3. **Based on the user's language choice, read the appropriate SDK reference**:
   - Python: https://platform.claude.com/docs/en/managed-agents/python
   - TypeScript: https://platform.claude.com/docs/en/managed-agents/typescript
4. **Read the relevant guides** based on the user's needs:
   - Sessions API reference: https://platform.claude.com/docs/en/managed-agents/sessions
   - Tools: https://platform.claude.com/docs/en/managed-agents/tools
   - Environments: https://platform.claude.com/docs/en/managed-agents/environments
   - Any other guides linked from the overview

**IMPORTANT**: Always check for and use the latest versions of packages. Use WebSearch or WebFetch to verify current versions before installation. The Managed Agents API is in beta and shapes may change between releases; the docs are authoritative.

## The Core Model (read this before scaffolding)

Managed Agents has a two-object model that is different from the Messages API:

| Object | What it holds | How often you create it |
|---|---|---|
| **Agent** | model, system prompt, tools, MCP servers, skills | **Once.** Persisted and versioned. Store the `agent_id`. |
| **Session** | a running instance of an agent in an environment | **Every run.** References the agent by ID. |

Do not call `agents.create()` on every run. The agent is a setup artifact; the session is the runtime. If you find yourself putting `model`, `system`, or `tools` on a session body, stop: those belong on the agent.

## Gather Requirements

IMPORTANT: Ask these questions one at a time. Wait for the user's response before asking the next question.

1. **Language** (ask first): "Would you like to use Python or TypeScript?"

   - Wait for response before continuing

2. **Project name** (ask second): "What would you like to name your project?"

   - If $ARGUMENTS is provided, use that as the project name and skip this question
   - Wait for response before continuing

3. **Agent purpose** (ask third): "What will this agent do? Some examples:

   - Customer support agent (answers questions, files tickets)
   - Coding agent (reads/edits files, runs commands in a sandbox)
   - Research agent (web search, document analysis)
   - Custom (describe your use case)"
   - Wait for response before continuing

4. **Tools** (ask fourth): "Which tools does the agent need?

   - Built-in tools only (Bash, file operations, web search; runs entirely server-side)
   - Custom tools (your application executes them and sends results back)
   - MCP servers (connect to external tool providers)
   - None (conversation only)"
   - Wait for response before continuing

5. **Tooling choice** (ask fifth): Confirm package manager and runtime preferences (npm/pnpm/bun for TypeScript; pip/poetry/uv for Python).

After all questions are answered, proceed to create the setup plan.

## Setup Plan

Based on the user's answers, create a plan that includes:

1. **Project initialization**:

   - Create project directory (if it doesn't exist)
   - Initialize package manager:
     - TypeScript: `npm init -y`, set `"type": "module"` in package.json, add a "typecheck" script
     - Python: create `requirements.txt` or `pyproject.toml`
   - Add config files:
     - TypeScript: `tsconfig.json` configured for the SDK
     - Python: optionally a `pyproject.toml`

2. **Check for latest SDK versions**:

   - TypeScript: https://www.npmjs.com/package/@anthropic-ai/sdk
   - Python: https://pypi.org/project/anthropic/
   - Inform the user which version you're installing

3. **SDK installation**:

   - TypeScript: `npm install @anthropic-ai/sdk@latest`
   - Python: `pip install anthropic`
   - After installation, verify the installed version

4. **Create starter files**:

   The starter should have **two separate scripts** reflecting the agent/session split:

   - `setup` (or `setup.ts` / `setup.py`): creates the agent once via `client.beta.agents.create(...)`, creates or reuses an environment via `client.beta.environments`, and writes both IDs to a local file (e.g. `.agent.json`). Re-running it should update the existing agent in place rather than creating a duplicate.
   - `run` (or `run.ts` / `run.py`): reads the IDs file, creates a session via `client.beta.sessions.create(...)`, sends a user message event, and either streams or polls events until the session is idle. If the agent uses custom tools, this script handles `agent.custom_tool_use` events and replies with `user.custom_tool_result`.

   Use the SDK's `client.beta.*` resources rather than raw HTTP. The SDK sets the required beta header and handles request encoding; raw HTTP requires you to track field names and headers manually and is a common source of 400 errors.

5. **Environment setup**:

   - Create `.env.example` with `ANTHROPIC_API_KEY=your_api_key_here`
   - Add `.env` to `.gitignore`
   - Explain how to get an API key from https://console.anthropic.com/

6. **Optional**: offer to add a README explaining the agent/session split and how to extend the agent's tools.

## Implementation

After getting user confirmation on the plan:

1. Check for latest package versions
2. Execute the setup steps
3. Create all files
4. Install dependencies
5. Verify installed versions and inform the user
6. Create a working example based on their agent purpose and tool choice
7. Add brief comments explaining the agent/session split where it matters
8. **VERIFY THE CODE WORKS BEFORE FINISHING**:
   - TypeScript: run `npx tsc --noEmit` and fix all type errors
   - Python: verify imports resolve and there are no syntax errors
   - If the user has `ANTHROPIC_API_KEY` set, offer to run `setup` and then `run` end-to-end so they see a real session execute
   - Do NOT consider setup complete until verification passes

## Verification

After all files are created and dependencies installed, use the appropriate verifier agent to validate the application:

1. **For TypeScript projects**: launch the **managed-agent-verifier-ts** agent
2. **For Python projects**: launch the **managed-agent-verifier-py** agent
3. Review the verification report and address any issues

## Getting Started Guide

Once setup is complete and verified, give the user:

1. **Next steps**:

   - How to set their API key
   - How to run setup once: `python setup.py` / `npm run setup`
   - How to run the agent: `python run.py` / `npm run start`

2. **Useful resources**:

   - Overview: https://platform.claude.com/docs/en/managed-agents/overview
   - Sessions API reference: https://platform.claude.com/docs/en/managed-agents/sessions
   - Tools: https://platform.claude.com/docs/en/managed-agents/tools

3. **Common next steps**:

   - How to add or change tools on the agent (update + re-run setup)
   - How to attach MCP servers
   - How to switch from polling to SSE streaming
   - How to run fully server-side (built-in tools only, no local loop)

## Important Notes

- **ALWAYS USE LATEST VERSIONS** of the SDK; verify after install
- **USE THE SDK, NOT RAW HTTP**: `client.beta.agents` / `client.beta.sessions` / `client.beta.environments` handle the beta header and request encoding for you
- **AGENT ONCE, SESSION PER RUN**: keep agent creation in a separate setup script and persist the ID
- **VERIFY BEFORE FINISHING**: typecheck (TS) or import-check (Python), and offer an end-to-end run if a key is available
- Ask questions one at a time
- Check the docs for any version-specific requirements

Begin by asking the FIRST requirement question only. Wait for the user's answer before proceeding to the next question.
