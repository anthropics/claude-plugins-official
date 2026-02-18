# Logfire

[Logfire](https://pydantic.dev/logfire) is an observability platform by Pydantic for monitoring and debugging your applications. This plugin connects Claude Code to your Logfire account, letting you query traces, analyze logs, and investigate performance issues directly from your terminal.

## Setup

### 1. Create a Logfire Account

Sign up at [logfire.pydantic.dev](https://pydantic.dev/logfire) and set up your project.

### 2. Configure the Region

The plugin defaults to the **US region** (`https://logfire-us.pydantic.dev/mcp`). No extra configuration is needed for US users.

**EU users** must set the `LOGFIRE_MCP_URL` environment variable to point to the EU endpoint. Add this to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
export LOGFIRE_MCP_URL="https://logfire-eu.pydantic.dev/mcp"
```

**Self-hosted** deployments can also use the `LOGFIRE_MCP_URL` variable to point to a custom instance:

```bash
export LOGFIRE_MCP_URL="https://your-logfire-instance.example.com/mcp"
```
