# Version pins

Every version-sensitive claim in this skill, in one place. When updating the skill, check these first.

| Claim | Where stated | Last verified |
|---|---|---|
| TypeScript SDK v2: `@modelcontextprotocol/server` 2.4.0, `/express` 2.0.2, `/node` 2.1.2, Zod `^4.2.0` | every TypeScript block in all three skills | 2026-10 |
| `@modelcontextprotocol/ext-apps` 2.x server helpers (peer: SDK v2) | `build-mcp-app/SKILL.md`, `build-mcp-app/references/widget-templates.md` | 2026-10 |
| `@modelcontextprotocol/ext-apps@1.2.2` CDN pin | `build-mcp-app/SKILL.md`, `build-mcp-app/references/widget-templates.md` (4×) | 2026-03 |
| Claude Code ≥2.1.76 for elicitation | `elicitation.md:15`, `build-mcp-server/SKILL.md:43,76` | 2026-03 |
| MCP spec 2025-11-25 CIMD/DCR status | `auth.md:20,24,41` | 2026-03 |
| MCPB manifest schema v0.4 | `build-mcpb/references/manifest-schema.md` | 2026-03 |
| CF `agents/mcp/server` `createMcpHandler` API | `deploy-cloudflare-workers.md` | 2026-10 |
| CF template path `cloudflare/ai/demos/remote-mcp-authless` | `deploy-cloudflare-workers.md` | 2026-10 |

## How to verify

```bash
# SDK and ext-apps latest
npm view @modelcontextprotocol/server version
npm view @modelcontextprotocol/ext-apps version

# CF template still exists
gh api repos/cloudflare/ai/contents/demos/remote-mcp-authless/src/index.ts --jq '.sha'

# MCPB schema
curl -sI https://raw.githubusercontent.com/anthropics/mcpb/main/schemas/mcpb-manifest-v0.4.schema.json | head -1
```
